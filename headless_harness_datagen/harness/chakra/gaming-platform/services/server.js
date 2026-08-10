const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json());
app.use(express.static('../client'));

// In-memory storage (in a real app, this would be a database)
let users = [
  { id: '1', username: 'player1', email: 'player1@example.com', password: 'hashed_password_1' },
  { id: '2', username: 'player2', email: 'player2@example.com', password: 'hashed_password_2' }
];

let scores = [
  { id: '1', userId: '1', gameId: 'demo-game', score: 1500, timestamp: new Date() },
  { id: '2', userId: '2', gameId: 'demo-game', score: 1200, timestamp: new Date() }
];

let leaderboard = [
  { id: '1', username: 'player1', score: 1500 },
  { id: '2', username: 'player2', score: 1200 }
];

// Routes

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

// Authentication routes
app.post('/api/auth/register', (req, res) => {
  const { username, email, password } = req.body;

  // Simple validation
  if (!username || !email || !password) {
    return res.status(400).json({ error: 'Missing required fields' });
  }

  // Check if user already exists
  const existingUser = users.find(u => u.username === username || u.email === email);
  if (existingUser) {
    return res.status(409).json({ error: 'User already exists' });
  }

  // Create new user (in a real app, hash the password)
  const newUser = {
    id: String(users.length + 1),
    username,
    email,
    password: password // In real app, hash this!
  };

  users.push(newUser);

  res.status(201).json({
    message: 'User registered successfully',
    user: { id: newUser.id, username: newUser.username, email: newUser.email }
  });
});

app.post('/api/auth/login', (req, res) => {
  const { username, password } = req.body;

  // Find user
  const user = users.find(u => u.username === username);
  if (!user) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }

  // Check password (in real app, compare hashed passwords)
  if (user.password !== password) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }

  // In a real app, generate JWT token here
  res.json({
    message: 'Login successful',
    user: { id: user.id, username: user.username, email: user.email }
  });
});

app.get('/api/auth/profile', (req, res) => {
  // In a real app, verify JWT token and get user from it
  res.json({ message: 'Profile endpoint - in a real app this would return user data' });
});

// User routes
app.get('/api/users', (req, res) => {
  res.json(users);
});

app.get('/api/users/:id', (req, res) => {
  const user = users.find(u => u.id === req.params.id);
  if (!user) {
    return res.status(404).json({ error: 'User not found' });
  }
  res.json(user);
});

app.put('/api/users/:id', (req, res) => {
  const userIndex = users.findIndex(u => u.id === req.params.id);
  if (userIndex === -1) {
    return res.status(404).json({ error: 'User not found' });
  }

  users[userIndex] = { ...users[userIndex], ...req.body };
  res.json(users[userIndex]);
});

app.delete('/api/users/:id', (req, res) => {
  const userIndex = users.findIndex(u => u.id === req.params.id);
  if (userIndex === -1) {
    return res.status(404).json({ error: 'User not found' });
  }

  users.splice(userIndex, 1);
  res.json({ message: 'User deleted successfully' });
});

// Score routes
app.post('/api/scores', (req, res) => {
  const { username, score, gameId } = req.body;

  // Validate input
  if (!username || typeof score !== 'number' || !gameId) {
    return res.status(400).json({ error: 'Missing required fields' });
  }

  // In a real app, you'd get the actual user ID from authentication
  const user = users.find(u => u.username === username);
  if (!user) {
    return res.status(404).json({ error: 'User not found' });
  }

  // Create new score entry
  const newScore = {
    id: String(scores.length + 1),
    userId: user.id,
    gameId,
    score,
    timestamp: new Date()
  };

  scores.push(newScore);

  // Update leaderboard
  updateLeaderboard();

  res.status(201).json({
    message: 'Score recorded successfully',
    score: newScore
  });
});

app.get('/api/scores/user/:userId', (req, res) => {
  const userScores = scores.filter(s => s.userId === req.params.userId);
  res.json(userScores);
});

app.get('/api/scores/game/:gameId', (req, res) => {
  const gameScores = scores.filter(s => s.gameId === req.params.gameId);
  res.json(gameScores);
});

// Leaderboard routes
app.get('/api/leaderboards/:gameId', (req, res) => {
  const gameLeaderboard = leaderboard.filter(l => l.gameId === req.params.gameId);
  res.json(gameLeaderboard);
});

// Multiplayer routes (stub)
app.get('/api/multiplayer/join', (req, res) => {
  res.json({
    message: 'Multiplayer session joined',
    sessionId: 'session-' + Math.random().toString(36).substr(2, 9)
  });
});

app.post('/api/multiplayer/state', (req, res) => {
  res.json({ message: 'State updated successfully' });
});

// Serve the index.html file for all other routes (for client-side routing)
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../client/index.html'));
});

// WebSocket server for multiplayer
const WebSocket = require('ws');
const wss = new WebSocket.Server({ port: 8080 });

wss.on('connection', (ws) => {
  console.log('New WebSocket connection established');

  ws.on('message', (message) => {
    console.log('Received:', message.toString());

    // Echo back to all clients (in a real app, you'd route messages appropriately)
    wss.clients.forEach((client) => {
      if (client !== ws && client.readyState === WebSocket.OPEN) {
        client.send(message);
      }
    });
  });

  ws.on('close', () => {
    console.log('WebSocket connection closed');
  });
});

console.log('WebSocket server listening on port 8080');

// Start server
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});

// Helper function to update leaderboard
function updateLeaderboard() {
  // Sort scores by score descending
  const sortedScores = [...scores].sort((a, b) => b.score - a.score);

  // Get top 10 players
  leaderboard = sortedScores.slice(0, 10).map((score, index) => {
    const user = users.find(u => u.id === score.userId);
    return {
      id: String(index + 1),
      username: user ? user.username : 'Unknown Player',
      score: score.score,
      gameId: score.gameId
    };
  });
}

module.exports = app;