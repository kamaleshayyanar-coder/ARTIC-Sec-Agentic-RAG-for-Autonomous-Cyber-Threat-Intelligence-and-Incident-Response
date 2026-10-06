"""ONNX Runtime inference with latency benchmarks."""

from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
import pandas as pd

from app.config import get_settings
from app.ml.anomaly_detector import FEATURE_COLUMNS

try:
    import onnxruntime as ort
except Exception:  # pragma: no cover
    ort = None


class ONNXInferenceEngine:
    def __init__(self, model_path: str | Path | None = None) -> None:
        settings = get_settings()
        self.model_path = Path(model_path) if model_path else Path(settings.model_dir) / "xgb_ids.onnx"
        self.session: Any = None
        if ort is not None and self.model_path.exists():
            self.session = ort.InferenceSession(str(self.model_path), providers=["CPUExecutionProvider"])

    def load_onnx_model(self, path: str | Path | None = None) -> "ONNXInferenceEngine":
        if ort is None:
            raise RuntimeError("onnxruntime is not installed")
        self.model_path = Path(path) if path else self.model_path
        self.session = ort.InferenceSession(str(self.model_path), providers=["CPUExecutionProvider"])
        return self

    def _input_name(self) -> str:
        if self.session is None:
            raise RuntimeError("ONNX session not loaded")
        return self.session.get_inputs()[0].name

    def predict(self, sample: np.ndarray | dict[str, Any] | pd.DataFrame) -> np.ndarray:
        matrix = self._as_matrix(sample)
        if self.session is None:
            raise RuntimeError("ONNX model not available; train and export first")
        outputs = self.session.run(None, {self._input_name(): matrix})
        return np.asarray(outputs[0])

    def batch_predict(self, dataframe: pd.DataFrame) -> np.ndarray:
        return self.predict(dataframe)

    def benchmark_latency(self, n: int = 200) -> dict[str, float]:
        rng = np.random.default_rng(0)
        samples = rng.normal(size=(n, len(FEATURE_COLUMNS))).astype(np.float32)
        timings: list[float] = []
        for i in range(n):
            start = perf_counter()
            if self.session is not None:
                self.predict(samples[i : i + 1])
            elapsed = (perf_counter() - start) * 1000
            timings.append(elapsed)
        arr = np.array(timings)
        return {
            "p50_ms": float(np.percentile(arr, 50)),
            "p95_ms": float(np.percentile(arr, 95)),
            "p99_ms": float(np.percentile(arr, 99)),
            "mean_ms": float(arr.mean()),
            "n": float(n),
        }

    @staticmethod
    def _as_matrix(sample: np.ndarray | dict[str, Any] | pd.DataFrame) -> np.ndarray:
        if isinstance(sample, dict):
            sample = pd.DataFrame([sample])
        if isinstance(sample, pd.DataFrame):
            for col in FEATURE_COLUMNS:
                if col not in sample.columns:
                    sample[col] = 0.0
            return sample[FEATURE_COLUMNS].to_numpy(dtype=np.float32)
        return np.asarray(sample, dtype=np.float32)
