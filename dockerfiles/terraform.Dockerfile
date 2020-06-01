ARG BASE_IMG

FROM ${BASE_IMG}

ARG TERRAFORM_VERSION
ENV TERRAFORM_VERSION ${TERRAFORM_VERSION}
ARG TF_DIR_PATH=/terraform
ENV TF_DIR_PATH ${TF_DIR_PATH}
ARG PROJ=luwu

WORKDIR /root/${PROJ}

ENV TF_DATA_DIR ${TF_DIR_PATH}/data
ENV TF_LOG_PATH ${TF_DIR_PATH}/terraform.log
ENV TF_LOG TRACE

ADD conf/terraform ${TF_DIR_PATH}

RUN apk add --no-cache unzip wget && mkdir -p ${TF_DIR_PATH}/raw ${TF_DIR_PATH}/plugins
RUN wget -4 -O ${TF_DIR_PATH}/raw/terraform.zip https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip
RUN wget -4 -O ${TF_DIR_PATH}/raw/terraform_plugin_docker.zip https://releases.hashicorp.com/terraform-provider-docker/2.7.0/terraform-provider-docker_2.7.0_linux_amd64.zip \
    && wget -4 -O ${TF_DIR_PATH}/raw/terraform_plugin_random.zip https://releases.hashicorp.com/terraform-provider-random/2.2.1/terraform-provider-random_2.2.1_linux_amd64.zip \
    && wget -4 -O ${TF_DIR_PATH}/raw/terraform_plugin_null.zip https://releases.hashicorp.com/terraform-provider-null/2.1.2/terraform-provider-null_2.1.2_linux_amd64.zip
RUN wget -4 -O ${TF_DIR_PATH}/raw/terraform_plugin_dg.zip https://releases.hashicorp.com/terraform-provider-digitalocean/1.18.0/terraform-provider-digitalocean_1.18.0_linux_amd64.zip \
    && wget -4 -O ${TF_DIR_PATH}/raw/terraform_plugin_local.zip https://releases.hashicorp.com/terraform-provider-local/1.4.0/terraform-provider-local_1.4.0_linux_amd64.zip \
    && wget -4 -O ${TF_DIR_PATH}/raw/terraform_plugin_vultr.zip https://releases.hashicorp.com/terraform-provider-vultr/1.1.5/terraform-provider-vultr_1.1.5_linux_amd64.zip
RUN unzip -d /bin ${TF_DIR_PATH}/raw/terraform.zip \
    && find ${TF_DIR_PATH}/raw -name "terraform_plugin*.zip" -print0 | xargs -0 -n1 unzip -d ${TF_DIR_PATH}/plugins

ADD ./src/backend/ ./src/backend/
ADD ./conf/supervisor/supervisor.task.conf  ./conf/supervisor/supervisor.task.conf

ENV PATH="/opt/venv/bin:$PATH"

CMD supervisord -c "./conf/supervisor/supervisor.task.conf"