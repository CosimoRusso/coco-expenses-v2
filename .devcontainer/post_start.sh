#!/bin/bash

apt install vim -y

echo "alias t='python manage.py test --keepdb'" >> ~/.bashrc
echo "alias r='python manage.py runserver 0.0.0.0:8000'" >> ~/.bashrc
echo "alias o='cursor -r'" >> ~/.bashrc

echo "READY TO CODE!"