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


def seed(csv_path: Path, database_url: str, limit: int | None = None) -> int:
    df = pd.read_csv(csv_path)
    if limit:
        df = df.head(limit)
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
    parser.add_argument("--csv", type=Path, default=None, help="default: settings.synthetic_alerts_path")
    parser.add_argument("--database-url", default=settings.database_url)
    parser.add_argument("--limit", type=int, default=500)
    args = parser.parse_args()
    csv = user_path(args.csv) if args.csv else Path(settings.synthetic_alerts_path).resolve()
    n = seed(csv, args.database_url, args.limit)
    print(f"seeded={n}")


if __name__ == "__main__":
    main()
