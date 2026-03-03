from __future__ import annotations

import folium
import pandas as pd


def _score_color(score: float) -> str:
    if pd.isna(score):
        return "gray"
    if score >= 70:
        return "red"
    if score >= 40:
        return "orange"
    return "green"


def _score_band(score: float) -> str:
    if pd.isna(score):
        return "Sin score"
    if score >= 70:
        return "Alto (>=70)"
    if score >= 40:
        return "Medio (40-69)"
    return "Bajo (<40)"


def create_projects_map(df: pd.DataFrame) -> folium.Map:
    center = [-33.45, -70.66]
    if not df.empty:
        center = [df["lat"].mean(), df["lon"].mean()]

    fmap = folium.Map(location=center, zoom_start=5, tiles="CartoDB positron")

    estado_groups: dict[str, folium.FeatureGroup] = {}
    band_groups: dict[str, folium.FeatureGroup] = {}

    for estado in sorted(df["estado"].fillna("Sin estado").unique()):
        group = folium.FeatureGroup(name=f"Estado: {estado}", show=False)
        group.add_to(fmap)
        estado_groups[estado] = group

    for band in ["Alto (>=70)", "Medio (40-69)", "Bajo (<40)", "Sin score"]:
        group = folium.FeatureGroup(name=f"Score: {band}", show=False)
        group.add_to(fmap)
        band_groups[band] = group

    all_group = folium.FeatureGroup(name="Todos", show=True)
    all_group.add_to(fmap)

    for _, row in df.iterrows():
        score = row.get("score_total")
        score_html = f"{score:.2f}" if pd.notna(score) else "N/A"
        popup_html = (
            f"<b>Empresa:</b> {row.get('empresa', '')}<br>"
            f"<b>Proyecto:</b> {row.get('nombre_proyecto', '')}<br>"
            f"<b>Región:</b> {row.get('region', '')}<br>"
            f"<b>Estado:</b> {row.get('estado', '')}<br>"
            f"<b>Score total:</b> {score_html}"
        )
        popup = folium.Popup(popup_html, max_width=320)
        marker = folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=6,
            color=_score_color(score),
            fill=True,
            fill_opacity=0.8,
            popup=popup,
        )

        marker.add_to(all_group)
        estado = row.get("estado", "Sin estado")
        if estado in estado_groups:
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=6,
                color=_score_color(score),
                fill=True,
                fill_opacity=0.8,
                popup=popup,
            ).add_to(estado_groups[estado])

        band = _score_band(score)
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=6,
            color=_score_color(score),
            fill=True,
            fill_opacity=0.8,
            popup=popup,
        ).add_to(band_groups[band])

    folium.LayerControl(collapsed=False).add_to(fmap)
    return fmap
