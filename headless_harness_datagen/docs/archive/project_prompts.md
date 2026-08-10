Here are 10 more medium-complexity project prompts. These are intentionally detailed enough to require planning, multiple components, dependency management, builds, runtime validation, and testing, making them good benchmarks for your autonomous generation → validation → repair pipeline.

⸻

1. Collaborative Whiteboard Application
Create a real-time collaborative whiteboard application using React, TypeScript, Node.js, Express, and Socket.IO. Multiple users should be able to join the same room and draw simultaneously using different colors and brush sizes. Support freehand drawing, shapes (rectangle, circle, line), eraser mode, undo/redo, canvas clearing, and exporting the drawing as an image. The UI should be responsive and handle reconnecting users gracefully.

⸻

2. Mini Cloud Storage Platform
Create a cloud storage web application using React, Node.js, Express, and MongoDB. Users should be able to register, log in, upload files, organize them into folders, rename, move, delete, search, and download files. Implement JWT-based authentication, file size validation, storage usage statistics, and a clean dashboard. The application should provide meaningful error handling and support responsive layouts.

⸻

3. Smart Home Automation Dashboard
Create a smart home dashboard using React, TypeScript, and FastAPI. The backend should simulate smart devices such as lights, fans, thermostats, doors, and cameras using REST APIs. The frontend should display device status in real time, allow users to control devices, schedule actions, create automation rules, and visualize historical sensor data. Include API documentation and unit tests for the backend.

⸻

4. AI Resume Analyzer
Create a resume analysis web application using React, FastAPI, and a pre-trained NLP model from Hugging Face Transformers. Users should be able to upload PDF or DOCX resumes, extract structured information, identify skills, estimate experience level, and compare the resume against a provided job description. Display skill gaps, matching percentage, keyword analysis, and recommendations through an intuitive dashboard.

⸻

5. Digital Library Management System
Create a complete library management system using Django. The application should support librarian and student accounts, book catalog management, borrowing and returning books, overdue tracking, reservation queues, notifications, search with multiple filters, and borrowing history. Include authentication, role-based permissions, SQLite database support, and automated unit tests covering the core workflows.

⸻

6. Secure Password Manager
Create a desktop password manager using Python and PySide6 (Qt). Users should be able to create encrypted password vaults protected by a master password. Implement AES encryption, password generation, categories, search, clipboard copying with automatic clearing, password strength indicators, and secure import/export functionality. Include proper exception handling and unit tests for the encryption logic.

⸻

7. E-commerce Inventory and Order Management Platform
Create a full-stack inventory management system using React, Node.js, Express, PostgreSQL, and Prisma. Administrators should be able to manage products, categories, suppliers, inventory levels, purchase orders, and customer orders. Include dashboards with analytics, low-stock alerts, pagination, filtering, authentication, and REST APIs with proper validation. Write automated backend tests for critical endpoints.

⸻

8. Network Monitoring Dashboard
Create a network monitoring application using Python and FastAPI. The backend should periodically ping configurable hosts, measure response times, detect outages, and expose REST APIs for historical metrics. Build a React dashboard that visualizes uptime percentages, latency graphs, downtime history, and device health using interactive charts. Support configurable monitoring intervals and persistent storage using SQLite.

⸻

9. 2D Tower Defense Game
Create a tower defense game using Unity and C#. Players should defend a base by placing different tower types with unique attack behaviors and upgrade paths. Implement enemy pathfinding, multiple enemy classes, wave progression, resource collection, tower upgrades, game saving/loading, sound effects, and a polished graphical interface. Include a configurable level system and difficulty settings.

⸻

10. Distributed Task Queue System
Create a distributed task queue framework using Go. Implement a central scheduler, multiple worker nodes, task prioritization, retries with exponential backoff, worker heartbeats, failure detection, persistent job storage using SQLite, and a REST API for submitting and monitoring jobs. Include structured logging, graceful shutdown, concurrency using goroutines, and automated integration tests demonstrating multiple workers processing jobs simultaneously.

⸻

11. Image Classification API (AI / Backend)
Create a REST API using Python and FastAPI that performs image classification using a pre-trained PyTorch model. The API should allow image uploads, return the top five predicted classes with confidence scores, provide automatic Swagger documentation, include proper input validation, and log prediction requests. Provide unit tests for the API endpoints.


12. Snake AI Simulator (AI / Game)
Create a Snake game in Python using Pygame with two modes: manual play and AI play. The AI should automatically navigate toward food using the A* pathfinding algorithm while avoiding collisions. Include adjustable game speed, score tracking, multiple difficulty levels, and visual indicators showing the AI’s planned path.

⸻


Bonus Challenge Prompts (Harder Medium)

If you want to push the validation and repair pipeline further, these tend to expose more build and runtime issues:

