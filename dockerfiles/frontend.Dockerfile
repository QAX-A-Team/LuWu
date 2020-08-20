FROM luwu-frontend-base as base

FROM nginx:stable-alpine

COPY --from=base /usr/src/app/dist /usr/share/nginx/html/
COPY conf/frontend/nginx.conf /etc/nginx/nginx.conf

RUN mkdir -p /etc/nginx/logs

EXPOSE 80
WORKDIR /usr/src/app

CMD ["nginx", "-g", "daemon off;"]