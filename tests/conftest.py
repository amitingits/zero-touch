"""
Zero-Touch ML — Pytest Fixtures
================================
Shared fixtures for model and API tests.
"""

import json
import os
import pickle
import sys

import pytest

# Ensure project root is on sys.path so imports work
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from service.app import create_app


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
MODEL_PATH = os.path.join(PROJECT_ROOT, "model", "artifacts", "model.pkl")
METADATA_PATH = os.path.join(PROJECT_ROOT, "model", "artifacts", "model_metadata.json")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def app():
    """Create a Flask application instance for testing."""
    application = create_app()
    application.config.update({"TESTING": True})
    return application


@pytest.fixture(scope="session")
def client(app):
    """Flask test client — simulates HTTP requests without running a server."""
    return app.test_client()


@pytest.fixture(scope="session")
def model():
    """Load the trained model from disk."""
    assert os.path.exists(MODEL_PATH), (
        f"Model file not found at {MODEL_PATH}. "
        "Run 'python model/train.py' first."
    )
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)


@pytest.fixture(scope="session")
def metadata():
    """Load model metadata from disk."""
    assert os.path.exists(METADATA_PATH), (
        f"Metadata file not found at {METADATA_PATH}. "
        "Run 'python model/train.py' first."
    )
    with open(METADATA_PATH, "r") as f:
        return json.load(f)


@pytest.fixture()
def valid_input():
    """A valid Iris feature vector (setosa)."""
    return {"features": [5.1, 3.5, 1.4, 0.2]}


@pytest.fixture()
def valid_input_versicolor():
    """A valid Iris feature vector (versicolor)."""
    return {"features": [6.0, 2.7, 5.1, 1.6]}


@pytest.fixture()
def invalid_input_missing_key():
    """Missing the 'features' key entirely."""
    return {"data": [5.1, 3.5, 1.4, 0.2]}


@pytest.fixture()
def invalid_input_wrong_length():
    """Wrong number of features (3 instead of 4)."""
    return {"features": [5.1, 3.5, 1.4]}


@pytest.fixture()
def invalid_input_non_numeric():
    """Non-numeric feature values."""
    return {"features": ["a", "b", "c", "d"]}
