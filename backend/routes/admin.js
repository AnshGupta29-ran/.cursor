// routes/admin.js
const express = require('express');
const { db } = require('../db');
const { verifyToken, adminOnly } = require('../middleware/auth');

const router = express.Router();

router.get('/stats', verifyToken, adminOnly, (req, res) => {
  db.get('SELECT COUNT(*) AS users FROM users', [], (e1, users) => {
    db.get('SELECT COUNT(*) AS products FROM products', [], (e2, products) => {
      db.get('SELECT COUNT(*) AS orders FROM orders', [], (e3, orders) => {
        if (e1 || e2 || e3) return res.status(500).json({ message: 'stats failed' });
        res.json({
          users: users?.users || 0,
          products: products?.products || 0,
          orders: orders?.orders || 0,
        });
      });
    });
  });
});

router.get('/orders', verifyToken, adminOnly, (req, res) => {
  db.all('SELECT * FROM orders ORDER BY id DESC', [], (err, rows) => {
    if (err) return res.status(500).json({ message: err.message });
    res.json(rows || []);
  });
});

module.exports = router;
