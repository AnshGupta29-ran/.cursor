'use strict';

module.exports = {
  up: async (queryInterface, Sequelize) => {
    return queryInterface.bulkInsert('Resources', [
      {
        title: 'Getting Started with FullStack Development',
        description: 'A comprehensive guide to building full-stack applications',
        content: 'Full-stack development involves working on both the front-end and back-end of web applications. This guide will walk you through the essential technologies and best practices...',
        createdAt: new Date(),
        updatedAt: new Date()
      },
      {
        title: 'React Best Practices',
        description: 'Tips and techniques for writing better React code',
        content: 'React is a powerful JavaScript library for building user interfaces. Here are some best practices that will help you write more maintainable and efficient React applications...',
        createdAt: new Date(),
        updatedAt: new Date()
      },
      {
        title: 'Node.js and Express Fundamentals',
        description: 'Understanding the core concepts of Node.js and Express framework',
        content: 'Node.js is a JavaScript runtime built on Chrome\'s V8 JavaScript engine. Express is a minimal and flexible Node.js web application framework that provides a robust set of features...',
        createdAt: new Date(),
        updatedAt: new Date()
      }
    ], {});
  },

  down: async (queryInterface, Sequelize) => {
    return queryInterface.bulkDelete('Resources', null, {});
  }
};