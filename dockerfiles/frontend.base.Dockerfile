FROM node:12

WORKDIR /usr/src/app
COPY src/frontend/package.json .

RUN npm install --registry=https://registry.npm.taobao.org

COPY src/frontend .
 
RUN env `cat .env | grep -v '^\s*#'` && npm run build

