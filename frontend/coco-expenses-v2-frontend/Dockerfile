# Dockerfile per il frontend Vue.js
FROM node:24-alpine as build

RUN apk add --no-cache bash wget

WORKDIR /app

COPY package*.json ./
RUN npm install

EXPOSE 5173

COPY . .
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

