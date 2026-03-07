# ===========================================================================
# Custom Jenkins Image for Zero-Touch ML
# ===========================================================================
# Extends jenkins/jenkins:lts with:
#   - Python 3 + pip
#   - Docker CLI
#   - kubectl
#   - Helm 3
#   - Trivy
# ===========================================================================

FROM jenkins/jenkins:lts

USER root

# --- Install Python 3, pip, and build essentials ---------------------------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv \
        curl \
        wget \
        gnupg \
        lsb-release \
        ca-certificates \
        apt-transport-https && \
    rm -rf /var/lib/apt/lists/*

# --- Install Docker CLI (not daemon — we mount the host socket) -----------
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends docker-ce-cli && \
    rm -rf /var/lib/apt/lists/*

# --- Install kubectl -------------------------------------------------------
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    chmod +x kubectl && \
    mv kubectl /usr/local/bin/

# --- Install Helm 3 --------------------------------------------------------
RUN curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# --- Install Trivy ---------------------------------------------------------
RUN wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | gpg --dearmor -o /usr/share/keyrings/trivy.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/trivy.gpg] https://aquasecurity.github.io/trivy-repo/deb generic main" > /etc/apt/sources.list.d/trivy.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends trivy && \
    rm -rf /var/lib/apt/lists/*

# --- Add jenkins user to docker group (for socket access) -----------------
RUN groupadd -f docker && usermod -aG docker jenkins

USER jenkins
