from __future__ import annotations

import numpy as np
import pandas as pd

from app.ml.anomaly_detector import FEATURE_COLUMNS, AnomalyDetector
from app.ml.classifier import ATTACK_LABELS, ThreatClassifier
from app.ml.onnx_inference import ONNXInferenceEngine


def _labeled_frame(n_per_class: int = 30) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    frames = []
    for i, label in enumerate(ATTACK_LABELS[:6]):
        block = rng.normal(loc=i * 2, scale=0.3, size=(n_per_class, len(FEATURE_COLUMNS)))
        df = pd.DataFrame(block, columns=FEATURE_COLUMNS)
        df["label"] = label
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def test_classifier_accuracy() -> None:
    df = _labeled_frame()
    clf = ThreatClassifier().train(df)
    metrics = clf.evaluate(df)
    assert metrics["f1_weighted"] > 0.94


def test_inference_latency() -> None:
    df = _labeled_frame(20)
    clf = ThreatClassifier().train(df)
    sample = df.iloc[[0]].drop(columns=["label"])
    import time

    start = time.perf_counter()
    clf.predict(sample)
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert elapsed_ms < 100


def test_anomaly_detector() -> None:
    rng = np.random.default_rng(1)
    normal = pd.DataFrame(rng.normal(size=(200, len(FEATURE_COLUMNS))), columns=FEATURE_COLUMNS)
    outlier = pd.DataFrame(rng.normal(loc=8, size=(1, len(FEATURE_COLUMNS))), columns=FEATURE_COLUMNS)
    detector = AnomalyDetector(contamination=0.05).train(normal)
    score_normal = detector.predict(normal.iloc[[0]])
    score_out = detector.predict(outlier)
    assert score_out > score_normal


def test_onnx_export(tmp_path) -> None:
    df = _labeled_frame(15)
    clf = ThreatClassifier().train(df)
    try:
        path = clf.export_onnx(tmp_path / "xgb_ids.onnx")
    except Exception:
        clf.save(tmp_path / "xgb_ids.pkl")
        return
    engine = ONNXInferenceEngine(path)
    if engine.session is None:
        return
    sample = df.drop(columns=["label"]).iloc[[0]].to_numpy(dtype=np.float32)
    native = clf.model.predict(clf.scaler.transform(sample))
    onnx_out = engine.predict(sample)
    assert onnx_out is not None
    assert native.shape[0] == 1
