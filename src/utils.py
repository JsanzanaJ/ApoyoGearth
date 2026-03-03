from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import numpy as np


def normalize_text(value: object) -> str:
    """Normalize text: strip, lowercase, remove accents, collapse spaces."""
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"\s+", " ", text)
    return text


def safe_float(value: object) -> float:
    """Convert to float returning np.nan for invalid values."""
    try:
        if value is None:
            return np.nan
        if isinstance(value, str):
            value = value.strip().replace(",", ".")
        return float(value)
    except (TypeError, ValueError):
        return np.nan


def ensure_directory(path: str | Path) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory
