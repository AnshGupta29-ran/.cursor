const { Sequelize } = require('sequelize');
require('dotenv').config();

// Create Sequelize instance with SQLite
const sequelize = new Sequelize({
  dialect: 'sqlite',
  storage: process.env.DB_NAME || './fullstack.db',
  logging: false // Set to true for SQL query logging
});

module.exports = sequelize;