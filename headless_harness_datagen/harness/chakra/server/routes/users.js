const express = require('express');
const router = express.Router();
const auth = require('../middleware/auth');
const usersController = require('../controllers/usersController');

// All routes require authentication
router.use(auth.authenticate);

// Routes
router.get('/', usersController.getAllUsers);
router.get('/:id', usersController.getUserById);
router.put('/:id', usersController.updateUser);
router.delete('/:id', usersController.deleteUser);

module.exports = router;