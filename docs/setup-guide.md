# Zero-Touch ML — Setup Guide

Complete step-by-step guide for setting up the project from scratch.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Python Environment](#2-python-environment)
3. [Train the Model](#3-train-the-model)
4. [Run Tests](#4-run-tests)
5. [Run Locally](#5-run-locally)
6. [Docker Setup](#6-docker-setup)
7. [Trivy Security Scanning](#7-trivy-security-scanning)
8. [Minikube & Kubernetes](#8-minikube--kubernetes)
9. [Helm Deployment](#9-helm-deployment)
10. [Jenkins CI/CD](#10-jenkins-cicd)
11. [GitHub Repository Setup](#11-github-repository-setup)
12. [End-to-End Pipeline Test](#12-end-to-end-pipeline-test)

---

## 1. Prerequisites

Install each tool in order. Verify each with the given command before proceeding.

| Tool | Install | Verify |
|---|---|---|
| **Python 3.10+** | [python.org/downloads](https://www.python.org/downloads/) | `python --version` |
| **Git** | [git-scm.com/downloads](https://git-scm.com/downloads/) | `git --version` |
| **Docker Desktop** | [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/) | `docker --version` |
| **Minikube** | [minikube.sigs.k8s.io](https://minikube.sigs.k8s.io/docs/start/) | `minikube version` |
| **kubectl** | Bundled with Docker Desktop, or install separately | `kubectl version --client` |
| **Helm 3** | [helm.sh/docs/intro/install](https://helm.sh/docs/intro/install/) | `helm version` |
| **Trivy** | [GitHub releases](https://github.com/aquasecurity/trivy/releases) | `trivy --version` |

> **Windows users:** [Chocolatey](https://chocolatey.org/install) simplifies installs: `choco install minikube kubernetes-helm kubernetes-cli trivy`

---

## 2. Python Environment

```bash
# Clone the repository
git clone https://github.com/<your-username>/zero-touch.git
cd zero-touch

# Create virtual environment
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# Linux / macOS:
# source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r service/requirements.txt
pip install pytest flake8 black
```

---

## 3. Train the Model

```bash
python model/train.py
```

**Expected output:**
```
============================================================
Model Training Complete
============================================================
Accuracy : 0.9667
Version  : 1.0.0
------------------------------------------------------------
              precision    recall  f1-score   support
      setosa       1.00      1.00      1.00        10
  versicolor       0.90      1.00      0.95        10
   virginica       1.00      0.90      0.95        10
    accuracy                           0.97        30

Model saved   → model/artifacts/model.pkl
Metadata saved → model/artifacts/model_metadata.json
```

---

## 4. Run Tests

```bash
python -m pytest tests/ -v
```

**Expected:** 24 tests pass (9 model + 15 API).

---

## 5. Run Locally

```bash
python service/app.py
```

Test the API in a new terminal:

```bash
# Health check
curl http://localhost:5000/health

# Prediction
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"features": [5.1, 3.5, 1.4, 0.2]}'

# Model info
curl http://localhost:5000/model/info

# Prometheus metrics
curl http://localhost:5000/metrics
```

---

## 6. Docker Setup

> **Prerequisite:** Docker Desktop must be installed and running.

### Build the image

```bash
docker build -t <your-dockerhub-username>/zero-touch-ml:latest .
```

> **Important:** Don't forget the `.` at the end — it specifies the build context.

### Run the container

```bash
docker run --rm -p 5000:5000 <your-dockerhub-username>/zero-touch-ml:latest
```

### Test it

```bash
curl http://localhost:5000/health
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"features": [6.0, 2.7, 5.1, 1.6]}'
```

### Push to Docker Hub

```bash
docker login -u <your-dockerhub-username>
docker push <your-dockerhub-username>/zero-touch-ml:latest
```

---

## 7. Trivy Security Scanning

> **Prerequisite:** Trivy must be installed.

### Standalone scan

```bash
trivy image <your-dockerhub-username>/zero-touch-ml:latest
```

### Scan with severity filter

```bash
trivy image --severity HIGH,CRITICAL <your-dockerhub-username>/zero-touch-ml:latest
```

> Trivy also runs automatically in Jenkins pipeline Stage 6.

---

## 8. Minikube & Kubernetes

> **Prerequisite:** Docker Desktop running, Minikube + kubectl installed.

### Start the cluster

```bash
minikube start --driver=docker --cpus=2 --memory=4096
```

### Enable required addons

```bash
minikube addons enable ingress
minikube addons enable metrics-server
minikube addons enable dashboard
```

### Load Docker image into Minikube

Minikube runs its own container runtime and **cannot access your local Docker images** directly. You must load the image:

```bash
minikube image load <your-dockerhub-username>/zero-touch-ml:latest
```

### Verify cluster

```bash
kubectl cluster-info
kubectl get nodes
```

### (Optional) Open dashboard

```bash
minikube dashboard
```

---

## 9. Helm Deployment

> **Prerequisite:** Helm 3 installed, Minikube running, image loaded into Minikube.

### Lint the chart

```bash
helm lint helm/zero-touch-ml
```

### Deploy

Since the image is loaded locally into Minikube (not pulled from a remote registry), use `imagePullPolicy=Never`:

```bash
helm upgrade --install zero-touch-ml helm/zero-touch-ml \
  --set image.repository=<your-dockerhub-username>/zero-touch-ml \
  --set image.tag=latest \
  --set image.pullPolicy=Never \
  --namespace default \
  --wait --timeout 180s
```

### Verify

```bash
kubectl get pods -l app.kubernetes.io/name=zero-touch-ml
kubectl get svc -l app.kubernetes.io/name=zero-touch-ml
```

### Access the API

```bash
minikube service zero-touch-ml --url
```

Use the returned URL to call the API:

```bash
curl <MINIKUBE_URL>/health
curl -X POST <MINIKUBE_URL>/predict \
  -H "Content-Type: application/json" \
  -d '{"features": [5.1, 3.5, 1.4, 0.2]}'
```

### Uninstall

```bash
helm uninstall zero-touch-ml
```

---

## 10. Jenkins CI/CD

### Start Jenkins (via Docker)

```bash
docker run -d \
  -p 8080:8080 \
  -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  --name jenkins \
  jenkins/jenkins:lts
```

### Get admin password

```bash
docker logs jenkins
```

Look for: `Please use the following password to proceed to installation:`

### Initial Setup

1. Open `http://localhost:8080`
2. Paste the admin password
3. Install **suggested plugins**
4. Create your admin user

### Add Docker Hub Credentials

1. Go to: `Manage Jenkins` → `Credentials` → `System` → `Global credentials`
2. Add **Secret text** credential:
   - ID: `docker-hub-username`
   - Secret: *your Docker Hub username*
3. Add another **Secret text** credential:
   - ID: `docker-hub-password`
   - Secret: *your Docker Hub password or access token*

### Create Pipeline Job

1. Click `New Item`
2. Name: `zero-touch-ml` → select **Pipeline** → OK
3. Scroll to **Pipeline** section:
   - Definition: `Pipeline script from SCM`
   - SCM: `Git`
   - Repository URL: `https://github.com/<your-username>/zero-touch.git`
   - Branch: `*/main`
   - Script Path: `jenkins/Jenkinsfile`
4. Save and click **Build Now**

---

## 11. GitHub Repository Setup

### Create repository

1. Go to [github.com/new](https://github.com/new)
2. Name: `zero-touch`
3. Set to **Public** (for portfolio visibility)

### Push code

```bash
cd zero-touch
git init
git add .
git commit -m "Initial commit: Zero-Touch ML pipeline"
git branch -M main
git remote add origin https://github.com/<your-username>/zero-touch.git
git push -u origin main
```

### (Optional) Set up webhook for Jenkins

1. In GitHub repo: `Settings` → `Webhooks` → `Add webhook`
2. Payload URL: `http://<your-jenkins-url>:8080/github-webhook/`
3. Content type: `application/json`
4. Events: `Just the push event`

> For local Jenkins, you'll need **ngrok** to expose it to the internet for GitHub webhooks.

---

## 12. End-to-End Pipeline Test

Once everything is set up:

1. Make a small change (e.g., update model version in `model/train.py`)
2. Commit and push to GitHub
3. Watch Jenkins pipeline run through all 9 stages
4. Verify the new pod is running in Minikube:
   ```bash
   kubectl get pods -l app.kubernetes.io/name=zero-touch-ml
   ```
5. Test the deployed API:
   ```bash
   minikube service zero-touch-ml --url
   ```

🎉 **Congratulations!** Your Zero-Touch ML pipeline is fully operational.
