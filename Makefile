DIR := ${CURDIR}
SRC_PATH ?= ${DIR}/src
ENV ?= dev
PROJECT_NAME ?= luwu
PROJECT_VERSION = $(shell git describe --abbrev=0 || echo 'v0.0.1')


DOCKER_FILE_PATH ?= ./dockerfiles
DOCKER_BASE_IMAGE_NAME = '${PROJECT_NAME}-base-${PROJECT_PART}-${ENV}'
DOCKER_IMAGE_NAME = '${PROJECT_NAME}-${PROJECT_PART}-${ENV}'
DOCKER_CONNTAINER_NAME = '${PROJECT_NAME}-${PROJECT_PART}-${ENV}'


### help:                                         Show Makefile rules.
.PHONY: help
help:
	@echo Makefile rules:
	@echo
	@grep -E '^### [-A-Za-z0-9_]+:' Makefile | sed 's/###/   /'


### terraform-build:                              Build terraform image.
.PHONY: terraform-build
terraform-build: PROJECT_PART=terraform
terraform-build: BASE_IMG=${PROJECT_NAME}-base-backend-${ENV}:${PROJECT_VERSION}
terraform-build: TERRAFORM_VERSION=${shell curl -w "%{redirect_url}" -o /dev/null -s "https://github.com/hashicorp/terraform/releases/latest"| sed 's/https:\/\/github.com\/hashicorp\/terraform\/releases\/tag\/v//'}
terraform-build:
	docker build --build-arg BASE_IMG=${BASE_IMG} --build-arg TERRAFORM_VERSION=${TERRAFORM_VERSION} -t ${DOCKER_IMAGE_NAME}:${PROJECT_VERSION} . -f ${DOCKER_FILE_PATH}/${PROJECT_PART}.Dockerfile


### terraform-run:                                Run terraform container.
.PHONY: terraform-run
terraform-run: PROJECT_PART=terraform
terraform-run:
	docker run --name ${DOCKER_CONNTAINER_NAME} --restart always -v ${DIR}/data/task-data:/opt/logs/luwu  -v ${DIR}/data/${PROJECT_PART}-data:/terraform -d ${DOCKER_IMAGE_NAME}:${PROJECT_VERSION}


### base-backend-build:                           Build base backend docker image.
.PHONY: base-backend-build
base-backend-build: PROJECT_PART=backend
base-backend-build:
	docker build --build-arg VERSION=${PROJECT_VERSION} -t ${DOCKER_BASE_IMAGE_NAME}:${PROJECT_VERSION} . -f ${DOCKER_FILE_PATH}/${PROJECT_PART}.base.Dockerfile


### base-frontend-build:                          Build base frontend docker image.
.PHONY: base-frontend-build
base-frontend-build: PROJECT_PART=frontend
base-frontend-build:
	docker build --build-arg VERSION=${PROJECT_VERSION} -t ${DOCKER_BASE_IMAGE_NAME}:${PROJECT_VERSION} . -f ${DOCKER_FILE_PATH}/${PROJECT_PART}.base.Dockerfile


### docker-backend-build:                         Build backend docker image
.PHONY: docker-backend-build
docker-backend-build: PROJECT_PART=backend
docker-backend-build: BASE_IMG=${PROJECT_NAME}-base-${PROJECT_PART}-${ENV}:${PROJECT_VERSION}
docker-backend-build:
	docker build --build-arg BASE_IMG=${BASE_IMG} -t ${DOCKER_IMAGE_NAME}:${PROJECT_VERSION} . -f ${DOCKER_FILE_PATH}/${PROJECT_PART}.Dockerfile


### docker-backend-run:                           Run backend docker image
.PHONY: docker-backend-run
docker-backend-run: PROJECT_PART=backend
docker-backend-run:
	docker run --name ${DOCKER_CONNTAINER_NAME} --restart always -p 3030:3030 -v ${DIR}/data/${PROJECT_PART}-data:/opt/logs -d ${DOCKER_IMAGE_NAME}:${PROJECT_VERSION}


### docker-frontend-build:                        Build frontend docker image
.PHONY: docker-frontend-build
docker-frontend-build: PROJECT_PART=frontend
docker-frontend-build: BASE_IMG=${PROJECT_NAME}-base-${PROJECT_PART}-${ENV}:${PROJECT_VERSION}
docker-frontend-build:
	docker build --build-arg BASE_IMG=${BASE_IMG} --build-arg VERSION=${PROJECT_VERSION} -t ${DOCKER_IMAGE_NAME}:${PROJECT_VERSION} . -f ${DOCKER_FILE_PATH}/${PROJECT_PART}.Dockerfile


### docker-frontend-run:                          Run frontend docker image
.PHONY: docker-frontend-run
docker-frontend-run: PROJECT_PART=frontend
docker-frontend-run:
	docker run --name ${DOCKER_CONNTAINER_NAME} --restart always -p 80:80 -v ${DIR}/data/${PROJECT_PART}-data:/etc/nginx/logs -d ${DOCKER_IMAGE_NAME}:${PROJECT_VERSION}
