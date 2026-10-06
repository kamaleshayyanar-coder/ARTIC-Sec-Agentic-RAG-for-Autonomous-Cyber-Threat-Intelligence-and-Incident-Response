"""XGBoost CIC-IDS style threat classifier with ONNX export."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from xgboost import XGBClassifier

from app.config import get_settings
from app.ml.anomaly_detector import FEATURE_COLUMNS

ATTACK_LABELS = [
    "BENIGN",
    "PortScan",
    "DDoS",
    "DoS",
    "SQLi",
    "XSS",
    "BruteForce",
    "Bot",
    "Infiltration",
    "Heartbleed",
    "FTP-Patator",
    "SSH-Patator",
]


class ThreatClassifier:
    def __init__(self) -> None:
        self.model = XGBClassifier(
            n_estimators=300,
            max_depth=8,
            learning_rate=0.08,
            subsample=0.9,
            colsample_bytree=0.9,
            objective="multi:softprob",
            eval_metric="mlogloss",
            n_jobs=-1,
            tree_method="hist",
        )
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.feature_columns = FEATURE_COLUMNS
        self._fitted = False

    def preprocess(self, dataframe: pd.DataFrame, *, fit: bool = False) -> tuple[np.ndarray, np.ndarray | None]:
        frame = dataframe.copy()
        frame.columns = [str(c).strip() for c in frame.columns]
        rename = {
            "Flow Duration": "flow_duration",
            "Total Fwd Packets": "total_fwd_packets",
            "Total Backward Packets": "total_bwd_packets",
            "Fwd Packet Length Mean": "fwd_packet_length_mean",
            "Bwd Packet Length Mean": "bwd_packet_length_mean",
            "Flow Bytes/s": "flow_bytes_s",
            "Flow Packets/s": "flow_packets_s",
            "Fwd IAT Mean": "fwd_iat_mean",
            "Bwd IAT Mean": "bwd_iat_mean",
            "Packet Length Std": "packet_length_std",
            "Label": "label",
        }
        frame = frame.rename(columns=rename)
        for col in self.feature_columns:
            if col not in frame.columns:
                frame[col] = 0.0
        x = frame[self.feature_columns].replace([np.inf, -np.inf], np.nan).fillna(0.0).to_numpy(dtype=np.float32)
        if fit:
            x = self.scaler.fit_transform(x)
        elif self._fitted:
            x = self.scaler.transform(x)
        y = None
        target_col = None
        for cand in ["label", "Label", "type", "attack_type"]:
            if cand in frame.columns:
                target_col = cand
                break
        if target_col:
            labels = frame[target_col].astype(str).str.strip()
            labels = labels.replace(
                {
                    "Web Attack – Sql Injection": "SQLi",
                    "Web Attack – XSS": "XSS",
                    "Web Attack – Brute Force": "BruteForce",
                    "DoS Hulk": "DoS",
                    "DoS GoldenEye": "DoS",
                    "DoS slowloris": "DoS",
                    "DoS Slowhttptest": "DoS",
                }
            )
            if fit:
                y = self.label_encoder.fit_transform(labels)
            else:
                y = self.label_encoder.transform(labels)
        return x, y

    def train(self, x_train: np.ndarray | pd.DataFrame, y_train: np.ndarray | None = None) -> "ThreatClassifier":
        if isinstance(x_train, pd.DataFrame):
            x_train, y_train = self.preprocess(x_train, fit=True)
        else:
            x_train = self.scaler.fit_transform(x_train)
            if y_train is not None and y_train.dtype.kind not in {"i", "u"}:
                y_train = self.label_encoder.fit_transform(y_train)
        self.model.fit(x_train, y_train)
        self._fitted = True
        return self

    def predict(self, x_test: np.ndarray | pd.DataFrame | dict[str, Any]) -> dict[str, Any]:
        if isinstance(x_test, dict):
            x_test = pd.DataFrame([x_test])
        if isinstance(x_test, pd.DataFrame):
            x_test, _ = self.preprocess(x_test, fit=False)
        elif self._fitted:
            x_test = self.scaler.transform(x_test)
        proba = self.model.predict_proba(x_test)[0]
        idx = int(np.argmax(proba))
        label = self.label_encoder.inverse_transform([idx])[0] if self._fitted else ATTACK_LABELS[idx]
        return {
            "ml_prediction": str(label),
            "confidence": float(proba[idx]),
            "distribution": {
                str(self.label_encoder.classes_[i] if self._fitted else ATTACK_LABELS[i]): float(p)
                for i, p in enumerate(proba)
            },
        }

    def evaluate(self, x_test: np.ndarray | pd.DataFrame, y_test: np.ndarray | None = None) -> dict[str, Any]:
        if isinstance(x_test, pd.DataFrame):
            x_test, y_test = self.preprocess(x_test, fit=False)
        preds = self.model.predict(x_test)
        return {
            "f1_weighted": float(f1_score(y_test, preds, average="weighted", zero_division=0)),
            "precision_weighted": float(precision_score(y_test, preds, average="weighted", zero_division=0)),
            "recall_weighted": float(recall_score(y_test, preds, average="weighted", zero_division=0)),
            "report": classification_report(y_test, preds, zero_division=0),
        }

    def export_onnx(self, path: str | Path | None = None) -> Path:
        import onnxmltools
        from onnxmltools.convert.common.data_types import FloatTensorType

        settings = get_settings()
        m_dir = Path(settings.model_dir)
        if not m_dir.is_absolute() and Path("backend/app/ml/models").exists():
            m_dir = Path("backend/app/ml/models")
        m_dir.mkdir(parents=True, exist_ok=True)
        out = Path(path) if path else m_dir / "xgb_ids.onnx"
        out.parent.mkdir(parents=True, exist_ok=True)
        onnx_model = onnxmltools.convert_xgboost(
            self.model,
            initial_types=[("input", FloatTensorType([None, len(self.feature_columns)]))],
        )
        onnxmltools.utils.save_model(onnx_model, str(out))
        joblib.dump(
            {"scaler": self.scaler, "label_encoder": self.label_encoder, "features": self.feature_columns},
            m_dir / "scaler.pkl",
        )
        joblib.dump(self, m_dir / "xgb_ids.pkl")
        return out

    def save(self, path: str | Path | None = None) -> Path:
        settings = get_settings()
        m_dir = Path(settings.model_dir)
        if not m_dir.is_absolute() and Path("backend/app/ml/models").exists():
            m_dir = Path("backend/app/ml/models")
        m_dir.mkdir(parents=True, exist_ok=True)
        out = Path(path) if path else m_dir / "xgb_ids.pkl"
        out.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, out)
        joblib.dump(self.scaler, m_dir / "scaler.pkl")
        return out

    @classmethod
    def load(cls, path: str | Path | None = None) -> "ThreatClassifier":
        settings = get_settings()
        file_path = Path(path) if path else Path(settings.model_dir) / "xgb_ids.pkl"
        return joblib.load(file_path)


def train_on_frame(df: pd.DataFrame) -> ThreatClassifier:
    clf = ThreatClassifier()
    train_df, _ = train_test_split(df, test_size=0.2, random_state=42, stratify=df.get("label"))
    return clf.train(train_df)


def default_classifier() -> ThreatClassifier:
    settings = get_settings()
    path = Path(settings.model_dir) / "xgb_ids.pkl"
    if path.exists():
        return ThreatClassifier.load(path)
    rng = np.random.default_rng(11)
    rows = []
    for i, label in enumerate(ATTACK_LABELS):
        block = rng.normal(loc=i, scale=0.4, size=(40, len(FEATURE_COLUMNS)))
        frame = pd.DataFrame(block, columns=FEATURE_COLUMNS)
        frame["label"] = label
        rows.append(frame)
    return ThreatClassifier().train(pd.concat(rows, ignore_index=True))
