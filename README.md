# Coco Expenses V2
My very personal expenses management app, tailored to my needs.

## Features
- Add both forecast and actual expenses
- See stats
- import from csv

## Development Roadmap
Next planned features, in order of development

- Remove nginx login alert
- Automatic db backup
- export expenses in csv
- Show Graphs
- Session cookie should renew on every access
- filter and search expenses
- local development without docker
- Use tailwind for consistent and decent style
- Deploy script should run on my PC and deploy through ssh on the remote machine

## Project Setup

This project uses Docker and Docker Compose to run the Django backend and PostgreSQL database.

## Prerequisites

- Docker
- Docker Compose

## Getting Started

1. Clone the repository
2. Navigate to the project directory
3. Copy the `expenses/.env.sample` to `expenses/.env` and fill in the blanks
4. Copy the `database/.env.sample` to `database/.env` and fill in the blanks
5. Build all the images with `docker compose build`
5. Start all the services:

```bash
docker-compose up -d
```

This will start all the containers:
- PostgreSQL database
- Django web server
- VueJS frontend
- Nginx reverse proxy

## Services

- Django Admin: http://localhost:3000/admin/
- API: http://localhost:3000/api/
- Frontend: http://localhost:3000/app/

## Stopping the Services

To stop the services, run:

```bash
docker-compose down
```

## Development

The Django application code is mounted as a volume, so changes to the code will be reflected in the container without rebuilding.