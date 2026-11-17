import { readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { existsSync } from 'node:fs';
import { resolve } from 'node:path';

const slug = process.argv[2];
if (!slug || !/^[a-z0-9-]+$/.test(slug)) {
  throw new Error('Usage: node scripts/acknowledge-ko-editorial.mjs <project-slug>');
}
const root = resolve('src/content/projects');
const englishFile = resolve(root, slug + '.mdx');
const koreanFile = resolve('i18n/editorial/projects', slug + '.md');
const mapFile = resolve('i18n/editorial/english-source-sha256.json');
if (!existsSync(englishFile) || !existsSync(koreanFile)) {
  throw new Error('Both original English and reviewed Korean articles must exist.');
}
const english = await readFile(englishFile);
if (/^draft:\s*true$/m.test(english.toString())) {
  throw new Error('Do not acknowledge an unpublished English draft.');
}
const korean = await readFile(koreanFile, 'utf8');
if (korean.length < 900) throw new Error('Refusing a too-short Korean article.');
const hashes = JSON.parse(await readFile(mapFile, 'utf8'));
hashes[slug] = createHash('sha256').update(english).digest('hex');
await writeFile(mapFile, JSON.stringify(hashes, null, 2) + '\n');
console.log('Acknowledged reviewed Korean edition for', slug);
