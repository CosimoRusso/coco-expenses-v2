# Dockerfile per il frontend Vue.js
FROM node:24-alpine AS base

RUN apk add --no-cache bash wget
WORKDIR /app
COPY coco-expenses-v2-frontend/package*.json ./
RUN npm install
COPY coco-expenses-v2-frontend/ .

FROM base AS dev

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

FROM base AS build_prod

RUN npm run build

FROM node:24-alpine AS prod

COPY --from=build_prod /app/dist /