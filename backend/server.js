// server.js - Entry point for e-commerce backend
require('dotenv').config();
const path = require('path');
const bcrypt = require('bcrypt');
const express = require('express');
const cors = require('cors');
const { initDb, db } = require('./db');
const authRoutes = require('./routes/auth');
const productRoutes = require('./routes/products');
const cartRoutes = require('./routes/cart');
const orderRoutes = require('./routes/orders');
const adminRoutes = require('./routes/admin');

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

initDb();

function seed() {
  db.get('SELECT COUNT(*) AS c FROM products', [], async (err, row) => {
    if (err) return console.error('seed products count failed', err.message);
    if ((row?.c || 0) === 0) {
      const products = [
        ['Wireless Headphones', 'Bluetooth over-ear headphones', 79.99, '', 25],
        ['USB-C Hub', '7-in-1 multiport adapter', 39.5, '', 40],
        ['Mechanical Keyboard', 'Hot-swappable RGB keyboard', 119.0, '', 15],
        ['Desk Lamp', 'LED lamp with USB charging', 24.99, '', 50],
      ];
      const stmt = db.prepare('INSERT INTO products (name, description, price, image, stock) VALUES (?,?,?,?,?)');
      for (const p of products) stmt.run(...p);
      stmt.finalize();
      console.log('Seeded products');
    }
  });

  db.get("SELECT id FROM users WHERE username = 'admin'", [], async (err, user) => {
    if (err) return console.error('seed admin lookup failed', err.message);
    if (!user) {
      const hash = await bcrypt.hash('admin123', 10);
      db.run(
        "INSERT INTO users (username, email, password, role) VALUES ('admin', 'admin@example.com', ?, 'admin')",
        [hash],
        (e) => {
          if (e) console.error('seed admin failed', e.message);
          else console.log('Seeded admin user admin@example.com / admin123');
        }
      );
    }
  });

  db.get("SELECT id FROM users WHERE email = 'demo@example.com'", [], async (err, user) => {
    if (err || user) return;
    const hash = await bcrypt.hash('demo1234', 10);
    db.run(
      "INSERT INTO users (username, email, password, role) VALUES ('demo', 'demo@example.com', ?, 'customer')",
      [hash]
    );
  });
}

setTimeout(seed, 300);

app.get('/api/health', (_req, res) => res.json({ ok: true, service: 'ecommerce-backend' }));
app.use('/api/auth', authRoutes);
app.use('/api/products', productRoutes);
app.use('/api/cart', cartRoutes);
app.use('/api/orders', orderRoutes);
app.use('/api/admin', adminRoutes);

app.get('*', (req, res, next) => {
  if (req.path.startsWith('/api/')) return next();
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Ecommerce running at http://localhost:${PORT}`);
  console.log(`Shop UI:  http://localhost:${PORT}/`);
  console.log(`API:      http://localhost:${PORT}/api/products`);
  console.log(`Admin login: admin@example.com / admin123`);
});
