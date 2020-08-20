FROM luwu-backend-base as base

FROM python:3.8-alpine3.12 as prod

WORKDIR /root/${PROJ}

ARG TF_DIR_PATH=/terraform
ENV TF_DIR_PATH ${TF_DIR_PATH}
ARG PROJ=luwu

ENV TF_DATA_DIR ${TF_DIR_PATH}/data
ENV TF_LOG_PATH ${TF_DIR_PATH}/terraform.log
ENV TF_LOG TRACE

ADD conf/terraform ${TF_DIR_PATH}

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories && \
    apk add --no-cache unzip curl wget libffi-dev jpeg-dev libxslt-dev tzdata postgresql-dev && mkdir -p ${TF_DIR_PATH}/raw ${TF_DIR_PATH}/plugins

RUN TERRAFORM_VERSION=$(curl -w "%{redirect_url}" -o /dev/null -s https://github.com/hashicorp/terraform/releases/latest | sed 's/https:\/\/github.com\/hashicorp\/terraform\/releases\/tag\/v//') && \
    export TERRAFORM_VERSION=$TERRAFORM_VERSION && \
    wget -4 -O ${TF_DIR_PATH}/raw/terraform.zip https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip

RUN unzip -d /bin ${TF_DIR_PATH}/raw/terraform.zip
ADD ./src/backend/ ./src/backend/
ADD ./conf/supervisor/supervisor.task.conf  ./conf/supervisor/supervisor.task.conf
RUN mkdir -p /opt/run/${PROJ} /opt/logs/${PROJ}

COPY --from=base /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

CMD supervisord -c "./conf/supervisor/supervisor.task.conf"