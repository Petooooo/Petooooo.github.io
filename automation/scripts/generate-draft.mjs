import { promises as fs } from "fs";
import { basename, join, relative } from "path";
import process from "process";

const collections = new Set(["notes", "devops", "research", "auto-archive", "projects"]);
const contentTypes = new Set([
  "troubleshooting-log",
  "terminal-log",
  "deployment-note",
  "implementation-note",
  "algorithm-study",
  "system-design",
  "infrastructure-decision",
  "debugging-note",
  "experiment-note",
  "paper-review",
  "engineering-observation"
]);
const sourceKinds = new Set(["raw-note", "terminal-log", "git-diff", "deployment-log", "study-note", "manual"]);

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exit(1);
});

async function main() {
  const args = parseArgs(process.argv.slice(2));

  if (!args.source || args.help) {
    printHelp();
    process.exit(args.help ? 0 : 1);
  }

  const root = process.cwd();
  const sourcePath = join(root, args.source);
  const raw = await fs.readFile(sourcePath, "utf8");
  const sanitized = sanitize(raw);
  const title = args.title || inferTitle(sanitized, sourcePath);
  const contentType = normalizeOption(args.type, contentTypes) || inferContentType(sanitized);
  const collection = normalizeOption(args.collection, collections) || inferCollection(contentType, sanitized);
  const sourceKind = normalizeOption(args.sourceKind, sourceKinds) || inferSourceKind(contentType);
  const tags = normalizeList(args.tags).length > 0 ? normalizeList(args.tags) : inferTags(sanitized, contentType);
  const techStack = normalizeList(args.tech);
  const today = new Date().toISOString().slice(0, 10);
  const slug = slugify(args.slug || title);
  const targetDir = join(root, "apps", "web", "src", "content", collection);
  const targetFile = join(targetDir, `${slug}.mdx`);

  const body = buildDraft({
    title,
    description: args.description || inferDescription(contentType, collection),
    date: today,
    generatedAt: today,
    tags,
    category: args.category || defaultCategory(collection, contentType),
    contentType,
    source: relative(root, sourcePath),
    sourceKind,
    techStack,
    collection,
    raw: sanitized
  });

  await fs.mkdir(targetDir, { recursive: true });
  await fs.writeFile(targetFile, body, { encoding: "utf8", flag: "wx" });

  console.log(`Created ${relative(root, targetFile)}`);
  console.log(`Collection: ${collection}`);
  console.log(`Content type: ${contentType}`);
  console.log("Status: draft, needs manual review");
}

function parseArgs(argv) {
  const parsed = {};
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--help" || arg === "-h") {
      parsed.help = true;
      continue;
    }
    if (!arg.startsWith("--")) {
      continue;
    }
    const key = arg.slice(2);
    const next = argv[index + 1];
    if (!next || next.startsWith("--")) {
      parsed[key] = true;
      continue;
    }
    parsed[key] = next;
    index += 1;
  }
  return parsed;
}

function printHelp() {
  console.log(`Usage:
node automation/scripts/generate-draft.mjs --source automation/raw/inbox/example.md [options]

Options:
  --title "Title"
  --description "Short description"
  --collection notes|devops|research|auto-archive|projects
  --type troubleshooting-log|terminal-log|deployment-note|implementation-note|algorithm-study|system-design|infrastructure-decision|debugging-note|experiment-note|paper-review|engineering-observation
  --sourceKind raw-note|terminal-log|git-diff|deployment-log|study-note|manual
  --tags "docker,github-pages,deployment"
  --tech "Astro,Docker,Caddy"
  --category "deployment"
  --slug "custom-slug"

Generated files are always draft MDX and require manual review.`);
}

function normalizeOption(value, allowed) {
  if (!value) return undefined;
  return allowed.has(value) ? value : undefined;
}

