"""Import this first in any pipelines/*.py script that needs `app.*`.

Two things the raw scripts got wrong when run from the repo root:
  1. `from app.config import ...` failed (app/ lives under backend/).
  2. Settings paths like `../data/synthetic/...` and `sqlite:///./articsec.db`
     are relative to backend/ (where uvicorn runs), so pipelines and the API
     could silently read/write different files.

So we put backend/ on sys.path AND chdir into it, making pipelines behave
exactly like the API process. Paths a user types on the command line are
still resolved against the directory they launched from -- use `user_path()`.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ORIGINAL_CWD = Path.cwd()
_BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))
os.chdir(_BACKEND_DIR)


def user_path(p: Path | str) -> Path:
    p = Path(p)
    return p if p.is_absolute() else (ORIGINAL_CWD / p).resolve()
