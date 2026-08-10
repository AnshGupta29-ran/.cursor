// routes/auth.js - User registration and login
const express = require('express');
const bcrypt = require('bcrypt');
const { body, validationResult } = require('express-validator');
const { db } = require('../db');
const { generateToken } = require('../middleware/auth');

const router = express.Router();

// Register
router.post(
  '/register',
  [
    body('username').isLength({ min: 3 }).trim(),
    body('email').isEmail().normalizeEmail(),
    body('password').isLength({ min: 6 })
  ],
  async (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) return res.status(400).json({ errors: errors.array() });
    const { username, email, password } = req.body;
    try {
      const hash = await bcrypt.hash(password, 10);
      const stmt = db.prepare('INSERT INTO users (username, email, password) VALUES (?,?,?)');
      stmt.run(username, email, hash, function (err) {
        if (err) return res.status(400).json({ message: 'User already exists' });
        const token = generateToken({ id: this.lastID, username, role: 'customer' });
        res.json({ token });
      });
    } catch (e) {
      res.status(500).json({ message: e.message });
    }
  }
);

// Login
router.post(
  '/login',
  [body('email').isEmail(), body('password').exists()],
  (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) return res.status(400).json({ errors: errors.array() });
    const { email, password } = req.body;
    db.get('SELECT * FROM users WHERE email = ?', [email], async (err, user) => {
      if (err || !user) return res.status(400).json({ message: 'Invalid credentials' });
      const match = await bcrypt.compare(password, user.password);
      if (!match) return res.status(400).json({ message: 'Invalid credentials' });
      const token = generateToken(user);
      res.json({ token });
    });
  }
);

module.exports = router;
