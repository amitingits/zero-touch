"""
Zero-Touch ML — Inference Service
==================================
Flask REST API that serves predictions from the trained ML model.

Endpoints
---------
POST /predict       — return prediction + confidence for input features
GET  /health        — liveness probe (always 200)
GET  /ready         — readiness probe (200 if model loaded)
GET  /model/info    — model metadata (version, accuracy, …)
GET  /metrics       — Prometheus-compatible metrics
"""

import json
import logging
import os
import pickle
import time

import numpy as np
from flask import Flask, Response, jsonify, request
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)

# ---------------------------------------------------------------------------
# Logging — structured JSON output for production log aggregation
# ---------------------------------------------------------------------------
LOG_FORMAT = json.dumps(
    {
        "time": "%(asctime)s",
        "level": "%(levelname)s",
        "logger": "%(name)s",
        "message": "%(message)s",
    }
)
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("zero-touch-ml")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "model", "artifacts", "model.pkl")
METADATA_PATH = os.path.join(BASE_DIR, "model", "artifacts", "model_metadata.json")

# ---------------------------------------------------------------------------
# Prometheus metrics
# ---------------------------------------------------------------------------
REGISTRY = CollectorRegistry()

REQUEST_COUNT = Counter(
    "inference_requests_total",
    "Total number of inference requests",
    ["endpoint", "method", "status"],
    registry=REGISTRY,
)

REQUEST_LATENCY = Histogram(
    "inference_request_duration_seconds",
    "Request latency in seconds",
    ["endpoint"],
    registry=REGISTRY,
)

PREDICTION_COUNT = Counter(
    "predictions_total",
    "Total predictions made",
    ["predicted_class"],
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app() -> Flask:
    """Flask application factory."""
    app = Flask(__name__)

    # ---- Load model & metadata on startup ----
    model = None
    metadata = {}

    try:
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
        logger.info("Model loaded from %s", MODEL_PATH)
    except FileNotFoundError:
        logger.error("Model file not found at %s", MODEL_PATH)
    except Exception as exc:
        logger.error("Failed to load model: %s", exc)

    try:
        with open(METADATA_PATH, "r") as f:
            metadata = json.load(f)
        logger.info("Metadata loaded — model v%s", metadata.get("version"))
    except FileNotFoundError:
        logger.warning("Metadata file not found at %s", METADATA_PATH)

    # ---- Middleware: request timing ----
    @app.before_request
    def _start_timer():
        request._start_time = time.time()

    @app.after_request
    def _record_metrics(response):
        latency = time.time() - getattr(request, "_start_time", time.time())
        REQUEST_LATENCY.labels(endpoint=request.path).observe(latency)
        REQUEST_COUNT.labels(
            endpoint=request.path,
            method=request.method,
            status=response.status_code,
        ).inc()
        return response

    # ---- Routes --------------------------------------------------------
    @app.route("/health", methods=["GET"])
    def health():
        """Liveness probe — always returns 200."""
        return jsonify({"status": "healthy"}), 200

    @app.route("/ready", methods=["GET"])
    def ready():
        """Readiness probe — 200 only when model is loaded."""
        if model is None:
            return jsonify({"status": "not ready", "reason": "model not loaded"}), 503
        return jsonify({"status": "ready"}), 200

    @app.route("/model/info", methods=["GET"])
    def model_info():
        """Return model metadata."""
        if not metadata:
            return jsonify({"error": "metadata not available"}), 404
        return jsonify(metadata), 200

    @app.route("/predict", methods=["POST"])
    def predict():
        """
        Accept JSON with `features` key (list of 4 floats) and return
        predicted class label + confidence score.
        """
        if model is None:
            return jsonify({"error": "model not loaded"}), 503

        body = request.get_json(silent=True)
        if body is None:
            return jsonify({"error": "request body must be valid JSON"}), 400

        features = body.get("features")
        if features is None:
            return jsonify({"error": "'features' key is required"}), 400

        # Validate feature shape
        expected = metadata.get("n_features", 4)
        if not isinstance(features, list) or len(features) != expected:
            return (
                jsonify(
                    {
                        "error": f"'features' must be a list of {expected} numeric values",
                        "expected_features": metadata.get("feature_names", []),
                    }
                ),
                400,
            )

        # Validate numeric types
        try:
            input_array = np.array(features, dtype=np.float64).reshape(1, -1)
        except (ValueError, TypeError):
            return jsonify({"error": "all feature values must be numeric"}), 400

        # Predict
        prediction = model.predict(input_array)
        probabilities = model.predict_proba(input_array)

        target_names = metadata.get("target_names", [])
        predicted_index = int(prediction[0])
        predicted_label = (
            target_names[predicted_index]
            if predicted_index < len(target_names)
            else str(predicted_index)
        )
        confidence = float(np.max(probabilities))

        PREDICTION_COUNT.labels(predicted_class=predicted_label).inc()

        return (
            jsonify(
                {
                    "prediction": predicted_label,
                    "predicted_index": predicted_index,
                    "confidence": round(confidence, 4),
                    "probabilities": {
                        name: round(float(prob), 4)
                        for name, prob in zip(target_names, probabilities[0])
                    },
                    "model_version": metadata.get("version", "unknown"),
                }
            ),
            200,
        )

    @app.route("/metrics", methods=["GET"])
    def metrics():
        """Prometheus-compatible metrics endpoint."""
        return Response(
            generate_latest(REGISTRY),
            mimetype="text/plain; version=0.0.4; charset=utf-8",
        )

    return app


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
