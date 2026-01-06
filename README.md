# Coco Expenses V2

My very personal expenses management app, tailored to my needs.

## Features

- Add both forecast and actual expenses
- See stats
- import from csv

## Development Roadmap

Next planned features, in order of development

- fix database backup
- fix import and export from csv

## Project Setup

This project uses Docker and Docker Compose to run the Django backend and PostgreSQL database.
The default development configuration is inside a development container.

## Prerequisites

- Docker
- Docker Compose

## Getting Started

1. Clone the repository
2. Navigate to the project directory
3. Copy the `expenses/.env.sample` to `expenses/.env` and fill in the blanks
4. Copy the `database/.env.sample` to `database/.env` and fill in the blanks
5. Build all the images with `docker compose -f docker-compose.devcontainer.yml build`
6. Start all the services:

```bash
docker-compose -f docker-compose.devcontainer.yml up -d
```

This will start all the containers:

- PostgreSQL database
- Nginx reverse proxy
- devcontainer (where backend and frontend are launched from)

Once inside the devcontainer, open a terminal and start backend and frontend from terminal:

`rb` for the backend on port 8000
`rf` for the frontend on port 5172

Note that nginx runs on port 3000, that's the one to use to access the server on local machine

## Services

- Django Admin: http://localhost:3000/admin/
- API: http://localhost:3000/api/
- Frontend: http://localhost:3000/app/

## Stopping the Services

To stop the services, run:

```bash
docker-compose -f docker-compose.devcontainer.yml down
```

## Backup database

The database is backed up automatically every day at 03:00.
The backup is stored in Google Drive.
The backup is named `backup_<date>.sql`.
Currently, backups are not deleted.

To backup the database, run:

```bash
bash backup_database.sh
```

To restore the database from a backup, run:

```bash
bash restore_database.sh
```
