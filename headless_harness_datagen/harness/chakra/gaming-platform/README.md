# Gaming Platform Prototype

This is a prototype implementation of a modular gaming platform with the following components:

## Architecture Overview
- **Engine Core**: Game loop with Entity Component System (ECS)
- **Game Modules**: Physics, Rendering, Input, Audio, Multiplayer
- **Services**: User management, Score tracking, Leaderboards
- **Client**: HTML/Canvas demo game
- **Multiplayer**: WebSocket-based real-time communication

## Running the Prototype

1. Install dependencies:
```bash
cd ./services
npm install
```

2. Start the backend server:
```bash
cd ./services
node server.js
```

3. Open the client in your browser:
```
http://localhost:3000
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/profile` - Get current user profile

### Users
- `GET /api/users` - Get all users
- `GET /api/users/:id` - Get user by ID
- `PUT /api/users/:id` - Update user
- `DELETE /api/users/:id` - Delete user

### Scores
- `POST /api/scores` - Record a new score
- `GET /api/scores/user/:userId` - Get scores for a user
- `GET /api/scores/game/:gameId` - Get scores for a game

### Leaderboards
- `GET /api/leaderboards/:gameId` - Get leaderboard for a game

### Multiplayer
- `GET /api/multiplayer/join` - Join a multiplayer session
- `POST /api/multiplayer/state` - Send state update

## Engine Components

### Core Engine
- Game loop with update/render cycle
- Entity Component System (ECS) architecture
- Event bus for component communication

### Game Modules
- Physics module
- Rendering module
- Input handling module
- Audio module
- Multiplayer module

## Direct URLs

| What | URL |
|------|-----|
| **Demo game (open this)** | http://localhost:3000/index.html |
| Health | http://localhost:3000/api/health |
| Games list | http://localhost:3000/api/games |
| Leaderboard | http://localhost:3000/api/leaderboards/demo-game |
| Multiplayer WS | ws://localhost:3000/api/multiplayer |

## Index / entry files

- Game UI: `client/index.html`
- Engine core: `engine/core.js`
- API + WS server: `services/server.js`

## Controls

- Move: Arrow keys or WASD
- Save score: enter username → **Save score**