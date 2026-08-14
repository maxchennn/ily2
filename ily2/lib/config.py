from __future__ import annotations

import json
import os


def load_config(path: str | None) -> dict:
    if not path:
        return {}
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Config dosyası bulunamadı: {path}")
    with open(path) as f:
        return json.load(f)


def save_config(path: str, data: dict) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
