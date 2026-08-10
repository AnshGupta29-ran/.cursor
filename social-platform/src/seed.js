// Demo data: a handful of users, follows, posts, likes, comments, and a DM thread.
// Safe to re-run — skips anything that already exists.
import { get, run } from './db.js';
import { hashPassword } from './utils/crypto.js';

const password = hashPassword('password123');
const users = ['alice', 'bob', 'carol', 'dave', 'erin'];
for (const name of users) {
  run(
    'INSERT OR IGNORE INTO users (username, email, password_hash, display_name, bio) VALUES (?,?,?,?,?)',
    name, `${name}@example.com`, password, name[0].toUpperCase() + name.slice(1), `Hi, I'm ${name}.`
  );
}
const id = (name) => get('SELECT id FROM users WHERE username = ?', name).id;

const follows = [['alice', 'bob'], ['alice', 'carol'], ['bob', 'alice'], ['bob', 'dave'], ['carol', 'alice'], ['dave', 'alice'], ['erin', 'alice'], ['erin', 'bob']];
for (const [a, b] of follows) run('INSERT OR IGNORE INTO follows (follower_id, followee_id) VALUES (?,?)', id(a), id(b));

const posts = [
  ['alice', 'Hello world! First post on the platform.'],
  ['bob', 'Just shipped a new feature. Feeling great.'],
  ['carol', 'Sunset pics from yesterday. No filter needed.'],
  ['alice', 'Hot take: SQLite is underrated for side projects. @bob agree?'],
  ['dave', 'Anyone up for a hackathon this weekend?'],
  ['erin', 'Reading list for 2026, thread below.'],
];
for (const [name, content] of posts) {
  if (!get('SELECT id FROM posts WHERE user_id = ? AND content = ?', id(name), content)) {
    run('INSERT INTO posts (user_id, content) VALUES (?,?)', id(name), content);
  }
}

const alicePost = get('SELECT id FROM posts WHERE user_id = ? ORDER BY id LIMIT 1', id('alice')).id;
run('INSERT OR IGNORE INTO likes (user_id, post_id) VALUES (?,?)', id('bob'), alicePost);
run('INSERT OR IGNORE INTO likes (user_id, post_id) VALUES (?,?)', id('carol'), alicePost);
if (!get('SELECT id FROM comments WHERE post_id = ? LIMIT 1', alicePost)) {
  run('INSERT INTO comments (post_id, user_id, content) VALUES (?,?,?)', alicePost, id('bob'), 'Welcome aboard!');
  run('INSERT INTO comments (post_id, user_id, content) VALUES (?,?,?)', alicePost, id('carol'), 'Great to see you here.');
}

let convo = get('SELECT * FROM conversations WHERE user_a = ? AND user_b = ?', Math.min(id('alice'), id('bob')), Math.max(id('alice'), id('bob')));
if (!convo) {
  const info = run('INSERT INTO conversations (user_a, user_b) VALUES (?,?)', Math.min(id('alice'), id('bob')), Math.max(id('alice'), id('bob')));
  convo = { id: Number(info.lastInsertRowid) };
  run('INSERT INTO messages (conversation_id, sender_id, content) VALUES (?,?,?)', convo.id, id('alice'), 'Hey Bob, did you see the new feed ranking?');
  run('INSERT INTO messages (conversation_id, sender_id, content) VALUES (?,?,?)', convo.id, id('bob'), 'Just checked — the follow boost is nice.');
}

console.log('Seed complete. All demo users share password: password123');
