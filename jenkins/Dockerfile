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

# --- Fix Docker socket permissions ----------------------------------------
# Ensure jenkins user can access Docker socket at runtime
RUN groupadd -f docker && usermod -aG docker jenkins

# Entrypoint script to fix socket permissions at startup
RUN echo '#!/bin/bash\n\
if [ -S /var/run/docker.sock ]; then\n\
    DOCKER_GID=$(stat -c "%g" /var/run/docker.sock)\n\
    if ! getent group $DOCKER_GID > /dev/null 2>&1; then\n\
        groupadd -g $DOCKER_GID dockerhost\n\
    fi\n\
    DOCKER_GROUP=$(getent group $DOCKER_GID | cut -d: -f1)\n\
    usermod -aG $DOCKER_GROUP jenkins\n\
fi\n\
exec /usr/local/bin/jenkins.sh "$@"' > /usr/local/bin/custom-entrypoint.sh && \
    chmod +x /usr/local/bin/custom-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/custom-entrypoint.sh"]
