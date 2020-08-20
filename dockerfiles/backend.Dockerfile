FROM luwu-backend-base as base

FROM python:3.8-alpine3.12 as prod

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories \
    && rm -rf /var/cache/apk/* && rm -rf /tmp/* \
    && apk --update add libffi-dev jpeg-dev libxslt-dev tzdata postgresql-dev
COPY --from=base /opt/venv /opt/venv
RUN mkdir -p /opt/logs /opt/run

ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /root/luwu

ADD ./src/backend/ .
ADD ./conf/supervisor/supervisor.api.conf  supervisor.api.conf
EXPOSE 3030

CMD supervisord -c "supervisor.api.conf"