* Build a GitHub-like code repository platform with repository browsing, issues, pull requests, authentication, and Markdown rendering.
* Build a Slack-style team chat application with channels, private messaging, notifications, and file sharing.
* Build a Docker container management dashboard that interacts with the Docker Engine API to start, stop, inspect, and monitor containers.
* Build a machine learning experiment tracking platform similar to MLflow with experiment comparison, metric visualization, artifact storage, and REST APIs.
* Build a Kubernetes cluster visualization dashboard that displays nodes, pods, deployments, services, logs, and resource utilization using the Kubernetes API.






Think of the prompt like a product requirements document (PRD). It should describe what needs to exist, not how to build it.

A good prompt should specify:

* Project objective
* Major features
* Quality expectations
* Deliverables
* Constraints
* Acceptance criteria





# e.g:
# Project Request
Build a production-quality Personal Finance Tracker application from scratch.
The application should allow users to manage their personal finances, track spending habits, and visualize their financial health through an intuitive interface.
This should be a complete software project rather than a prototype or static UI mockup.
---
## Core Requirements
The application should support:
- User registration and authentication
- Secure login and logout
- User profile management
Each user should have completely isolated financial data.
Users should be able to:
- Add income
- Add expenses
- Edit transactions
- Delete transactions
- Categorize transactions
- Add notes
- Specify payment methods
- Record transaction dates

---

## Financial Features

Implement support for:

- Multiple income categories
- Multiple expense categories
- Monthly summaries
- Yearly summaries
- Category-wise spending analysis
- Current balance calculation
- Budget creation
- Budget utilization tracking
- Savings tracking

The application should automatically calculate totals and financial statistics whenever data changes.

---

## Dashboard

Create a dashboard showing:

- Current balance
- Total income
- Total expenses
- Savings
- Recent transactions
- Monthly spending overview
- Budget progress

Visualizations should be included where appropriate.

---

## Search and Filtering

Users should be able to:

- Search transactions
- Filter by category
- Filter by date
- Filter by amount
- Sort results
- View transaction history

---

## Reports

Support generation of:

- Monthly reports
- Annual reports
- Category reports

Allow export of financial data in common formats such as CSV.

---

## Data Persistence

Application data must persist between runs.

Do not rely on in-memory storage.

---

## Validation

Implement appropriate validation for:

- User input
- Financial values
- Authentication
- Invalid operations

Display meaningful error messages.

---

## Documentation

Include:

- README
- Installation instructions
- Project structure
- Usage guide

---

## Testing

Provide automated tests covering important functionality.

---

## Expected Deliverable

Produce a complete, runnable repository.

The repository should include all source code, configuration, documentation, and assets necessary to run the application locally.

Avoid placeholder implementations wherever reasonably possible.

The finished project should resemble something that could realistically be developed as a university capstone or an early-stage startup MVP rather than a simple tutorial application.

------















Think of the prompt like a product requirements document (PRD). It should describe what needs to exist, not how to build it.

A good prompt should specify:

* Project objective
* Major features
* Quality expectations
* Deliverables
* Constraints
* Acceptance criteria



# e.g. 1:

# Project Request

Build a production-quality Personal Finance Tracker application from scratch.

The application should allow users to manage their personal finances, track spending habits, and visualize their financial health through an intuitive interface.

This should be a complete software project rather than a prototype or static UI mockup.

---

## Core Requirements

The application should support:

- User registration and authentication
- Secure login and logout
- User profile management

Each user should have completely isolated financial data.

Users should be able to:

- Add income
- Add expenses
- Edit transactions
- Delete transactions
- Categorize transactions
- Add notes
- Specify payment methods
- Record transaction dates

---

## Financial Features

Implement support for:

- Multiple income categories
- Multiple expense categories
- Monthly summaries
- Yearly summaries
- Category-wise spending analysis
- Current balance calculation
- Budget creation
- Budget utilization tracking
- Savings tracking

The application should automatically calculate totals and financial statistics whenever data changes.

---

## Dashboard

Create a dashboard showing:

- Current balance
- Total income
- Total expenses
- Savings
- Recent transactions
- Monthly spending overview
- Budget progress

Visualizations should be included where appropriate.

---

## Search and Filtering

Users should be able to:

- Search transactions
- Filter by category
- Filter by date
- Filter by amount
- Sort results
- View transaction history

---

## Reports

Support generation of:

- Monthly reports
- Annual reports
- Category reports

Allow export of financial data in common formats such as CSV.

---

## Data Persistence

Application data must persist between runs.

Do not rely on in-memory storage.

---

## Validation

Implement appropriate validation for:

- User input
- Financial values
- Authentication
- Invalid operations

Display meaningful error messages.

---

## Documentation

Include:

- README
- Installation instructions
- Project structure
- Usage guide

---

## Testing

Provide automated tests covering important functionality.

---

## Expected Deliverable

Produce a complete, runnable repository.

The repository should include all source code, configuration, documentation, and assets necessary to run the application locally.

Avoid placeholder implementations wherever reasonably possible.

