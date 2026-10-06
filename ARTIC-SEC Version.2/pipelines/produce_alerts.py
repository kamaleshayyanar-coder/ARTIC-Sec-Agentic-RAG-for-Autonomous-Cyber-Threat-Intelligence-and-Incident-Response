"""Stream synthetic alerts into Kafka (topic: KAFKA_ALERT_TOPIC) to demo the Kafka ingest path.

    python pipelines/produce_alerts.py                 # 2 alerts/sec, forever (Ctrl+C to stop)
    python pipelines/produce_alerts.py --rate 10 --count 500
    python pipelines/produce_alerts.py --bootstrap localhost:9094   # from the host (default)

Requires: `docker compose --profile kafka up -d kafka` and KAFKA_ENABLED=true for the backend.
"""
from __future__ import annotations

import argparse
import json
import random
import time
from datetime import datetime, timezone

from kafka import KafkaProducer

LABELS = {
    "PortScan": ("T1046", "high"), "DDoS": ("T1498", "critical"), "SQLi": ("T1190", "high"),
    "BruteForce": ("T1110", "high"), "Bot": ("T1071", "medium"), "XSS": ("T1059", "medium"),
    "BENIGN": (None, "low"),
}


def ip(public: bool) -> str:
    return ".".join(str(random.randint(1, 223)) for _ in range(4)) if public else f"10.0.{random.randint(0,255)}.{random.randint(1,254)}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bootstrap", default="localhost:9094")
    ap.add_argument("--topic", default="security-alerts")
    ap.add_argument("--rate", type=float, default=2.0, help="alerts per second")
    ap.add_argument("--count", type=int, default=0, help="0 = run forever")
    a = ap.parse_args()

    producer = KafkaProducer(bootstrap_servers=a.bootstrap, value_serializer=lambda v: json.dumps(v).encode())
    sent = 0
    try:
        while a.count == 0 or sent < a.count:
            label = random.choices(list(LABELS), weights=[8, 3, 3, 3, 2, 2, 20])[0]
            technique, severity = LABELS[label]
            producer.send(a.topic, {
                "type": label, "src_ip": ip(True), "dst_ip": ip(False),
                "risk_score": round(random.uniform(0.05, 0.15) if label == "BENIGN" else random.uniform(0.4, 0.98), 3),
                "severity": severity, "mitre_technique": technique,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            sent += 1
            if sent % 20 == 0:
                print(f"sent={sent}")
            time.sleep(1.0 / a.rate)
    except KeyboardInterrupt:
        pass
    finally:
        producer.flush()
        print(f"done, sent={sent}")


if __name__ == "__main__":
    main()
