.ONESHELL:

all: help

################################################################################
# PROJECT CONFIG
PROJECT_NAME := mtg-mate
CONTAINER_NAME := backend
IMAGE_REGISTRY := registry.cojodi.com
IMAGE_NAME := $(PROJECT_NAME)/$(CONTAINER_NAME)
RELEASE_DATE := $(shell date -u +'%Y-%m-%dT%H:%M:%SZ')
RELEASE_DATE_TAG := $(shell date -u +'%Y-%m-%dT%H-%M-%SZ')

################################################################################
# DOCKER
docker: docker-build docker-push ## build and push the docker image, extra args with DOCKER_ARGS=... (e.g. --no-cache)

docker-push:
	docker image push $(IMAGE_REGISTRY)/$(IMAGE_NAME):latest \
		&& docker image push $(IMAGE_REGISTRY)/$(IMAGE_NAME):$(RELEASE_DATE_TAG)

docker-build: ## build the docker image, extra args with DOCKER_ARGS=... (e.g. --no-cache)
	eval $(ssh-agent) && ssh-add ~/.ssh/id_ed25519
	DOCKER_BUILDKIT=1 docker buildx build \
		$${DOCKER_ARGS} \
		--ssh default \
		--network host \
		--build-arg BUILD_DATE=$(RELEASE_DATE) \
		--build-arg VCS_REF=$(RELEASE_VERSION) \
		-t $(IMAGE_NAME):$(RELEASE_DATE_TAG) \
		-t $(IMAGE_NAME):latest \
		-t $(IMAGE_REGISTRY)/$(IMAGE_NAME):$(RELEASE_DATE_TAG) \
		-t $(IMAGE_REGISTRY)/$(IMAGE_NAME):latest \
		.

################################################################################
# RUN
run: ## run backend
	python3 -m src.run_backend

run-microphone-app: ## run the microphone app
	python3 -m src.run_microphone_app

run-dev-mock-backend: ## run dev mock appointment backend
	python3 -m uvicorn --port 8001 assets.dev_appointment_backend:app

run-docker: ## run a docker compose setup, requires a built frontend and backend
	APP_NAME=mtg-mate-dev \
	OPENAI_API_KEY=$${OPENAI_API_KEY} \
	docker compose -f assets/docker-compose.yaml up

################################################################################
# TESTS
test: test-unit test-e2e ## run all tests

test-unit: ## run unit tests
	python3 -m pytest -s tests/unit

test-e2e: ## run e2e tests
	python3 -m pytest -s tests/e2e

test-cov: ## run the tests with coverage
	python3 -m pytest -s tests \
        --cov-report term-missing:skip-covered \
        --cov-config pytest.ini \
        --cov=. tests/ \
        -vv

help: ## print this help
	@grep '##' $(MAKEFILE_LIST) \
		| grep -Ev 'grep|###' \
		| sed -e 's/^\([^:]*\):[^#]*##\([^#]*\)$$/\1:\2/' \
		| awk -F ":" '{ printf "%-34s%s\n", "\033[1;32m" $$1 ":\033[0m", $$2 }' \
		| grep -v 'sed'
