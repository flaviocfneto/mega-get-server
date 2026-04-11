#!/usr/bin/env node
/**
 * Enforces HANDOFF-TYPESCRIPT-PRO: views/ and components/ must not import web/src/lib/api.ts
 * (API calls stay in App.tsx with normalizers). Also ensures .json() is only used in lib/api.ts
 * for fetch Response parsing (excluding test files).
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const srcRoot = path.join(__dirname, '..', 'src');

const importApiPattern = /from\s+['"][\w./@\-]*\/lib\/api['"]|from\s+['"]\.\.\/lib\/api['"]|from\s+['"]\.\/lib\/api['"]/;

function walk(dir) {
  const files = [];
  for (const name of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, name.name);
    if (name.isDirectory()) files.push(...walk(p));
    else files.push(p);
  }
  return files;
}

let failed = false;

// 1) No lib/api imports under views/ or components/ (non-test files only)
for (const sub of ['views', 'components']) {
  const root = path.join(srcRoot, sub);
  if (!fs.existsSync(root)) continue;
  for (const file of walk(root)) {
    if (/\.(test|spec)\.(tsx|ts)$/.test(file)) continue;
    const rel = path.relative(srcRoot, file);
    const content = fs.readFileSync(file, 'utf8');
    if (importApiPattern.test(content)) {
      console.error(`[check-api-surface] Forbidden import of lib/api in ${rel}. Use App.tsx + apiNormalize instead.`);
      failed = true;
    }
  }
}

// 2) No Response.json() outside lib/api.ts (production source only)
const jsonCall = /\.json\s*\(\s*\)/;
for (const file of walk(srcRoot)) {
  if (/\.(test|spec)\.(tsx|ts)$/.test(file)) continue;
  const rel = path.relative(path.join(__dirname, '..'), file).replace(/\\/g, '/');
  const norm = rel.replace(/\\/g, '/');
  if (norm === 'src/lib/api.ts' || norm.endsWith('/lib/api.ts')) continue;
  const content = fs.readFileSync(file, 'utf8');
  if (jsonCall.test(content)) {
    console.error(
      `[check-api-surface] Forbidden .json() in ${rel}. Parse JSON only via web/src/lib/api.ts (readJsonBody).`,
    );
    failed = true;
  }
}

if (failed) process.exit(1);
console.log('[check-api-surface] OK');
