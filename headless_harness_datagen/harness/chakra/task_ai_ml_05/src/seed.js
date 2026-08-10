import fetch from 'node-fetch';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const API_URL = process.env.API_URL || 'http://127.0.0.1:5000';

async function main() {
  const fixturesDir = path.join(__dirname, '..', 'fixtures');
  const files = fs.readdirSync(fixturesDir).filter(f => f.endsWith('.txt'));
  for (const file of files) {
    const body = fs.readFileSync(path.join(fixturesDir, file), 'utf-8');
    const payload = {
      channel: 'email',
      author_handle: 'fixture_user',
      subject: file,
      body,
    };
    const res = await fetch(`${API_URL}/tickets`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    console.log(`Seeded ${file}: ${res.status}`);
    console.dir(data);
  }
}

main().catch(e => {
  console.error('Seed error:', e);
  process.exit(1);
});