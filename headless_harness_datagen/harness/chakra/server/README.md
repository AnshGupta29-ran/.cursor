# Server

This directory contains the Node.js/Express backend server for the full-stack application.

## Technologies Used

- **Node.js**: Runtime environment
- **Express.js**: Web framework
- **SQLite3**: Database
- **Sequelize**: ORM for database operations
- **JWT**: Authentication
- **Bcryptjs**: Password hashing
- **Dotenv**: Environment variable management

## Project Structure

```
server/
├── config/          # Configuration files
│   └── database.js  # Database connection
├── controllers/     # Request handlers
├── middleware/      # Custom middleware
├── models/          # Database models
├── routes/          # API route definitions
├── seeders/         # Data seeding scripts
├── migrations/      # Database migration files
└── server.js        # Main server file
```

## Setup Instructions

1. Install dependencies:
```bash
npm install
```

2. Create `.env` file:
```bash
cp .env.example .env
```

3. Run database migrations:
```bash
npx sequelize db:migrate
```

4. Run the development server:
```bash
npm run dev
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

### Resources
- `GET /api/resources` - Get all resources
- `GET /api/resources/:id` - Get resource by ID
- `POST /api/resources` - Create new resource
- `PUT /api/resources/:id` - Update resource
- `DELETE /api/resources/:id` - Delete resource

## Scripts

- `npm run dev` - Start development server with nodemon
- `npm start` - Start production server
- `npm run test` - Run tests
- `npx sequelize db:migrate` - Run database migrations
- `npx sequelize db:seed:all` - Run all seeders