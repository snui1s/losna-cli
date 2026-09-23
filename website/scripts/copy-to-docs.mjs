import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.resolve(__dirname, '..', 'out');
const docsDir = path.resolve(__dirname, '..', '..', 'docs');

if (!fs.existsSync(outDir)) {
  console.error(`Export directory not found: ${outDir}`);
  process.exit(1);
}

// Clean and recreate docs directory
if (fs.existsSync(docsDir)) {
  fs.rmSync(docsDir, { recursive: true, force: true });
}

fs.cpSync(outDir, docsDir, { recursive: true });
console.log('✓ Successfully exported static website to ../docs');
