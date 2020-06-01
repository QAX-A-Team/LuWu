ARG BASE_IMG

FROM $BASE_IMG As base
FROM nginx:stable-alpine

COPY --from=base /usr/src/app/dist /usr/share/nginx/html/
COPY conf/frontend/nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
WORKDIR /usr/src/app

CMD ["nginx", "-g", "daemon off;"]