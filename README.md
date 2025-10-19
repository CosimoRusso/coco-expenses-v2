# Coco Expenses V2
My very personal expenses management app, tailored to my needs.

## Features
- Add both forecast and actual expenses
- See stats
- import from csv

## Development Roadmap
Next planned features, in order of development

- Automatic db backup
- Fix email confirmation flow
- Fix CSS with a strategy (tailwind?)
- Show Graphs
- export expenses in csv
- filter and search expenses
- local development without docker
- Deploy script should run on my PC and deploy through ssh on the remote machine
- Add a button to mark a forecast expense as paid

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

## Backup database

The database is backed up automatically every day at 00:00.
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