# Coco Expenses V2 - Docker Setup

This project uses Docker and Docker Compose to run the Django backend and PostgreSQL database.

## Prerequisites

- Docker
- Docker Compose

## Getting Started

1. Clone the repository
2. Navigate to the project directory
3. Run the following command to start the services:

```bash
docker-compose up -d
```

This will start both the PostgreSQL database and the Django web server.

## Services

### PostgreSQL Database
- Container name: coco-expenses-db
- Port: 5432
- Environment variables: See `database/.env`

### Django Web Server
- Container name: coco-expenses-django
- Port: 8000
- Environment variables: See `backend/.env`

## Accessing the Application

- Django Admin: http://localhost:8000/admin/
- API: http://localhost:8000/api/

## Stopping the Services

To stop the services, run:

```bash
docker-compose down
```

## Development

The Django application code is mounted as a volume, so changes to the code will be reflected in the container without rebuilding.