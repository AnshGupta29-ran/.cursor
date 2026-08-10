import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { loadLexicon, tokenize, matchTerms } from './utils.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const sentimentLex = loadLexicon('sentiment');
const urgencyLex = loadLexicon('urgency');
const categoryLex = loadLexicon('categories');
const routingConfig = JSON.parse(fs.readFileSync(path.join(__dirname, 'config', 'routing.json'), 'utf-8'));

function classify(body) {
  const tokens = tokenize(body);
  const sentimentMatches = matchTerms(tokens, sentimentLex);
  const urgencyMatches = matchTerms(tokens, urgencyLex);
  const categoryMatches = matchTerms(tokens, categoryLex);

  const pos = sentimentMatches.filter(m => m.category === 'positive').length;
  const neg = sentimentMatches.filter(m => m.category === 'negative').length;
  const totalSent = pos + neg || 1;
  const sentiment = pos >= neg ? 'positive' : 'negative';
  const sentimentScore = Math.max(pos, neg) / totalSent;

  const urgencyLevels = Object.keys(urgencyLex);
  let urgency = 'p1';
  let urgencyScore = 0;
  for (const level of urgencyLevels) {
    const count = urgencyMatches.filter(m => m.category === level).length;
    if (count > 0) {
      urgency = level;
      urgencyScore = count / tokens.length;
      break;
    }
  }

  let category = 'general';
  for (const q of routingConfig.queuePrecedence) {
    if (categoryMatches.some(m => m.category === q)) { category = q; break; }
  }

  const scores = [sentimentScore, urgencyScore];
  scores.sort((a,b)=>b-a);
  const confidence = scores[0] - (scores[1]||0);

  const evidence = [];
  sentimentMatches.forEach(m=>evidence.push({type:'sentiment',term:m.term,category:m.category}));
  urgencyMatches.forEach(m=>evidence.push({type:'urgency',term:m.term,category:m.category}));
  categoryMatches.forEach(m=>evidence.push({type:'category',term:m.term,category:m.category}));

  return {sentiment, sentimentScore, urgency, urgencyScore, category, confidence, evidence};
}

const fixturesDir = path.join(__dirname, '..', 'fixtures');
const outDir = path.join(__dirname, '..', 'preview');
fs.mkdirSync(outDir, {recursive:true});
let html = `<html><head><title>Harborline Dispatch Preview</title></head><body><h1>Classification Preview</h1>`;
const files = fs.readdirSync(fixturesDir).filter(f=>f.endsWith('.txt'));
for (const file of files) {
  const body = fs.readFileSync(path.join(fixturesDir, file), 'utf-8');
  const result = classify(body);
  html += `<h2>${file}</h2>`;
  html += `<pre>${body}</pre>`;
  html += `<p><strong>Sentiment:</strong> ${result.sentiment} (${result.sentimentScore.toFixed(2)})</p>`;
  html += `<p><strong>Urgency:</strong> ${result.urgency} (${result.urgencyScore.toFixed(2)})</p>`;
  html += `<p><strong>Category:</strong> ${result.category}</p>`;
  html += `<p><strong>Confidence:</strong> ${result.confidence.toFixed(2)}</p>`;
  html += `<p><strong>Evidence:</strong> ${result.evidence.map(e=>e.type+':'+e.term).join(', ')}</p>`;
}
html += `</body></html>`;
fs.writeFileSync(path.join(outDir, 'index.html'), html, 'utf-8');
console.log('Preview written to', path.join(outDir, 'index.html'));
