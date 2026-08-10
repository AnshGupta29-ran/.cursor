import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export function loadLexicon(name) {
  const filePath = path.join(__dirname, 'lexicon', `${name}.json`);
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
}

export function tokenize(text) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, ' ')
    .split(/\s+/)
    .filter(Boolean);
}

export function matchTerms(tokens, lexicon) {
  const matches = [];
  for (const [category, terms] of Object.entries(lexicon)) {
    for (const term of terms) {
      const termTokens = term.toLowerCase().split(/\s+/);
      for (let i = 0; i <= tokens.length - termTokens.length; i++) {
        if (termTokens.every((t, idx) => t === tokens[i + idx])) {
          matches.push({ category, term });
        }
      }
    }
  }
  return matches;
}
