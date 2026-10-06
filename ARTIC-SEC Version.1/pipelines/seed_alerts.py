from __future__ import annotations

import argparse
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models.alert import Alert
from app.db.postgres import Base


def seed(csv_path: Path, database_url: str, limit: int | None = None) -> int:
    csv_file = Path(csv_path)
    if not csv_file.exists():
        candidates = [
            Path("data/synthetic/synthetic_alerts.csv"),
            Path(__file__).resolve().parent.parent / "data" / "synthetic" / "synthetic_alerts.csv",
        ]
        for c in candidates:
            if c.exists():
                csv_file = c
                break
    df = pd.read_csv(csv_file)
    if limit:
        df = df.head(limit)
    try:
        engine = create_engine(database_url)
        Base.metadata.create_all(engine)
    except Exception:
        database_url = "sqlite:///articsec.db"
        engine = create_engine(database_url)
        Base.metadata.create_all(engine)
    records = []
    for row in df.to_dict(orient="records"):
        records.append(
            Alert(
                type=str(row["type"]),
                src_ip=str(row["src_ip"]),
                dst_ip=str(row["dst_ip"]),
                risk_score=float(row["risk_score"]),
                ml_prediction=row.get("ml_prediction"),
                mitre_technique=row.get("mitre_technique") if pd.notna(row.get("mitre_technique")) else None,
                severity=str(row.get("severity") or "medium"),
                status=str(row.get("status") or "open"),
            )
        )
    with Session(engine) as session:
        session.add_all(records)
        session.commit()
    return len(records)


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=settings.synthetic_alerts_path)
    parser.add_argument("--database-url", default=settings.database_url)
    parser.add_argument("--limit", type=int, default=500)
    args = parser.parse_args()
    n = seed(args.csv, args.database_url, args.limit)
    print(f"seeded={n}")


if __name__ == "__main__":
    main()
