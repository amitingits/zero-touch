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
9. [Helm Deployment (Manual)](#9-helm-deployment-manual)
10. [Jenkins CI/CD](#10-jenkins-cicd)
11. [Connect Jenkins to Minikube](#11-connect-jenkins-to-minikube)
12. [Automatic Builds via GitHub Webhook](#12-automatic-builds-via-github-webhook)
13. [Access the Live API](#13-access-the-live-api)
14. [End-to-End Pipeline Test](#14-end-to-end-pipeline-test)

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
| **ngrok** | [ngrok.com/download](https://ngrok.com/download) | `ngrok version` |

> **Windows users:** [Chocolatey](https://chocolatey.org/install) simplifies installs: `choco install minikube kubernetes-helm kubernetes-cli trivy`

---

## 2. Python Environment

```bash
git clone https://github.com/amitingits/zero-touch.git
cd zero-touch

python -m venv venv

# Windows:
venv\Scripts\activate
# Linux / macOS:
# source venv/bin/activate

pip install --upgrade pip
pip install -r service/requirements.txt
pip install pytest flake8 black
```

---

## 3. Train the Model

```bash
python model/train.py
```

**Expected:** Accuracy ~96%, generates `model/artifacts/model.pkl` and `model_metadata.json`.

---

## 4. Run Tests Locally

```bash
python -m pytest tests/ -v
```

**Expected:** 24 tests pass (9 model + 15 API).

---

## 5. Run Locally

```bash
python service/app.py
```

Test in another terminal:

```bash
curl http://localhost:5000/health
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"features": [5.1, 3.5, 1.4, 0.2]}'
```

---

## 6. Docker Setup

> **Prerequisite:** Docker Desktop must be running.

### Build

```bash
docker build -t <your-dockerhub-username>/zero-touch-ml:latest .
```

> **Important:** Don't forget the `.` at the end.

### Run

```bash
docker run --rm -p 5000:5000 <your-dockerhub-username>/zero-touch-ml:latest
```

### Push to Docker Hub

```bash
docker login -u <your-dockerhub-username>
docker push <your-dockerhub-username>/zero-touch-ml:latest
```

---

## 7. Trivy Security Scanning

```bash
trivy image --severity HIGH,CRITICAL <your-dockerhub-username>/zero-touch-ml:latest
```

---

## 8. Minikube & Kubernetes

### Start cluster

```bash
minikube start --driver=docker --cpus=2 --memory=4096
```

### Enable addons

```bash
minikube addons enable ingress
minikube addons enable metrics-server
minikube addons enable dashboard
```

### Load Docker image into Minikube

Minikube **cannot access your local Docker images** directly. You must load them:

```bash
minikube image load <your-dockerhub-username>/zero-touch-ml:latest
```

### Verify

```bash
kubectl cluster-info
kubectl get nodes
```

---

## 9. Helm Deployment (Manual)

### Lint

```bash
helm lint helm/zero-touch-ml
```

### Deploy

Since the image is loaded locally, use `imagePullPolicy=Never`:

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
kubectl get svc zero-touch-ml
```

### Uninstall

```bash
helm uninstall zero-touch-ml
```

---

## 10. Jenkins CI/CD

This project includes a **custom Jenkins Docker image** (`jenkins/Dockerfile`) that comes with Python, Docker CLI, kubectl, Helm, and Trivy pre-installed.

### Build the custom Jenkins image

```bash
docker build -t jenkins-zero-touch -f jenkins/Dockerfile .
```

> This takes a few minutes on first build.

### Start Jenkins

```bash
docker run -d \
  -p 8080:8080 \
  -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $HOME/.kube:/var/jenkins_home/.kube \
  --name jenkins \
  jenkins-zero-touch
```

> **Windows:** Replace `$HOME/.kube` with `%USERPROFILE%\.kube`

### Initial setup

1. Get admin password: `docker logs jenkins`
2. Open `http://localhost:8080`, paste the password
3. Install **suggested plugins**, create admin user

### Add Docker Hub credentials

1. `Manage Jenkins` → `Credentials` → `System` → `Global credentials`
2. Add **Secret text**: ID = `docker-hub-username`, Value = *your Docker Hub username*
3. Add **Secret text**: ID = `docker-hub-password`, Value = *your Docker Hub password/token*

### Create pipeline job

1. `New Item` → name: `zero-touch-ml` → select **Pipeline** → OK
2. Under **Pipeline**:
   - Definition: `Pipeline script from SCM`
   - SCM: `Git`
   - Repository URL: `https://github.com/<your-username>/zero-touch.git`
   - Branch: `*/main`
   - Script Path: `jenkins/Jenkinsfile`
   - **Uncheck "Lightweight checkout"** ← important!
3. Save

---

## 11. Connect Jenkins to Minikube

Jenkins runs inside a Docker container and needs special setup to reach Minikube (also a Docker container).

### Step 1 — Connect Jenkins to Minikube's Docker network

```bash
docker network connect minikube jenkins
```

### Step 2 — Copy Minikube TLS certificates into Jenkins

The kubeconfig references certificate files on your host machine. Jenkins needs its own copies:

```bash
docker cp $HOME/.minikube/profiles/minikube/client.crt jenkins:/var/jenkins_home/.kube/client.crt
docker cp $HOME/.minikube/profiles/minikube/client.key jenkins:/var/jenkins_home/.kube/client.key
docker cp $HOME/.minikube/ca.crt jenkins:/var/jenkins_home/.kube/ca.crt
```

> **Windows:** Replace `$HOME` with `%USERPROFILE%`

### Step 3 — Create a separate kubeconfig for Jenkins

This avoids conflicts with your local kubectl config:

```bash
docker exec jenkins cp /var/jenkins_home/.kube/config /var/jenkins_home/.kube/jenkins-config
```

Update it to use the Docker-internal IP and the copied certs:

```bash
docker exec jenkins kubectl config set-cluster minikube \
  --server=https://192.168.49.2:8443 \
  --certificate-authority=/var/jenkins_home/.kube/ca.crt \
  --kubeconfig=/var/jenkins_home/.kube/jenkins-config

docker exec jenkins kubectl config set-credentials minikube \
  --client-certificate=/var/jenkins_home/.kube/client.crt \
  --client-key=/var/jenkins_home/.kube/client.key \
  --kubeconfig=/var/jenkins_home/.kube/jenkins-config
```

> **Note:** `192.168.49.2` is Minikube's default Docker network IP. Verify with: `docker inspect minikube --format "{{.NetworkSettings.Networks.minikube.IPAddress}}"`

### Step 4 — Verify

```bash
docker exec jenkins kubectl get nodes --kubeconfig=/var/jenkins_home/.kube/jenkins-config
```

You should see the Minikube node. The Jenkinsfile is already configured to use `/var/jenkins_home/.kube/jenkins-config`.

---

## 12. Automatic Builds via GitHub Webhook

Make Jenkins build automatically on every `git push`.

### Start ngrok

```bash
ngrok http 8080
```

Note the public URL (e.g., `https://xxxx.ngrok-free.dev`).

### Add webhook in GitHub

1. Repo → `Settings` → `Webhooks` → `Add webhook`
2. Payload URL: `https://xxxx.ngrok-free.dev/github-webhook/`
3. Content type: `application/json`
4. Events: `Just the push event`

### Enable in Jenkins

1. Open the job → `Configure`
2. Under **Build Triggers**, check **"GitHub hook trigger for GITScm polling"**
3. Save

Now every `git push` → Jenkins builds automatically!

> **Note:** Free ngrok URLs change on restart. Update the GitHub webhook URL if you restart ngrok.

---

## 13. Access the Live API

After Jenkins deploys to Minikube, access your ML API using port-forwarding:

```bash
kubectl port-forward svc/zero-touch-ml 5000:80
```

Keep that running, then in another terminal:

```bash
# Health check
curl http://localhost:5000/health

# Predict
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"features": [5.1, 3.5, 1.4, 0.2]}'

# Model info
curl http://localhost:5000/model/info

# Metrics
curl http://localhost:5000/metrics
```

> **Why port-forward?** Minikube pods run in an isolated Docker network. `kubectl port-forward` creates a tunnel from your machine into the cluster. In production (AWS/GCP/Azure), a LoadBalancer or Ingress provides a public URL instead.

---

## 14. End-to-End Pipeline Test

1. Make a code change (e.g., update a version string)
2. Commit and push:
   ```bash
   git add .
   git commit -m "test: trigger pipeline"
   git push origin main
   ```
3. Watch Jenkins at `http://localhost:8080` — all 9 stages should pass
4. Verify pods updated:
   ```bash
   kubectl get pods -l app.kubernetes.io/name=zero-touch-ml
   ```
5. Port-forward and test the API:
   ```bash
   kubectl port-forward svc/zero-touch-ml 5000:80
   curl http://localhost:5000/health
   ```

🎉 **Congratulations!** Your Zero-Touch ML pipeline is fully operational.
