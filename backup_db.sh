docker exec ce-db pg_dump -U postgres coco_expenses > /tmp/backup_$(date +%Y-%m-%d).sql

# Must be logged in with gdrive
gdrive files upload --parent 1z44dlXLPZk8iQMYzktbJmrjuworxyATo /tmp/backup_$(date +%Y-%m-%d).sql

# Add to cron job
# 0 3 * * * /home/ubuntu/coco-expenses-v2/backup_db.sh

# To restore the database from a backup, download from gdrive and run:
# docker exec ce-db dropdb -U postgres coco_expenses
# docker exec ce-db createdb -T template0 -U postgres coco_expenses
# docker exec ce-db psql -U postgres -X coco_expenses < backup_$(date +%Y-%m-%d).sql
