import express from 'express';
import crypto from 'crypto';
import db from './db.js';
import { loadLexicon, tokenize, matchTerms } from './utils.js';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { promisify } from 'util';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
app.use(express.json({ limit: '4kb' }));
app.use(express.static(path.join(__dirname, '..', 'public')));

// Load lexicons & config
const sentimentLex = loadLexicon('sentiment');
const urgencyLex = loadLexicon('urgency');
const categoryLex = loadLexicon('categories');
const routingConfig = JSON.parse(fs.readFileSync(path.join(__dirname, 'config', 'routing.json'), 'utf-8'));

// Promisify db methods (sqlite3 callback style)
const dbRun = promisify(db.run.bind(db));
const dbAll = promisify(db.all.bind(db));
const dbGet = promisify(db.get.bind(db));

// Initialize DB and static queues
function initDb() {
  const sql = fs.readFileSync(path.join(__dirname, '..', 'migrations', '001_init.sql'), 'utf-8');
  db.serialize(() => {
    db.exec(sql, (err) => {
      if (err) console.error('migration error', err);
    });
    routingConfig.queuePrecedence.forEach((q, i) => {
      db.run(
        'INSERT OR IGNORE INTO queues (name, description, sla_minutes, precedence) VALUES (?,?,?,?)',
        [q, `Queue for ${q}`, 60, i]
      );
    });
  });
}
initDb();

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

  let urgency = 'p1';
  let urgencyScore = 0;
  for (const level of Object.keys(urgencyLex)) {
    const cnt = urgencyMatches.filter(m => m.category === level).length;
    if (cnt > 0) {
      urgency = level;
      urgencyScore = cnt / tokens.length;
      break;
    }
  }

  let category = 'general';
  for (const q of routingConfig.queuePrecedence) {
    if (categoryMatches.some(m => m.category === q)) { category = q; break; }
  }

  const scores = [sentimentScore, urgencyScore];
  scores.sort((a, b) => b - a);
  const confidence = scores[0] - (scores[1] || 0);

  const evidence = [];
  sentimentMatches.forEach(m => evidence.push({ type: 'sentiment', term: m.term, category: m.category }));
  urgencyMatches.forEach(m => evidence.push({ type: 'urgency', term: m.term, category: m.category }));
  categoryMatches.forEach(m => evidence.push({ type: 'category', term: m.term, category: m.category }));

  return { sentiment, sentimentScore, urgency, urgencyScore, category, confidence, evidence };
}

app.get('/health', (req, res) => res.json({ status: 'ok' }));

app.post('/tickets', async (req, res) => {
  const { channel, author_handle, subject, body } = req.body || {};
  if (!body) return res.status(422).json({ error: { code: 'EMPTY_BODY', message: 'Message body required' } });
  if (!channel || !['email', 'sms', 'kiosk'].includes(channel))
    return res.status(400).json({ error: { code: 'BAD_CHANNEL', message: 'Invalid or missing channel' } });
  if (body.length > 4000) return res.status(413).json({ error: { code: 'TOO_LARGE', message: 'Message exceeds 4000 characters' } });

  const id = crypto.randomUUID().replace(/-/g, '').slice(0, 12);
  const created = new Date().toISOString();
  await dbRun('INSERT INTO tickets (id, channel, author_handle, subject, body, status, created_at) VALUES (?,?,?,?,?,?,?)', [
    id,
    channel,
    author_handle || '',
    subject || '',
    body,
    'open',
    created,
  ]);

  const classification = classify(body);
  const status =
    classification.confidence < routingConfig.thresholds.reviewConfidence ? 'review' : 'triaged';
  await dbRun('UPDATE tickets SET status = ? WHERE id = ?', [status, id]);
  await dbRun(
    'INSERT INTO classifications (ticket_id, sentiment, sentiment_score, urgency, urgency_score, category, confidence, evidence) VALUES (?,?,?,?,?,?,?,?)',
    [
      id,
      classification.sentiment,
      classification.sentimentScore,
      classification.urgency,
      classification.urgencyScore,
      classification.category,
      classification.confidence,
      JSON.stringify(classification.evidence),
    ]
  );

  const response = {
    id,
    ticket_id: id,
    sentiment: classification.sentiment,
    sentiment_score: classification.sentimentScore,
    urgency: classification.urgency,
    urgency_score: classification.urgencyScore,
    category: classification.category,
    confidence: classification.confidence,
    evidence: classification.evidence,
    status,
    suggested_queue: status === 'review' ? classification.category : undefined,
  };
  res.status(201).json(response);
});

