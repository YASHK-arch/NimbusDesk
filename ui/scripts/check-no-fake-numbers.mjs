#!/usr/bin/env node

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const SRC_DIR = path.resolve(__dirname, '../src');

const FORBIDDEN_TOKENS = [
  '157200',
  '144500',
  '172800',
  '18.8',
  '59.6',
  '20.9',
  '1.16',
  '145 + i',
  'GDP Growth',
  'getDemoResponse',
];

const FORBIDDEN_PATTERNS = [
  /status:\s*['"]Passed['"]/i,
];

let violations = [];

function scanDirectory(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      scanDirectory(fullPath);
    } else if (/\.(tsx?|jsx?|html)$/.test(entry.name)) {
      const content = fs.readFileSync(fullPath, 'utf8');
      const lines = content.split('\n');

      lines.forEach((line, lineIdx) => {
        for (const token of FORBIDDEN_TOKENS) {
          if (line.includes(token)) {
            violations.push({
              file: path.relative(path.resolve(__dirname, '..'), fullPath),
              line: lineIdx + 1,
              matched: token,
              content: line.trim(),
            });
          }
        }
        for (const pattern of FORBIDDEN_PATTERNS) {
          if (pattern.test(line)) {
            violations.push({
              file: path.relative(path.resolve(__dirname, '..'), fullPath),
              line: lineIdx + 1,
              matched: pattern.toString(),
              content: line.trim(),
            });
          }
        }
      });
    }
  }
}

console.log('Auditing frontend source code for forbidden mock tokens...');
scanDirectory(SRC_DIR);

if (violations.length > 0) {
  console.error(`\n❌ Found ${violations.length} forbidden mock tokens in frontend codebase:`);
  violations.forEach((v) => {
    console.error(`  - ${v.file}:${v.line} -> [${v.matched}] : "${v.content}"`);
  });
  console.error('\nHard Rule Violation: All numbers and validations must originate from real backend simulations or company snapshots.');
  process.exit(1);
} else {
  console.log('✓ No fake numbers or mocked validators detected in ui/src.');
  process.exit(0);
}
