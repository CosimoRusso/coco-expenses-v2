FROM nginx as base

RUN apt update && apt install -y wget

FROM base AS dev
COPY nginx.conf /etc/nginx/nginx.conf

FROM base AS prod
COPY app.conf /etc/nginx/conf.d/app.conf
COPY nginx-prod.conf /etc/nginx/nginx.conf
COPY frontend_prod /usr/share/nginx/html/app
