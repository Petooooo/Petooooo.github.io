import { readFile, readdir, mkdir, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkGfm from 'remark-gfm';
import remarkRehype from 'remark-rehype';
import rehypeRaw from 'rehype-raw';
import rehypeStringify from 'rehype-stringify';

const web = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const root = path.join(web, 'i18n', 'editorial', 'projects');
const output = path.join(web, '.generated', 'ko-editorials');
const projectSource = path.join(web, 'src', 'content', 'projects');
const manifestFile = path.join(web, 'i18n', 'editorial', 'english-source-sha256.json');
const dist = path.join(web, 'dist', 'projects');
const processor = unified()
  .use(remarkParse)
  .use(remarkGfm)
  .use(remarkRehype, { allowDangerousHtml: true })
  .use(rehypeRaw)
  .use(rehypeStringify, { allowDangerousHtml: true });

const esc = (s) => s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const inlineCaption = (caption) => esc(caption).replace(/`([^`\n]+)`/g, '<code>$1</code>');
function figures(text) {
  return text.replace(/^\{\{figure\s+(\/figures\/[^\s|]+\.svg)\s*\|\s*(.+)\}\}[ \t]*$/gm, (_, src, caption) => (
    '<figure class="project-concept-figure">\n'
    + '  <a href="' + esc(src) + '" target="_blank" rel="noopener noreferrer" aria-label="' + esc(caption.replaceAll('`', '')) + '">\n'
    + '    <img src="' + esc(src) + '" alt="' + esc(caption.replaceAll('`', '')) + '" loading="lazy" decoding="async" />\n'
    + '  </a>\n  <figcaption>' + inlineCaption(caption) + '</figcaption>\n</figure>\n\n'
  ));
}

await mkdir(output, { recursive: true });
const reviewedSourceHashes = JSON.parse(await readFile(manifestFile, 'utf8'));
let count = 0;
for (const entry of await readdir(projectSource)) {
  if (!entry.endsWith('.mdx')) continue;
  const slug = entry.slice(0,-4);
  const original = await readFile(path.join(projectSource,entry),'utf8');
  if (/^draft:\s*true$/m.test(original)) continue;
  if (!existsSync(path.join(dist,slug,'index.html'))) continue;
  const currentSourceHash = createHash('sha256').update(original).digest('hex');
  if (reviewedSourceHashes[slug] !== currentSourceHash) {
    throw new Error('Korean article must be reviewed after English source changed: '+slug
      +'. Rewrite/check its Korean Markdown, then explicitly acknowledge the new source fingerprint.');
  }

  const sourceFile = path.join(root, slug+'.md');
  if (!existsSync(sourceFile)) {
    throw new Error('No human-authored Korean editorial for ' + slug);
  }
  const translated = await readFile(sourceFile,'utf8');
  if (translated.trim().length < 900) {
    throw new Error('Korean article ' + slug + ' is too short.');
  }
  const originalFigures = new Set([...original.matchAll(/<img[^>]+src="(\/figures\/[^"]+\.svg)"/g)].map(x=>x[1]));
  const koreanFigures = new Set([...translated.matchAll(/\{\{figure\s+(\/figures\/[^\s|]+\.svg)\s*\|/g)].map(x=>x[1]));
  const missing = [...originalFigures].filter(x=>!koreanFigures.has(x));
  if(missing.length) throw new Error(slug + ': missing diagrams: ' + missing.join(', '));
  const ast = await processor.run(processor.parse(figures(translated)));
  const markdownLeaks = [];
  function checkRenderedNode(node, insideCode = false) {
    const ignored = insideCode || (node.type === 'element' && ['pre', 'code', 'script', 'style'].includes(node.tagName));
    if (node.type === 'text' && !ignored) {
      const value = node.value ?? '';
      if (/(?:^|\n)#{1,6}[ \t]+\S/m.test(value)) markdownLeaks.push('unrendered heading: ' + value.slice(0, 110));
      if (value.includes('**')) markdownLeaks.push('unrendered emphasis: ' + value.slice(0, 110));
      if (value.includes('`')) markdownLeaks.push('unrendered inline code: ' + value.slice(0, 110));
    }
    for (const child of node.children ?? []) checkRenderedNode(child, ignored);
  }
  checkRenderedNode(ast);
  if (markdownLeaks.length) throw new Error(slug + ': Korean Markdown rendering failed:\n' + markdownLeaks.slice(0, 8).join('\n'));
  const html = String(processor.stringify(ast));
  if (!html.includes('<h2>') || !html.includes('<p>')) {
    throw new Error(slug + ': expected narrative paragraphs and sections');
  }
  await writeFile(path.join(output,slug+'.html'),html,'utf8');
  count++;
}
console.log('Compiled '+count+' human-edited Korean project articles with preserved diagrams.');