app.get('/queues/:name/tickets', async (req, res) => {
  const { name } = req.params;
  let rows;
  if (name === 'review') {
    rows = await dbAll(
      `SELECT t.id, t.channel, t.author_handle, t.subject, t.body, t.status, t.created_at
       FROM tickets t JOIN classifications c ON t.id = c.ticket_id
       WHERE t.status = 'review' OR c.confidence < ?`,
      [routingConfig.thresholds.reviewConfidence]
    );
  } else {
    rows = await dbAll(
      `SELECT t.id, t.channel, t.author_handle, t.subject, t.body, t.status, t.created_at
       FROM tickets t JOIN classifications c ON t.id = c.ticket_id
       WHERE c.category = ?`,
      [name]
    );
  }
  res.json(rows);
});

app.get('/stats', async (req, res) => {
  const total = await dbGet('SELECT COUNT(*) as cnt FROM tickets');
  const perQueue = await dbAll('SELECT category, COUNT(*) as cnt FROM classifications GROUP BY category');
  const urgencyHist = await dbAll('SELECT urgency, COUNT(*) as cnt FROM classifications GROUP BY urgency');
  const reviewCount = await dbGet('SELECT COUNT(*) as cnt FROM classifications WHERE confidence < ?', [routingConfig.thresholds.reviewConfidence]);
  res.json({ total: total.cnt, perQueue, urgencyHist, reviewCount: reviewCount.cnt });
});

app.get('/export', async (req, res) => {
  const tickets = await dbAll('SELECT * FROM tickets');
  const classifications = await dbAll('SELECT * FROM classifications');
  const queues = await dbAll('SELECT * FROM queues');
  const audit = await dbAll('SELECT * FROM audit_log');
  res.json({ version: 1, tickets, classifications, queues, audit });
});

app.post('/import', async (req, res) => {
  const bundle = req.body;
  if (!bundle || bundle.version !== 1) return res.status(400).json({ error: { code: 'BAD_BUNDLE', message: 'Invalid export bundle' } });
  try {
    await dbRun('BEGIN TRANSACTION');
    await dbRun('DELETE FROM tickets');
    await dbRun('DELETE FROM classifications');
    await dbRun('DELETE FROM queues');
    await dbRun('DELETE FROM audit_log');
    const ti = db.prepare('INSERT INTO tickets (id, channel, author_handle, subject, body, status, created_at) VALUES (?,?,?,?,?,?,?)');
    bundle.tickets.forEach(t => ti.run(t.id, t.channel, t.author_handle, t.subject, t.body, t.status, t.created_at));
    const ci = db.prepare('INSERT INTO classifications (ticket_id, sentiment, sentiment_score, urgency, urgency_score, category, confidence, evidence) VALUES (?,?,?,?,?,?,?,?)');
    bundle.classifications.forEach(c => ci.run(c.ticket_id, c.sentiment, c.sentiment_score, c.urgency, c.urgency_score, c.category, c.confidence, c.evidence));
    const qi = db.prepare('INSERT INTO queues (name, description, sla_minutes, precedence) VALUES (?,?,?,?)');
    bundle.queues.forEach(q => qi.run(q.name, q.description, q.sla_minutes, q.precedence));
    const ai = db.prepare('INSERT INTO audit_log (event, payload, ts) VALUES (?,?,?)');
    bundle.audit.forEach(a => ai.run(a.event, a.payload, a.ts));
    await dbRun('COMMIT');
    res.json({ status: 'imported' });
  } catch (e) {
    await dbRun('ROLLBACK');
    res.status(500).json({ error: { code: 'IMPORT_FAIL', message: e.message } });
  }
});

app.use('/preview', express.static(path.join(__dirname, '..', 'preview')));
app.get('/', (_req, res) => {
  res.sendFile(path.join(__dirname, '..', 'public', 'index.html'));
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Harborline Dispatch listening on port ${PORT}`));

export default app;
