ARG BASE_IMG

FROM ${BASE_IMG}

ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /root/luwu

ADD ./src/backend/ ./src/backend/
ADD ./conf/supervisor/supervisor.api.conf  ./conf/supervisor/supervisor.api.conf
EXPOSE 3030

CMD supervisord -c "./conf/supervisor/supervisor.api.conf"