function normalizeList(value) {
  if (!value) return [];
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function inferTitle(text, sourcePath) {
  const heading = text.split("\n").find((line) => line.trim().startsWith("# "));
  if (heading) return heading.replace(/^#\s+/, "").trim();
  return titleCase(basename(sourcePath).replace(/\.[^.]+$/, "").replace(/[-_]+/g, " "));
}

function inferDescription(contentType, collection) {
  const label = contentType.replace(/-/g, " ");
  return `Draft ${label} captured for manual review in the ${collection} archive.`;
}

function inferContentType(text) {
  const lower = text.toLowerCase();
  if (containsAny(lower, ["error", "failed", "traceback", "exception", "regression"])) return "troubleshooting-log";
  if (containsAny(lower, ["npm run", "docker compose", "systemctl", "journalctl", "$ ", " exit code "])) return "terminal-log";
  if (containsAny(lower, ["deploy", "github pages", "caddy", "raspberry pi", "rp4"])) return "deployment-note";
  if (containsAny(lower, ["algorithm", "complexity", "big-o", "pseudocode"])) return "algorithm-study";
  if (containsAny(lower, ["paper", "abstract", "method", "citation"])) return "paper-review";
  if (containsAny(lower, ["architecture", "design", "tradeoff", "interface"])) return "system-design";
  if (containsAny(lower, ["experiment", "hypothesis", "measurement", "result"])) return "experiment-note";
  if (containsAny(lower, ["debug", "breakpoint", "reproduce"])) return "debugging-note";
  if (containsAny(lower, ["decision", "decided", "rollback", "risk"])) return "infrastructure-decision";
  return "implementation-note";
}

function inferCollection(contentType, text) {
  const lower = text.toLowerCase();
  if (["troubleshooting-log", "terminal-log", "deployment-note", "infrastructure-decision", "debugging-note"].includes(contentType)) {
    return "devops";
  }
  if (
    ["algorithm-study", "experiment-note", "paper-review"].includes(contentType) ||
    containsAny(lower, ["algorithm", "compiler", "distributed system", "embedded", "firmware", "ai infrastructure"])
  ) {
    return "research";
  }
  return "notes";
}

function inferSourceKind(contentType) {
  if (contentType === "terminal-log") return "terminal-log";
  if (contentType === "deployment-note") return "deployment-log";
  if (["algorithm-study", "paper-review", "experiment-note"].includes(contentType)) return "study-note";
  return "raw-note";
}

function inferTags(text, contentType) {
  const lower = text.toLowerCase();
  const tags = new Set(["review-needed", contentType]);
  const keywordTags = [
    ["astro", "astro"],
    ["github pages", "github-pages"],
    ["docker", "docker"],
    ["docker compose", "docker-compose"],
    ["caddy", "caddy"],
    ["raspberry pi", "raspberry-pi"],
    ["rp4", "raspberry-pi"],
    ["typescript", "typescript"],
    ["algorithm", "algorithms"],
    ["embedded", "embedded"],
    ["firmware", "embedded"],
    ["ai infrastructure", "ai-infrastructure"],
    ["linux", "linux"],
    ["deployment", "deployment"],
    ["debug", "debugging"]
  ];
  for (const [needle, tag] of keywordTags) {
    if (lower.includes(needle)) tags.add(tag);
  }
  return [...tags].slice(0, 8);
}

function defaultCategory(collection, contentType) {
  if (collection === "devops") return "operations";
  if (collection === "research") return "engineering-research";
  if (collection === "auto-archive") return "archive";
  return contentType;
}

function buildDraft(data) {
  const sections = extractSections(data.raw);
  const frontmatter = [
    "---",
    `title: "${yamlString(data.title)}"`,
    `description: "${yamlString(data.description)}"`,
    `date: "${data.date}"`,
    `tags: ${yamlArray(data.tags)}`,
    `category: "${yamlString(data.category)}"`,
    `contentType: "${data.contentType}"`,
    "draft: true",
    "featured: false",
    "autoGenerated: true",
    `generatedAt: "${data.generatedAt}"`,
    "reviewed: false",
    'reviewStatus: "needs-review"',
    `source: "${yamlString(data.source)}"`,
    `sourceKind: "${data.sourceKind}"`,
    'sensitivity: "sanitized"',
    `techStack: ${yamlArray(data.techStack)}`,
    ...(data.collection === "projects"
      ? ['role: "Draft review"', `period: "${data.date.slice(0, 4)}"`, 'status: "planned"']
      : []),
    "---"
  ].join("\n");

  return `${frontmatter}

## Review Checklist

- [ ] Verify the source note is real and complete.
- [ ] Remove secrets, private IPs, internal hostnames, tokens, and sensitive personal data.
- [ ] Check commands, paths, package names, versions, and dates.
- [ ] Replace uncertain claims with observations or open questions.
- [ ] Confirm the collection, category, content type, and tags.
- [ ] Publish only by setting \`draft: false\`, \`reviewed: true\`, and \`reviewStatus: "reviewed"\`.

## Context

${sections.context}

## Observations

${sections.observations}

## Commands Or Evidence

\`\`\`text
${sections.evidence}
\`\`\`

## Decisions

${sections.decisions}

## Follow-Up

${sections.followUp}
`;
}

function extractSections(text) {
  const lines = text.split(/\r?\n/).map((line) => line.trimEnd());
  const nonEmpty = lines.filter((line) => line.trim());
  const commandLines = nonEmpty.filter((line) => looksLikeCommand(line) || looksLikeLog(line));
  const proseLines = nonEmpty.filter((line) => !looksLikeCommand(line) && !looksLikeLog(line) && !line.startsWith("#"));
  const bullets = proseLines.slice(0, 10).map((line) => `- ${stripMarkdownMarker(line)}`);

  return {
    context: bullets.length > 0 ? bullets.slice(0, 3).join("\n") : "- Add context from the source note.",
    observations: bullets.length > 3 ? bullets.slice(3, 8).join("\n") : "- Add concrete observations during review.",
    evidence: commandLines.length > 0 ? commandLines.slice(0, 60).join("\n") : "Add commands, logs, links, or evidence during review.",
    decisions: "- Record decisions made and why they were chosen.",
    followUp: "- Add verification steps, risks, and open tasks."
  };
}

function sanitize(text) {
  return text
    .replace(/\b(?:\d{1,3}\.){3}\d{1,3}\b/g, "<redacted-ip>")
    .replace(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g, "<redacted-email>")
    .replace(/(token|api[_-]?key|password|secret|authorization)(\s*[:=]\s*)(\S+)/gi, "$1$2<redacted>")
    .replace(/(Bearer\s+)[A-Za-z0-9._~+/=-]+/g, "$1<redacted>");
}

function looksLikeCommand(line) {
  return /^(?:\$|>|npm |pnpm |yarn |node |git |docker |docker compose|systemctl |journalctl |ssh |curl |cat |rg |sed |astro )/.test(line.trim());
}

function looksLikeLog(line) {
  return /\b(?:ERROR|WARN|Traceback|Exception|failed|exit code|localhost:\d+)\b/i.test(line);
}

function stripMarkdownMarker(line) {
  return line.replace(/^[-*]\s+/, "").replace(/^\d+\.\s+/, "");
}

function containsAny(text, needles) {
  return needles.some((needle) => text.includes(needle));
}

function slugify(value) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80);
}

function titleCase(value) {
  return value.replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function yamlString(value) {
  return String(value).replace(/\\/g, "\\\\").replace(/"/g, '\\"');
}

function yamlArray(values) {
  if (!values || values.length === 0) return "[]";
  return `[${values.map((value) => `"${yamlString(value)}"`).join(", ")}]`;
}
