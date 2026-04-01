"""Shared caching utilities for MCP servers.

Each server gets its own subdirectory under .cache/ with MD5-hashed
filenames and a configurable TTL (default 24h).
"""

import hashlib
import json
import os
import time
from pathlib import Path

CACHE_TTL = int(os.getenv("CACHE_TTL_HOURS", "24")) * 3600


def _cache_path(cache_dir: Path, key: str) -> Path:
    return cache_dir / f"{hashlib.md5(key.encode()).hexdigest()}.json"


def get_cached(cache_dir: Path, key: str) -> list[dict] | None:
    path = _cache_path(cache_dir, key)
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        if time.time() - data["timestamp"] < CACHE_TTL:
            return data["results"]
    return None


def set_cache(cache_dir: Path, key: str, results: list[dict]):
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = _cache_path(cache_dir, key)
    path.write_text(
        json.dumps({"timestamp": time.time(), "results": results}, ensure_ascii=False),
        encoding="utf-8",
    )
