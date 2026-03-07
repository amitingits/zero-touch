"""
Zero-Touch ML — Model Unit Tests
==================================
Tests for the trained ML model artifact.
"""

import json
import os
import numpy as np
import pytest


class TestModelArtifact:
    """Verify the serialized model file is valid and functional."""

    def test_model_file_exists(self, model):
        """Model object should load without errors (fixture handles assertion)."""
        assert model is not None

    def test_model_has_predict(self, model):
        """Model must expose a .predict() method."""
        assert hasattr(model, "predict"), "Model is missing .predict() method"

    def test_model_has_predict_proba(self, model):
        """Model must expose a .predict_proba() method for confidence scores."""
        assert hasattr(model, "predict_proba"), "Model is missing .predict_proba()"

    def test_prediction_returns_valid_class(self, model, metadata):
        """Prediction index should be within [0, n_classes)."""
        sample = np.array([[5.1, 3.5, 1.4, 0.2]])
        prediction = model.predict(sample)
        n_classes = metadata["n_classes"]
        assert 0 <= int(prediction[0]) < n_classes

    def test_prediction_shape(self, model):
        """Single sample in → single prediction out."""
        sample = np.array([[5.1, 3.5, 1.4, 0.2]])
        prediction = model.predict(sample)
        assert prediction.shape == (1,)

    def test_predict_proba_shape(self, model, metadata):
        """predict_proba should return probabilities for each class."""
        sample = np.array([[5.1, 3.5, 1.4, 0.2]])
        proba = model.predict_proba(sample)
        assert proba.shape == (1, metadata["n_classes"])

    def test_predict_proba_sums_to_one(self, model):
        """Class probabilities should sum to ~1.0."""
        sample = np.array([[5.1, 3.5, 1.4, 0.2]])
        proba = model.predict_proba(sample)
        assert abs(proba.sum() - 1.0) < 1e-6

    def test_batch_prediction(self, model):
        """Model should handle batch predictions."""
        batch = np.array([
            [5.1, 3.5, 1.4, 0.2],
            [6.0, 2.7, 5.1, 1.6],
            [6.7, 3.1, 5.6, 2.4],
        ])
        predictions = model.predict(batch)
        assert predictions.shape == (3,)


class TestModelMetadata:
    """Verify the model_metadata.json file is correct."""

    def test_metadata_file_exists(self, metadata):
        """Metadata dict should load without errors (fixture handles assertion)."""
        assert metadata is not None

    def test_required_keys_present(self, metadata):
        """Metadata must contain all required keys."""
        required = [
            "model_name",
            "version",
            "accuracy",
            "algorithm",
            "feature_names",
            "target_names",
            "n_features",
            "n_classes",
            "trained_at",
        ]
        for key in required:
            assert key in metadata, f"Missing required key: {key}"

    def test_accuracy_range(self, metadata):
        """Accuracy should be between 0 and 1."""
        assert 0.0 <= metadata["accuracy"] <= 1.0

    def test_feature_count_matches(self, metadata):
        """n_features should match length of feature_names."""
        assert metadata["n_features"] == len(metadata["feature_names"])

    def test_class_count_matches(self, metadata):
        """n_classes should match length of target_names."""
        assert metadata["n_classes"] == len(metadata["target_names"])

    def test_version_format(self, metadata):
        """Version should follow semver-like format (x.y.z)."""
        parts = metadata["version"].split(".")
        assert len(parts) == 3, f"Version '{metadata['version']}' is not semver"
        for part in parts:
            assert part.isdigit(), f"Version part '{part}' is not a digit"
