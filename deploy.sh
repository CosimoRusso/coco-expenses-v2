docker compose -f docker-compose-prod.yml down &&
git pull && 
bash build_frontend.sh && 
bash restart_prod.sh