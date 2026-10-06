"""Classifier accuracy on synthetic or CIC holdout CSV."""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import argparse
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, roc_auc_score
from sklearn.model_selection import train_test_split

from app.ml.classifier import ThreatClassifier, train_on_frame


def load_frame(path: Path | None) -> pd.DataFrame:
    if path and path.exists():
        df = pd.read_csv(path)
        if "Label" in df.columns:
            df = df.rename(columns={"Label": "label"})
        return df
    from pipelines.generate_synthetic import generate

    df = generate(4000)
    df = df.rename(columns={"type": "label"})
    return df


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=None)
    args = parser.parse_args()
    df = load_frame(args.csv)
    train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)
    clf = ThreatClassifier().train(train_df)
    metrics = clf.evaluate(test_df)
    x_test, y_test = clf.preprocess(test_df, fit=False)
    preds = clf.model.predict(x_test)
    cm = confusion_matrix(y_test, preds)
    y_bin = (np.array(y_test) != list(clf.label_encoder.transform(["BENIGN"]))[0]).astype(int) if "BENIGN" in clf.label_encoder.classes_ else None
    proba = clf.model.predict_proba(x_test)
    auc = None
    if y_bin is not None:
        attack_mass = 1.0 - proba[:, list(clf.label_encoder.classes_).index("BENIGN")]
        auc = float(roc_auc_score(y_bin, attack_mass))
    print(metrics["report"])
    print("f1_weighted", metrics["f1_weighted"])
    print("precision_weighted", metrics["precision_weighted"])
    print("recall_weighted", metrics["recall_weighted"])
    print("roc_auc_benign_vs_attack", auc)
    print("confusion_matrix_shape", cm.shape)


if __name__ == "__main__":
    main()
