from __future__ import annotations

import json
from pathlib import Path


def read_last_sync(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("last_sync")
    except (json.JSONDecodeError, OSError) as error:
        raise RuntimeError(f"Não foi possível ler o estado de sincronização: {error}") from error


def save_last_sync(path: Path, timestamp: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"last_sync": timestamp}, indent=2), encoding="utf-8")
