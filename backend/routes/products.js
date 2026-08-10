// routes/products.js - Product catalog routes
const express = require('express');
const { body, validationResult } = require('express-validator');
const { db } = require('../db');
const { adminOnly, verifyToken } = require('../middleware/auth');

const router = express.Router();

// Get all products (public)
router.get('/', (req, res) => {
  db.all('SELECT * FROM products', [], (err, rows) => {
    if (err) return res.status(500).json({ message: err.message });
    res.json(rows);
  });
});

// Get single product (public)
router.get('/:id', (req, res) => {
  const id = req.params.id;
  db.get('SELECT * FROM products WHERE id = ?', [id], (err, row) => {
    if (err) return res.status(500).json({ message: err.message });
    if (!row) return res.status(404).json({ message: 'Product not found' });
    res.json(row);
  });
});

// Create product (admin only)
router.post(
  '/',
  verifyToken,
  adminOnly,
  [body('name').notEmpty(), body('price').isFloat({ gt: 0 })],
  (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) return res.status(400).json({ errors: errors.array() });
    const { name, description, price, image, stock } = req.body;
    const stmt = db.prepare(
      'INSERT INTO products (name, description, price, image, stock) VALUES (?,?,?,?,?)'
    );
    stmt.run(name, description, price, image, stock || 0, function (err) {
      if (err) return res.status(500).json({ message: err.message });
      res.status(201).json({ id: this.lastID });
    });
  }
);

// Update product (admin only)
router.put(
  '/:id',
  verifyToken,
  adminOnly,
  [body('price').optional().isFloat({ gt: 0 })],
  (req, res) => {
    const id = req.params.id;
    const { name, description, price, image, stock } = req.body;
    const fields = [];
    const values = [];
    if (name) { fields.push('name = ?'); values.push(name); }
    if (description) { fields.push('description = ?'); values.push(description); }
    if (price !== undefined) { fields.push('price = ?'); values.push(price); }
    if (image) { fields.push('image = ?'); values.push(image); }
    if (stock !== undefined) { fields.push('stock = ?'); values.push(stock); }
    if (fields.length === 0) return res.status(400).json({ message: 'No fields to update' });
    values.push(id);
    const sql = `UPDATE products SET ${fields.join(', ')} WHERE id = ?`;
    db.run(sql, values, function (err) {
      if (err) return res.status(500).json({ message: err.message });
      res.json({ changes: this.changes });
    });
  }
);

// Delete product (admin only)
router.delete('/:id', verifyToken, adminOnly, (req, res) => {
  const id = req.params.id;
  db.run('DELETE FROM products WHERE id = ?', [id], function (err) {
    if (err) return res.status(500).json({ message: err.message });
    res.json({ changes: this.changes });
  });
});

module.exports = router;
