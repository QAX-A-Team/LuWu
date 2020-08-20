FROM node:12

WORKDIR /usr/src/app
COPY src/frontend/package.json .

RUN npm install

COPY src/frontend .
COPY conf/frontend/env.docker .env

RUN npm run build

