"""
Zero-Touch ML — API Integration Tests
=======================================
Tests for the Flask inference API endpoints.
"""

import json
import pytest


class TestHealthEndpoint:
    """GET /health — liveness probe."""

    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_returns_healthy(self, client):
        data = resp = client.get("/health").get_json()
        assert data["status"] == "healthy"


class TestReadinessEndpoint:
    """GET /ready — readiness probe."""

    def test_ready_returns_200(self, client):
        resp = client.get("/ready")
        assert resp.status_code == 200

    def test_ready_returns_ready(self, client):
        data = client.get("/ready").get_json()
        assert data["status"] == "ready"


class TestModelInfoEndpoint:
    """GET /model/info — model metadata."""

    def test_model_info_returns_200(self, client):
        resp = client.get("/model/info")
        assert resp.status_code == 200

    def test_model_info_contains_version(self, client):
        data = client.get("/model/info").get_json()
        assert "version" in data

    def test_model_info_contains_accuracy(self, client):
        data = client.get("/model/info").get_json()
        assert "accuracy" in data
        assert 0.0 <= data["accuracy"] <= 1.0

    def test_model_info_contains_feature_names(self, client):
        data = client.get("/model/info").get_json()
        assert "feature_names" in data
        assert isinstance(data["feature_names"], list)


class TestPredictEndpoint:
    """POST /predict — model inference."""

    def test_predict_valid_input(self, client, valid_input):
        resp = client.post(
            "/predict",
            data=json.dumps(valid_input),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "prediction" in data
        assert "confidence" in data
        assert "probabilities" in data
        assert "model_version" in data

    def test_predict_returns_valid_class(self, client, valid_input):
        resp = client.post(
            "/predict",
            data=json.dumps(valid_input),
            content_type="application/json",
        )
        data = resp.get_json()
        valid_classes = ["setosa", "versicolor", "virginica"]
        assert data["prediction"] in valid_classes

    def test_predict_confidence_range(self, client, valid_input):
        resp = client.post(
            "/predict",
            data=json.dumps(valid_input),
            content_type="application/json",
        )
        data = resp.get_json()
        assert 0.0 <= data["confidence"] <= 1.0

    def test_predict_probabilities_sum_to_one(self, client, valid_input):
        resp = client.post(
            "/predict",
            data=json.dumps(valid_input),
            content_type="application/json",
        )
        data = resp.get_json()
        total = sum(data["probabilities"].values())
        assert abs(total - 1.0) < 1e-4

    def test_predict_versicolor(self, client, valid_input_versicolor):
        resp = client.post(
            "/predict",
            data=json.dumps(valid_input_versicolor),
            content_type="application/json",
        )
        data = resp.get_json()
        # Should predict versicolor or virginica for this input
        assert data["prediction"] in ["versicolor", "virginica"]

    def test_predict_missing_features_key(self, client, invalid_input_missing_key):
        resp = client.post(
            "/predict",
            data=json.dumps(invalid_input_missing_key),
            content_type="application/json",
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data

    def test_predict_wrong_feature_count(self, client, invalid_input_wrong_length):
        resp = client.post(
            "/predict",
            data=json.dumps(invalid_input_wrong_length),
            content_type="application/json",
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data

    def test_predict_non_numeric_features(self, client, invalid_input_non_numeric):
        resp = client.post(
            "/predict",
            data=json.dumps(invalid_input_non_numeric),
            content_type="application/json",
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data

    def test_predict_no_body(self, client):
        resp = client.post("/predict", content_type="application/json")
        assert resp.status_code == 400

    def test_predict_empty_json(self, client):
        resp = client.post(
            "/predict",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert resp.status_code == 400


class TestMetricsEndpoint:
    """GET /metrics — Prometheus metrics."""

    def test_metrics_returns_200(self, client):
        resp = client.get("/metrics")
        assert resp.status_code == 200

    def test_metrics_content_type(self, client):
        resp = client.get("/metrics")
        assert "text/plain" in resp.content_type

    def test_metrics_contains_request_counter(self, client):
        # Make a request first to ensure counters are populated
        client.get("/health")
        resp = client.get("/metrics")
        body = resp.data.decode()
        assert "inference_requests_total" in body
