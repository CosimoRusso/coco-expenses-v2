docker exec ce-db pg_dump -U postgres coco_expenses > /tmp/backup_$(date +%Y-%m-%d).sql

# Must be logged in with gdrive
gdrive files upload --parent 1z44dlXLPZk8iQMYzktbJmrjuworxyATo /tmp/backup_$(date +%Y-%m-%d).sql