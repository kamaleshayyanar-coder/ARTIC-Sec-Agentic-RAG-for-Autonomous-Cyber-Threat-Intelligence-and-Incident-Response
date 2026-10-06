from __future__ import annotations

import _pathfix  # noqa: F401  (adds backend/ to sys.path for `app.*` imports)
from _pathfix import user_path

import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models.alert import Alert
from app.db.postgres import Base
from app.ml.classifier import ThreatClassifier


CIC_TO_TYPE = {
    "BENIGN": "BENIGN",
    "DDoS": "DDoS",
    "PortScan": "PortScan",
    "FTP-Patator": "FTP-Patator",
    "SSH-Patator": "SSH-Patator",
    "Bot": "Bot",
    "Infiltration": "Infiltration",
    "Heartbleed": "Heartbleed",
}


def _normalize_label(label: str) -> str:
    value = str(label).strip()
    if "Sql Injection" in value or "SQL Injection" in value:
        return "SQLi"
    if "XSS" in value:
        return "XSS"
    if "Brute Force" in value:
        return "BruteForce"
    if value.startswith("DoS"):
        return "DoS"
    return CIC_TO_TYPE.get(value, value[:64])


def ingest(csv_path: Path, database_url: str, chunksize: int = 10_000) -> int:
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    clf = ThreatClassifier()
    inserted = 0
    for chunk in pd.read_csv(csv_path, chunksize=chunksize, low_memory=False):
        chunk.columns = [c.strip() for c in chunk.columns]
        chunk = chunk.replace([float("inf"), float("-inf")], pd.NA).dropna(how="all")
        records = []
        for _, row in chunk.iterrows():
            label = _normalize_label(row.get("Label") or row.get("label") or "UNKNOWN")
            if label == "BENIGN":
                continue
            src = str(row.get("Source IP") or row.get("src_ip") or "0.0.0.0")
            dst = str(row.get("Destination IP") or row.get("dst_ip") or "0.0.0.0")
            records.append(
                Alert(
                    type=label,
                    src_ip=src[:64],
                    dst_ip=dst[:64],
                    risk_score=0.65,
                    ml_prediction=label,
                    severity="high" if label in {"DDoS", "Infiltration", "Heartbleed"} else "medium",
                    status="open",
                )
            )
        if not records:
            continue
        with Session(engine) as session:
            session.add_all(records)
            try:
                session.commit()
                inserted += len(records)
            except Exception:
                session.rollback()
        print(f"ingested={inserted}")
    return inserted


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Load CIC-IDS2017 CSV into PostgreSQL alerts")
    parser.add_argument("--csv", type=Path, default=None, help="default: <cic_data_dir>/Friday-WorkingHours.csv")
    parser.add_argument("--database-url", default=settings.database_url)
    args = parser.parse_args()
    args.csv = user_path(args.csv) if args.csv else (settings.cic_data_dir / "Friday-WorkingHours.csv").resolve()
    if not args.csv.exists():
        raise SystemExit(f"CSV not found: {args.csv}. Download CIC-IDS2017 first.")
    total = ingest(args.csv, args.database_url)
    print(f"done total={total}")


if __name__ == "__main__":
    main()
