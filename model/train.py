import json
import os
import pickle
import subprocess
import sys
from datetime import datetime, timezone

import numpy as np
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

#config
MODEL_VERSION = "1.3.0"
ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
MODEL_PATH = os.path.join(ARTIFACTS_DIR, "model.pkl")
METADATA_PATH = os.path.join(ARTIFACTS_DIR, "model_metadata.json")
RANDOM_STATE = 42
TEST_SIZE = 0.2


def _git_sha() -> str:
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
        )
        return sha.decode().strip()
    except Exception:
        return "unknown"


def train() -> dict:
    iris = load_iris()
    X, y = iris.data, iris.target 
    feature_names = list(iris.feature_names) 
    target_names = list(iris.target_names)  

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )

    # Training
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=5,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    # ---- Evaluation ----------------------------------------------------
    y_pred = clf.predict(X_test)
    accuracy = float(accuracy_score(y_test, y_pred))
    report = classification_report(y_test, y_pred, target_names=target_names)

    print("=" * 60)
    print("Model Training Complete")
    print("=" * 60)
    print(f"Accuracy : {accuracy:.4f}")
    print(f"Version  : {MODEL_VERSION}")
    print("-" * 60)
    print(report)

    # ---- Save artifacts --------------------------------------------
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(clf, f)
    print(f"Model saved   → {MODEL_PATH}")

    metadata = {
        "model_name": "iris-random-forest",
        "version": MODEL_VERSION,
        "git_sha": _git_sha(),
        "accuracy": round(accuracy, 4),
        "algorithm": "RandomForestClassifier",
        "n_estimators": 100,
        "max_depth": 5,
        "feature_names": feature_names,
        "target_names": target_names,
        "n_features": len(feature_names),
        "n_classes": len(target_names),
        "test_size": TEST_SIZE,
        "random_state": RANDOM_STATE,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version,
        "sklearn_version": __import__("sklearn").__version__,
    }

    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved → {METADATA_PATH}")

    return metadata


if __name__ == "__main__":
    train()
