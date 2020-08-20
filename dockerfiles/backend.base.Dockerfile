FROM python:3.8-alpine3.12 as builder

ARG ENV=dev
ARG PROJ=luwu

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories \
    && rm -rf /var/cache/apk/* && rm -rf /tmp/* \
    && apk update \
    && apk --update add --no-cache --virtual build-deps libffi-dev git tzdata jpeg-dev zlib-dev libjpeg libxslt libxslt-dev build-base postgresql-dev \
    && echo '[global]' > /etc/pip.conf \
    && echo 'index-url = https://mirrors.aliyun.com/pypi/simple/' >> /etc/pip.conf \
    && mkdir -p /opt/run/${PROJ}/ \
    && mkdir -p /opt/logs/${PROJ}/ \
    && ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo "Asia/Shanghai" > /etc/timezone

COPY src/backend/requirements /root/requirements/

RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r /root/requirements/${ENV}.txt
