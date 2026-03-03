from __future__ import annotations

from typing import Iterable

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
from shapely.geometry import LineString, MultiLineString, shape

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def projects_to_gdf(df: pd.DataFrame) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        df.copy(),
        geometry=gpd.points_from_xy(df["lon"], df["lat"]),
        crs="EPSG:4326",
    )


def fetch_rivers_overpass(gdf_projects: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    minx, miny, maxx, maxy = gdf_projects.total_bounds
    query = f"""
    [out:json][timeout:60];
    (
      way["waterway"~"river|stream"]({miny},{minx},{maxy},{maxx});
      relation["waterway"~"river|stream"]({miny},{minx},{maxy},{maxx});
    );
    out geom;
    """

    response = requests.post(OVERPASS_URL, data=query, timeout=90)
    response.raise_for_status()
    payload = response.json()

    lines = []
    names = []
    for element in payload.get("elements", []):
        geom = element.get("geometry")
        if not geom:
            continue
        coords = [(p["lon"], p["lat"]) for p in geom]
        if len(coords) < 2:
            continue
        lines.append(LineString(coords))
        names.append(element.get("tags", {}).get("name", "sin_nombre"))

    if not lines:
        return gpd.GeoDataFrame(columns=["name", "geometry"], geometry="geometry", crs="EPSG:4326")

    return gpd.GeoDataFrame({"name": names}, geometry=lines, crs="EPSG:4326")


def fetch_rivers_natural_earth() -> gpd.GeoDataFrame:
    url = "https://naciscdn.org/naturalearth/10m/physical/ne_10m_rivers_lake_centerlines.zip"
    gdf = gpd.read_file(url)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    return gdf[[col for col in gdf.columns if col != "geometry"] + ["geometry"]]


def get_rivers_data(projects_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    try:
        rivers = fetch_rivers_overpass(projects_gdf)
        if not rivers.empty:
            return rivers
    except Exception:
        pass

    try:
        rivers = fetch_rivers_natural_earth()
        minx, miny, maxx, maxy = projects_gdf.total_bounds
        bbox = gpd.GeoDataFrame(geometry=[shape({
            "type": "Polygon",
            "coordinates": [[
                [minx, miny], [maxx, miny], [maxx, maxy], [minx, maxy], [minx, miny]
            ]],
        })], crs="EPSG:4326")
        rivers = gpd.clip(rivers, bbox)
        return rivers
    except Exception:
        return gpd.GeoDataFrame(columns=["geometry"], geometry="geometry", crs="EPSG:4326")


def score_by_river_distance(projects_gdf: gpd.GeoDataFrame, rivers_gdf: gpd.GeoDataFrame) -> pd.Series:
    if rivers_gdf.empty:
        return pd.Series(np.nan, index=projects_gdf.index, name="score_rio")

    projects_m = projects_gdf.to_crs("EPSG:32719")
    rivers_m = rivers_gdf.to_crs("EPSG:32719")
    distances_km = projects_m.geometry.apply(lambda p: rivers_m.distance(p).min() / 1000.0)
    score = 100.0 / (1.0 + distances_km)
    return score.rename("score_rio")


def score_slope_stub(projects_df: pd.DataFrame) -> pd.Series:
    return pd.Series(np.nan, index=projects_df.index, name="score_pendiente")


def apply_optional_hazard_layers(
    projects_gdf: gpd.GeoDataFrame,
    hazard_urls: Iterable[str] | None = None,
) -> pd.Series:
    _ = projects_gdf
    _ = hazard_urls
    return pd.Series(np.nan, index=projects_gdf.index, name="score_amenaza")


def compute_total_score(
    df: pd.DataFrame,
    weight_rio: float,
    weight_pendiente: float,
    weight_amenaza: float,
) -> pd.DataFrame:
    scored = df.copy()
    components = ["score_rio", "score_pendiente", "score_amenaza"]
    for col in components:
        if col not in scored.columns:
            scored[col] = np.nan

    weighted_sum = (
        scored["score_rio"].fillna(0) * weight_rio
        + scored["score_pendiente"].fillna(0) * weight_pendiente
        + scored["score_amenaza"].fillna(0) * weight_amenaza
    )
    weight_sum = (
        (~scored["score_rio"].isna()).astype(float) * weight_rio
        + (~scored["score_pendiente"].isna()).astype(float) * weight_pendiente
        + (~scored["score_amenaza"].isna()).astype(float) * weight_amenaza
    )
    scored["score_total"] = np.where(weight_sum > 0, weighted_sum / weight_sum, np.nan)
    return scored