The finished project should resemble something that could realistically be developed as a university capstone or an early-stage startup MVP rather than a simple tutorial application.







----








Below are 15 Python project ideas that are substantial enough to demonstrate backend engineering skills but can still be developed and run locally with minimal setup. Most require only Python, a virtual environment, and a few packages installed via pip.

⸻

1. Personal Finance Manager

Description

Develop a desktop/web application to manage personal finances.

Features

* User accounts
* Income and expense tracking
* Categories
* Monthly budget
* Spending analytics
* CSV import/export
* Search and filtering
* Recurring transactions

Tech Stack

* Flask
* SQLite
* SQLAlchemy
* Bootstrap

Difficulty: Intermediate

⸻

2. Library Management System

Description

A complete system for managing books and library members.

Features

* Member registration
* Book catalog
* Borrow/return books
* Late fee calculation
* Reservation queue
* Admin dashboard
* Reports

Tech Stack

* Flask
* SQLite
* Jinja2

Difficulty: Intermediate

⸻

3. Hospital Appointment Management

Description

Manage doctors, patients, and appointments.

Features

* Doctor schedules
* Appointment booking
* Patient history
* Prescription records
* Search doctors
* Email reminders (optional)

Tech Stack

* Flask
* SQLite

Difficulty: Intermediate

⸻

4. Employee Leave Management System

Description

Manage leave requests inside a company.

Features

* Employee login
* Leave requests
* Approval workflow
* Holiday calendar
* Leave balance
* Admin reports

Tech Stack

* Flask
* SQLite

Difficulty: Intermediate

⸻

5. Restaurant Ordering System

Description

Restaurant menu and ordering platform.

Features

* Browse menu
* Categories
* Shopping cart
* Order tracking
* Admin menu management
* Sales reports

Tech Stack

* Flask
* SQLite

Difficulty: Intermediate

⸻

6. URL Shortener Service

Description

Build your own Bitly-like application.

Features

* Generate short URLs
* Custom aliases
* QR code generation
* Click analytics
* Expiration dates
* REST API

Tech Stack

* Flask
* SQLite

Difficulty: Intermediate

⸻

7. File Sharing Platform

Description

Upload and share files securely.

Features

* User authentication
* File upload/download
* Sharing links
* Expiration links
* File previews
* Storage quota

Tech Stack

* Flask
* SQLite

Difficulty: Intermediate

⸻

8. Notes & Knowledge Base

Description: A personal knowledge management application.
Features
* Rich text notes
* Tags
* Search
* Markdown support
* Folder organization
* Version history
Tech Stack
* Flask
* SQLite

Difficulty: Beginner–Intermediate

⸻

9. Task & Project Management Tool

Description

A lightweight Trello/Jira alternative.

Features

* Projects
* Tasks
* Kanban board
* Due dates
* Labels
* Comments
* Activity log

Tech Stack

* Flask
* SQLite
* JavaScript

Difficulty: Intermediate

⸻

10. Inventory Management System

Description

Manage products and warehouse inventory.

Features

* Product management
* Categories
* Suppliers
* Purchase history
* Stock alerts
* Reports
* Barcode generation

Tech Stack

* Flask
* SQLite

Difficulty: Intermediate

⸻

11. University Course Registration Portal

Description

Simulate a university registration system.

Features

* Student accounts
* Faculty accounts
* Course registration
* Timetable generation
* Attendance
* Grade management

Tech Stack

* Flask
* SQLite

Difficulty: Intermediate

⸻

12. Expense Splitter

Description

A Splitwise-inspired application.

Features

* Groups
* Shared expenses
* Debt calculation
* Settlement history
* Expense reports
* Multi-currency support

Tech Stack

* Flask
* SQLite

Difficulty: Intermediate

⸻

13. AI Document Assistant

Description

Upload documents and ask questions about them.

Features

* PDF upload
* Text extraction
* Semantic search
* Chat interface
* Document summaries
* Citation support

Tech Stack

* Flask
* SQLite
* FAISS
* Sentence Transformers

Difficulty: Advanced

⸻

14. Local Code Search Engine

Description

Index local code repositories and search semantically.

Features

* Repository indexing
* Symbol extraction
* Semantic search
* Code snippets
* Similar file detection
* Duplicate detection

Tech Stack

* Flask
* SQLite
* Tree-sitter
* Sentence Transformers

Difficulty: Advanced

⸻

15. Automated Resume Screening System

Description

Screen resumes against job descriptions.

Features

* Resume upload
* Skill extraction
* Candidate ranking
* Resume parser
* Keyword matching
* Dashboard

Tech Stack

* Flask
* SQLite
* spaCy
* PDF parsing libraries

Difficulty: Advanced

⸻


Level	Recommended Projects
Beginner	Notes App, Library Management, URL Shortener
Intermediate	Inventory Management, Restaurant Ordering, Employee Leave System, Task Management, Personal Finance Manager
Advanced	AI Document Assistant, Local Code Search Engine, Resume Screening System
