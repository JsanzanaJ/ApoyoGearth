from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from utils import normalize_text, safe_float

REQUIRED_STANDARD_COLUMNS = [
    "nombre_proyecto",
    "empresa",
    "region",
    "comuna",
    "estado",
    "tipo",
    "lat",
    "lon",
]

COLUMN_SYNONYMS = {
    "nombre_proyecto": ["nombre_proyecto", "nombre", "proyecto", "nombre proyecto"],
    "empresa": ["empresa", "titular", "razon_social", "razon social"],
    "region": ["region", "región"],
    "comuna": ["comuna"],
    "estado": ["estado", "estado_expediente", "estado expediente"],
    "tipo": ["tipo", "tipo_seia", "dia/eia", "dia_eia"],
    "lat": ["lat", "latitude", "latitud", "y"],
    "lon": ["lon", "lng", "longitud", "longitude", "x"],
}


def _normalize_column_name(name: str) -> str:
    return normalize_text(name).replace("_", " ")


def map_columns(df: pd.DataFrame) -> pd.DataFrame:
    normalized_map = {_normalize_column_name(col): col for col in df.columns}
    renamed: dict[str, str] = {}

    for standard_col, candidates in COLUMN_SYNONYMS.items():
        for candidate in candidates:
            key = _normalize_column_name(candidate)
            if key in normalized_map:
                renamed[normalized_map[key]] = standard_col
                break

    mapped = df.rename(columns=renamed)
    missing = [col for col in REQUIRED_STANDARD_COLUMNS if col not in mapped.columns]
    if missing:
        raise ValueError(
            "Faltan columnas obligatorias tras el mapeo: " + ", ".join(missing)
        )

    return mapped


def read_input_file(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix in {".csv", ".txt"}:
        try:
            df = pd.read_csv(path)
        except UnicodeDecodeError:
            df = pd.read_csv(path, encoding="latin-1")
    elif suffix in {".xls", ".xlsx"}:
        df = pd.read_excel(path)
    else:
        raise ValueError(f"Formato no soportado: {suffix}")

    return map_columns(df)


def clean_projects(
    df: pd.DataFrame,
    region_filter: str | None = None,
    dedupe_subset: Iterable[str] = ("nombre_proyecto", "empresa", "lat", "lon"),
) -> pd.DataFrame:
    cleaned = df.copy()

    text_cols = ["nombre_proyecto", "empresa", "region", "comuna", "estado", "tipo"]
    for col in text_cols:
        cleaned[col] = cleaned[col].fillna("").astype(str).str.strip()

    cleaned["lat"] = cleaned["lat"].apply(safe_float)
    cleaned["lon"] = cleaned["lon"].apply(safe_float)

    cleaned = cleaned.dropna(subset=["lat", "lon"])
    cleaned = cleaned[(cleaned["lat"].between(-90, 90)) & (cleaned["lon"].between(-180, 180))]

    if region_filter:
        region_target = normalize_text(region_filter)
        cleaned = cleaned[
            cleaned["region"].apply(normalize_text) == region_target
        ]

    cleaned = cleaned.drop_duplicates(subset=list(dedupe_subset), keep="first")
    cleaned = cleaned.reset_index(drop=True)

    return cleaned
