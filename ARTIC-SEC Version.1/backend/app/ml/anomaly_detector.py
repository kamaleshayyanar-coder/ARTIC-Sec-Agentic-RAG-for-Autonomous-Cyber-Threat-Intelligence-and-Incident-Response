"""Isolation Forest anomaly detector with persistence."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from app.config import get_settings

FEATURE_COLUMNS = [
    "flow_duration",
    "total_fwd_packets",
    "total_bwd_packets",
    "fwd_packet_length_mean",
    "bwd_packet_length_mean",
    "flow_bytes_s",
    "flow_packets_s",
    "fwd_iat_mean",
    "bwd_iat_mean",
    "packet_length_std",
]


class AnomalyDetector:
    def __init__(self, contamination: float = 0.05, n_estimators: int = 200, random_state: int = 42) -> None:
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            random_state=random_state,
            n_jobs=-1,
        )
        self.scaler = StandardScaler()
        self._fitted = False

    def _matrix(self, data: pd.DataFrame) -> np.ndarray:
        frame = data.copy()
        for col in FEATURE_COLUMNS:
            if col not in frame.columns:
                frame[col] = 0.0
        frame = frame[FEATURE_COLUMNS].apply(pd.to_numeric, errors="coerce").fillna(0.0)
        return frame.to_numpy(dtype=np.float32)

    def train(self, data: pd.DataFrame) -> "AnomalyDetector":
        matrix = self._matrix(data)
        scaled = self.scaler.fit_transform(matrix)
        self.model.fit(scaled)
        self._fitted = True
        return self

    def predict(self, sample: pd.DataFrame | dict[str, Any] | np.ndarray) -> float:
        if isinstance(sample, dict):
            sample = pd.DataFrame([sample])
        elif isinstance(sample, np.ndarray):
            sample = pd.DataFrame(sample, columns=FEATURE_COLUMNS[: sample.shape[-1]])
        matrix = self._matrix(sample)
        scaled = self.scaler.transform(matrix) if self._fitted else matrix
        raw = self.model.decision_function(scaled)
        # Map sklearn decision_function (higher = more normal) to anomaly score 0-1
        score = 1.0 / (1.0 + np.exp(raw))
        return float(np.clip(score[0], 0.0, 1.0))

    def detect_outliers(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        matrix = self._matrix(dataframe)
        scaled = self.scaler.transform(matrix) if self._fitted else matrix
        labels = self.model.predict(scaled)
        scores = 1.0 / (1.0 + np.exp(self.model.decision_function(scaled)))
        out = dataframe.copy()
        out["anomaly_label"] = labels
        out["anomaly_score"] = np.clip(scores, 0.0, 1.0)
        return out

    def save_model(self, path: str | Path | None = None) -> Path:
        settings = get_settings()
        directory = Path(path) if path else Path(settings.model_dir)
        directory.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": self.model, "scaler": self.scaler, "fitted": self._fitted}, directory / "isolation_forest.pkl")
        joblib.dump(self.scaler, directory / "anomaly_scaler.pkl")
        return directory / "isolation_forest.pkl"

    def load_model(self, path: str | Path | None = None) -> "AnomalyDetector":
        settings = get_settings()
        file_path = Path(path) if path else Path(settings.model_dir) / "isolation_forest.pkl"
        payload = joblib.load(file_path)
        self.model = payload["model"]
        self.scaler = payload["scaler"]
        self._fitted = payload.get("fitted", True)
        return self


def default_detector() -> AnomalyDetector:
    detector = AnomalyDetector()
    settings = get_settings()
    path = Path(settings.model_dir) / "isolation_forest.pkl"
    if path.exists():
        return detector.load_model(path)
    rng = np.random.default_rng(7)
    synthetic = pd.DataFrame(rng.normal(size=(256, len(FEATURE_COLUMNS))), columns=FEATURE_COLUMNS)
    return detector.train(synthetic)
