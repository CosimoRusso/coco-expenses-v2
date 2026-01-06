#!/bin/bash

apt install vim -y

echo "alias t='python manage.py test --keepdb'" >> ~/.bashrc
echo "alias r='python manage.py runserver 0.0.0.0:8000'" >> ~/.bashrc
echo "alias o='cursor -r'" >> ~/.bashrc
# Run frontend in dev mode
echo "alias rf='cd frontend/coco-expenses-v2-frontend/ && npm run dev -- --host 0.0.0.0'" >> ~/.bashrc
echo "alias rb='cd backend/ && python manage.py runserver 0.0.0.0:8000'" >> ~/.bashrc

echo "READY TO CODE!"