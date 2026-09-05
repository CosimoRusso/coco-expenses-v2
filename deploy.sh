docker compose -f docker-compose-prod.yml down &&
git pull && 
bash build_frontend.sh && 
docker compose -f docker-compose-prod.yml build &&
docker compose -f docker-compose-prod.yml up -d &&
docker compose -f docker-compose-prod.yml exec backend python manage.py migrate
