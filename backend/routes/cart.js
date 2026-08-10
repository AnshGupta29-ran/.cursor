// routes/cart.js - Shopping cart routes
const express = require('express');
const { db } = require('../db');
const { verifyToken } = require('../middleware/auth');

const router = express.Router();

// Get cart items for logged-in user
router.get('/', verifyToken, (req, res) => {
  const userId = req.user.id;
  const sql = `SELECT ci.id, ci.quantity, p.id as product_id, p.name, p.price, p.image, p.stock
               FROM cart_items ci JOIN products p ON ci.product_id = p.id
               WHERE ci.user_id = ?`;
  db.all(sql, [userId], (err, rows) => {
    if (err) return res.status(500).json({ message: err.message });
    res.json(rows);
  });
});

// Add or update item in cart
router.post('/', verifyToken, (req, res) => {
  const userId = req.user.id;
  const { product_id, quantity } = req.body;
  if (!product_id || !quantity || quantity < 1) return res.status(400).json({ message: 'Invalid data' });
  // Check if item already exists
  db.get('SELECT * FROM cart_items WHERE user_id = ? AND product_id = ?', [userId, product_id], (err, row) => {
    if (err) return res.status(500).json({ message: err.message });
    if (row) {
      // Update quantity
      db.run('UPDATE cart_items SET quantity = ? WHERE id = ?', [quantity, row.id], function (err) {
        if (err) return res.status(500).json({ message: err.message });
        res.json({ updated: true });
      });
    } else {
      // Insert new cart item
      db.run('INSERT INTO cart_items (user_id, product_id, quantity) VALUES (?,?,?)', [userId, product_id, quantity], function (err) {
        if (err) return res.status(500).json({ message: err.message });
        res.status(201).json({ id: this.lastID });
      });
    }
  });
});

// Remove item from cart
router.delete('/:id', verifyToken, (req, res) => {
  const cartItemId = req.params.id;
  const userId = req.user.id;
  db.run('DELETE FROM cart_items WHERE id = ? AND user_id = ?', [cartItemId, userId], function (err) {
    if (err) return res.status(500).json({ message: err.message });
    res.json({ deleted: this.changes });
  });
});

module.exports = router;
