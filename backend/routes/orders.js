// routes/orders.js
const express = require('express');
const { db } = require('../db');
const { verifyToken } = require('../middleware/auth');

const router = express.Router();

router.get('/', verifyToken, (req, res) => {
  db.all('SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC', [req.user.id], (err, rows) => {
    if (err) return res.status(500).json({ message: err.message });
    res.json(rows || []);
  });
});

router.post('/', verifyToken, (req, res) => {
  const { total = 0, items = [] } = req.body || {};
  db.run(
    'INSERT INTO orders (user_id, total, status) VALUES (?, ?, ?)',
    [req.user.id, Number(total) || 0, 'pending'],
    function (err) {
      if (err) return res.status(500).json({ message: err.message });
      const orderId = this.lastID;
      const stmt = db.prepare(
        'INSERT INTO order_items (order_id, product_id, quantity, price_at_purchase) VALUES (?, ?, ?, ?)'
      );
      for (const item of items) {
        stmt.run(orderId, item.product_id, item.quantity || 1, item.price || 0);
      }
      stmt.finalize();
      res.status(201).json({ id: orderId, status: 'pending' });
    }
  );
});

module.exports = router;
