/**
 * Fail if total JS bytes under dist/assets exceed BUNDLE_BUDGET_BYTES (default 2.5 MiB).
 * Run after `npm run build`.
 */
import fs from 'fs';
import path from 'path';
import {fileURLToPath} from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const distAssets = path.join(__dirname, '../dist/assets');

const DEFAULT_BUDGET = 2.5 * 1024 * 1024;

function main() {
  const budget = Number(process.env.BUNDLE_BUDGET_BYTES) || DEFAULT_BUDGET;
  if (!fs.existsSync(distAssets)) {
    console.error('check-bundle-budget: dist/assets not found. Run npm run build first.');
    process.exit(1);
  }
  const files = fs.readdirSync(distAssets).filter((f) => f.endsWith('.js'));
  let total = 0;
  for (const f of files) {
    total += fs.statSync(path.join(distAssets, f)).size;
  }
  console.log(`check-bundle-budget: ${files.length} JS file(s), ${total} bytes (budget ${budget})`);
  if (total > budget) {
    console.error(`check-bundle-budget: FAILED — total JS ${total} exceeds budget ${budget}`);
    process.exit(1);
  }
}

main();
