"""Train and persist the ML models used by the ingestion pipeline.

The repo ships app/ml/models/ empty (just a .gitkeep) and the model classes
only expose their training logic as methods, with no runnable script wiring
them together. This closes that gap.

Usage (from repo root, after `python pipelines/generate_synthetic.py`):

    python pipelines/train_models.py
    python pipelines/train_models.py --csv data/synthetic/synthetic_alerts.csv --n 20000

What it produces, all under backend/app/ml/models/:
    isolation_forest.pkl   -- anomaly detector (+ scaler bundled inside)
    anomaly_scaler.pkl      -- standalone copy of the scaler
    xgb_ids.pkl              -- the fitted ThreatClassifier (model+scaler+encoder)
    scaler.pkl                -- standalone scaler/encoder bundle
    xgb_ids.onnx              -- ONNX export, for onnx_inference.py / low-latency inference

Both `default_detector()` and `default_classifier()` in app/ml/* already
check for these files and load them automatically the next time the backend
starts -- no other wiring is needed once this script has run.
"""
from __future__ import annotations

import _pathfix  # noqa: F401
from _pathfix import user_path

import argparse
import subprocess
import sys
from pathlib import Path

import pandas as pd

from app.config import get_settings
from app.ml.anomaly_detector import AnomalyDetector
from app.ml.classifier import ThreatClassifier

REPO_ROOT = Path(__file__).resolve().parent.parent


def _ensure_csv(csv_path: Path, n: int) -> Path:
    if csv_path.exists():
        return csv_path
    print(f"[train_models] {csv_path} not found -- generating {n} synthetic rows first")
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "pipelines" / "generate_synthetic.py"), "--n", str(n), "--out", str(csv_path)],
        check=True,
    )
    return csv_path


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Train ARTIC-Sec ML models")
    parser.add_argument("--csv", type=Path, default=REPO_ROOT / "data" / "synthetic" / "synthetic_alerts.csv")
    parser.add_argument("--n", type=int, default=10_000, help="rows to generate if --csv doesn't exist yet")
    parser.add_argument("--model-dir", type=Path, default=REPO_ROOT / "backend" / "app" / "ml" / "models")
    parser.add_argument("--skip-onnx", action="store_true", help="skip the ONNX export step")
    args = parser.parse_args()

    csv_path = _ensure_csv(user_path(args.csv), args.n)
    args.model_dir = user_path(args.model_dir)
    args.model_dir.mkdir(parents=True, exist_ok=True)

    print(f"[train_models] loading {csv_path}")
    df = pd.read_csv(csv_path)
    df["label"] = df["type"]  # ThreatClassifier.preprocess() looks for a `label` column

    # --- Anomaly detector: unsupervised, train on everything (mostly BENIGN) ---
    print("[train_models] training IsolationForest anomaly detector ...")
    detector = AnomalyDetector()
    detector.train(df)
    detector.save_model(args.model_dir)
    scored = detector.detect_outliers(df.sample(min(2000, len(df)), random_state=1))
    flagged_rate = float((scored["anomaly_label"] == -1).mean())
    print(f"[train_models]   -> saved. sampled anomaly-flag rate={flagged_rate:.3f}")

    # --- Threat classifier: supervised multi-class, holdout eval ---
    print("[train_models] training XGBoost threat classifier ...")
    from sklearn.model_selection import train_test_split

    train_df, test_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df["label"])
    clf = ThreatClassifier()
    clf.train(train_df)
    metrics = clf.evaluate(test_df)
    print(
        "[train_models]   -> f1_weighted={f1_weighted:.4f} precision={precision_weighted:.4f} recall={recall_weighted:.4f}".format(
            **metrics
        )
    )
    print(metrics["report"])
    clf.save(args.model_dir / "xgb_ids.pkl")

    if not args.skip_onnx:
        try:
            out = clf.export_onnx(args.model_dir / "xgb_ids.onnx")
            print(f"[train_models]   -> ONNX export saved to {out}")
        except Exception as exc:  # onnxmltools/onnx quirks shouldn't block a usable .pkl model
            print(f"[train_models]   ! ONNX export skipped ({exc}); xgb_ids.pkl is still usable via joblib")

    print(f"[train_models] done. Models saved under {args.model_dir}")
    print("[train_models] restart the backend (or it will pick them up on next default_detector()/default_classifier() call).")


if __name__ == "__main__":
    main()
