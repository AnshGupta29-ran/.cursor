const Resource = require('../models/Resource');

// Get all resources
exports.getAllResources = async (req, res) => {
  try {
    const resources = await Resource.findAll();
    res.json({ resources });
  } catch (error) {
    console.error('Get all resources error:', error);
    res.status(500).json({ message: 'Server error fetching resources' });
  }
};

// Get resource by ID
exports.getResourceById = async (req, res) => {
  try {
    const resource = await Resource.findByPk(req.params.id);

    if (!resource) {
      return res.status(404).json({ message: 'Resource not found' });
    }

    res.json({ resource });
  } catch (error) {
    console.error('Get resource error:', error);
    res.status(500).json({ message: 'Server error fetching resource' });
  }
};

// Create new resource
exports.createResource = async (req, res) => {
  try {
    const { title, description, content } = req.body;

    const resource = await Resource.create({
      title,
      description,
      content
    });

    res.status(201).json({ message: 'Resource created successfully', resource });
  } catch (error) {
    console.error('Create resource error:', error);
    res.status(500).json({ message: 'Server error creating resource' });
  }
};

// Update resource
exports.updateResource = async (req, res) => {
  try {
    const { title, description, content } = req.body;

    const [updated] = await Resource.update(
      { title, description, content },
      { where: { id: req.params.id } }
    );

    if (!updated) {
      return res.status(404).json({ message: 'Resource not found' });
    }

    const updatedResource = await Resource.findByPk(req.params.id);

    res.json({ message: 'Resource updated successfully', resource: updatedResource });
  } catch (error) {
    console.error('Update resource error:', error);
    res.status(500).json({ message: 'Server error updating resource' });
  }
};

// Delete resource
exports.deleteResource = async (req, res) => {
  try {
    const deleted = await Resource.destroy({
      where: { id: req.params.id }
    });

    if (!deleted) {
      return res.status(404).json({ message: 'Resource not found' });
    }

    res.json({ message: 'Resource deleted successfully' });
  } catch (error) {
    console.error('Delete resource error:', error);
    res.status(500).json({ message: 'Server error deleting resource' });
  }
};