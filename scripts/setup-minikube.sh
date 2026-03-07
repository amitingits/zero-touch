#!/usr/bin/env bash
# ===========================================================================
# Zero-Touch ML — Minikube Setup Script
# ===========================================================================
# Starts a local Kubernetes cluster with required addons.
#
# Prerequisites:
#   - Docker Desktop running
#   - minikube installed
#   - kubectl installed
# ===========================================================================

set -euo pipefail

echo "============================================"
echo " Zero-Touch ML — Minikube Setup"
echo "============================================"

# --- Start Minikube --------------------------------------------------------
echo ""
echo "🚀 Starting Minikube cluster..."
minikube start --driver=docker --cpus=2 --memory=4096

# --- Enable addons --------------------------------------------------------
echo ""
echo "🔌 Enabling addons..."
minikube addons enable ingress
minikube addons enable metrics-server
minikube addons enable dashboard

# --- Verify cluster -------------------------------------------------------
echo ""
echo "✅ Cluster info:"
kubectl cluster-info

echo ""
echo "📦 Nodes:"
kubectl get nodes

echo ""
echo "============================================"
echo " Minikube is ready!"
echo " Dashboard: minikube dashboard"
echo " IP:        $(minikube ip)"
echo "============================================"
