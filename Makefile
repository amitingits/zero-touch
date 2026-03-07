# ===========================================================================
# Zero-Touch ML — Makefile
# ===========================================================================
# One-command targets for common development tasks.
#
# Usage:
#   make train       — train the ML model
#   make test        — run all tests
#   make lint        — check code style
#   make docker-build — build Docker image
#   make deploy      — deploy to Minikube via Helm
# ===========================================================================

# --- Configuration ---------------------------------------------------------
SHELL          := /bin/bash
PYTHON         := python
PIP            := pip
VENV_DIR       := venv
VENV_PYTHON    := $(VENV_DIR)/Scripts/python
VENV_PIP       := $(VENV_DIR)/Scripts/pip

DOCKER_USER    ?= $(shell echo $$DOCKER_USERNAME)
IMAGE_NAME     := zero-touch-ml
IMAGE_TAG      ?= latest
FULL_IMAGE     := $(DOCKER_USER)/$(IMAGE_NAME):$(IMAGE_TAG)

HELM_RELEASE   := zero-touch-ml
HELM_CHART     := helm/zero-touch-ml
K8S_NAMESPACE  := default

# --- Python / Venv ---------------------------------------------------------
.PHONY: venv
venv:  ## Create virtual environment
	$(PYTHON) -m venv $(VENV_DIR)
	$(VENV_PIP) install --upgrade pip

.PHONY: install
install:  ## Install all dependencies
	$(VENV_PIP) install -r service/requirements.txt
	$(VENV_PIP) install pytest flake8 black

# --- ML Model --------------------------------------------------------------
.PHONY: train
train:  ## Train the ML model and export artifacts
	$(VENV_PYTHON) model/train.py

# --- Testing ---------------------------------------------------------------
.PHONY: test
test:  ## Run all tests with verbose output
	$(VENV_PYTHON) -m pytest tests/ -v --tb=short

.PHONY: test-model
test-model:  ## Run model tests only
	$(VENV_PYTHON) -m pytest tests/test_model.py -v

.PHONY: test-api
test-api:  ## Run API tests only
	$(VENV_PYTHON) -m pytest tests/test_api.py -v

# --- Code Quality ----------------------------------------------------------
.PHONY: lint
lint:  ## Run linters (flake8 + black check)
	$(VENV_PYTHON) -m flake8 service/ model/ tests/ --max-line-length=120 --exclude=__pycache__
	$(VENV_PYTHON) -m black --check service/ model/ tests/ --line-length=120

.PHONY: format
format:  ## Auto-format code with black
	$(VENV_PYTHON) -m black service/ model/ tests/ --line-length=120

# --- Docker ----------------------------------------------------------------
.PHONY: docker-build
docker-build:  ## Build Docker image
	docker build -t $(FULL_IMAGE) .

.PHONY: docker-run
docker-run:  ## Run Docker container locally
	docker run --rm -p 5000:5000 --name $(IMAGE_NAME) $(FULL_IMAGE)

.PHONY: docker-push
docker-push:  ## Push Docker image to registry
	docker push $(FULL_IMAGE)

.PHONY: docker-scan
docker-scan:  ## Scan Docker image with Trivy
	trivy image --severity HIGH,CRITICAL $(FULL_IMAGE)

# --- Kubernetes / Helm -----------------------------------------------------
.PHONY: deploy
deploy:  ## Deploy to Minikube via Helm
	helm upgrade --install $(HELM_RELEASE) $(HELM_CHART) \
		--set image.repository=$(DOCKER_USER)/$(IMAGE_NAME) \
		--set image.tag=$(IMAGE_TAG) \
		--namespace $(K8S_NAMESPACE)

.PHONY: undeploy
undeploy:  ## Uninstall Helm release
	helm uninstall $(HELM_RELEASE) --namespace $(K8S_NAMESPACE)

.PHONY: helm-lint
helm-lint:  ## Lint the Helm chart
	helm lint $(HELM_CHART)

.PHONY: status
status:  ## Show deployment status
	kubectl get pods,svc -l app.kubernetes.io/name=$(IMAGE_NAME) -n $(K8S_NAMESPACE)

# --- Utilities -------------------------------------------------------------
.PHONY: clean
clean:  ## Remove generated files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf model/artifacts/*.pkl
	rm -f .coverage coverage.xml

.PHONY: help
help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
