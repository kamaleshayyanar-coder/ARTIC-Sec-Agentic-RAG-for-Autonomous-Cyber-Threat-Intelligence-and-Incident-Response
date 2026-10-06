from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

ATTACK_WEIGHTS = {
    "BENIGN": 0.60,
    "PortScan": 0.10,
    "DDoS": 0.07,
    "DoS": 0.05,
    "SQLi": 0.04,
    "XSS": 0.03,
    "BruteForce": 0.03,
    "Bot": 0.03,
    "Infiltration": 0.02,
    "FTP-Patator": 0.015,
    "SSH-Patator": 0.015,
}

MITRE = {
    "BENIGN": None,
    "PortScan": "T1046",
    "DDoS": "T1498",
    "DoS": "T1499",
    "SQLi": "T1190",
    "XSS": "T1059",
    "BruteForce": "T1110",
    "Bot": "T1071",
    "Infiltration": "T1021",
    "FTP-Patator": "T1110",
    "SSH-Patator": "T1110.001",
}

SEVERITY = {
    "BENIGN": "low",
    "PortScan": "medium",
    "DDoS": "critical",
    "DoS": "high",
    "SQLi": "high",
    "XSS": "medium",
    "BruteForce": "high",
    "Bot": "high",
    "Infiltration": "critical",
    "FTP-Patator": "medium",
    "SSH-Patator": "medium",
}


def _ip(rng: random.Random, public: bool = True) -> str:
    if public:
        return f"{rng.randint(11, 223)}.{rng.randint(0, 255)}.{rng.randint(0, 255)}.{rng.randint(1, 254)}"
    return f"10.{rng.randint(0, 10)}.{rng.randint(0, 255)}.{rng.randint(1, 254)}"


def generate(n: int = 10_000, seed: int = 7) -> pd.DataFrame:
    rng = random.Random(seed)
    labels = list(ATTACK_WEIGHTS)
    weights = list(ATTACK_WEIGHTS.values())
    now = datetime.now(timezone.utc)
    rows = []
    for i in range(n):
        label = rng.choices(labels, weights=weights, k=1)[0]
        ts = now - timedelta(seconds=rng.randint(0, 86_400))
        risk = 0.05 if label == "BENIGN" else round(rng.uniform(0.35, 0.98), 3)
        rows.append(
            {
                "id": i + 1,
                "type": label,
                "src_ip": _ip(rng, public=label != "BENIGN" or rng.random() > 0.3),
                "dst_ip": _ip(rng, public=False),
                "risk_score": risk,
                "ml_prediction": label,
                "mitre_technique": MITRE[label],
                "severity": SEVERITY[label],
                "status": rng.choice(["open", "open", "investigating", "resolved"]),
                "timestamp": ts.isoformat(),
                "flow_duration": rng.random() * 1e6,
                "total_fwd_packets": rng.randint(1, 500),
                "total_bwd_packets": rng.randint(1, 500),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=10_000)
    parser.add_argument("--out", type=Path, default=Path("data/synthetic/synthetic_alerts.csv"))
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df = generate(args.n)
    df.to_csv(args.out, index=False)
    print(df["type"].value_counts().to_string())
    print(f"wrote {args.out} rows={len(df)}")


if __name__ == "__main__":
    main()
