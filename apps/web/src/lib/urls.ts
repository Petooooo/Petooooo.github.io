const rawBase = import.meta.env.BASE_URL ?? "/";
const base = rawBase.endsWith("/") ? rawBase : `${rawBase}/`;

function trimLeadingSlash(path: string) {
  return path.replace(/^\/+/, "");
}

export function withBase(path: string) {
  if (/^(https?:)?\/\//.test(path) || path.startsWith("mailto:")) {
    return path;
  }

  if (path === "/" || path === "") {
    return base;
  }

  return `${base}${trimLeadingSlash(path)}`;
}
