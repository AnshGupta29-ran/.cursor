const express = require('express');
const router = express.Router();
const auth = require('../middleware/auth');
const resourcesController = require('../controllers/resourcesController');

// All routes require authentication
router.use(auth.authenticate);

// Routes
router.get('/', resourcesController.getAllResources);
router.get('/:id', resourcesController.getResourceById);
router.post('/', resourcesController.createResource);
router.put('/:id', resourcesController.updateResource);
router.delete('/:id', resourcesController.deleteResource);

module.exports = router;