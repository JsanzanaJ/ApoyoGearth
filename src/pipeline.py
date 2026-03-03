from __future__ import annotations

import argparse
from pathlib import Path

from seia_io import clean_projects, read_input_file
from mapping import create_projects_map
from scoring import (
    apply_optional_hazard_layers,
    compute_total_score,
    get_rivers_data,
    projects_to_gdf,
    score_by_river_distance,
    score_slope_stub,
)
from utils import ensure_directory


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pipeline MVP SEIA - Chile")
    parser.add_argument("--input", required=True, help="Ruta CSV/XLS/XLSX exportado desde SEIA")
    parser.add_argument("--outdir", default="outputs", help="Directorio de salida para HTML/MD")
    parser.add_argument("--data-dir", default="data", help="Directorio para CSV intermedios/finales")
    parser.add_argument("--region", default=None, help="Filtro opcional por región")
    parser.add_argument("--categoria", default="inmobiliarios", help="Categoría objetivo (metadato)")
    parser.add_argument("--weight-rio", type=float, default=0.7)
    parser.add_argument("--weight-pendiente", type=float, default=0.2)
    parser.add_argument("--weight-amenaza", type=float, default=0.1)
    parser.add_argument(
        "--hazard-urls",
        nargs="*",
        default=None,
        help="URLs opcionales WMS/WFS para capas de amenaza (stub no bloqueante)",
    )
    return parser.parse_args()


def build_report(df, category: str) -> str:
    top20 = df.sort_values("score_total", ascending=False).head(20)
    region_counts = df.groupby("region", dropna=False).size().sort_values(ascending=False)
    estado_counts = df.groupby("estado", dropna=False).size().sort_values(ascending=False)

    lines = [
        "# Reporte resumen de proyectos SEIA",
        "",
        f"Categoría objetivo: **{category}**",
        "",
        "## Top 20 proyectos por score_total",
        "",
        "| # | Empresa | Proyecto | Región | Estado | Score |",
        "|---|---|---|---|---|---:|",
    ]

    for idx, row in enumerate(top20.itertuples(index=False), start=1):
        score = "N/A" if row.score_total != row.score_total else f"{row.score_total:.2f}"
        lines.append(
            f"| {idx} | {row.empresa} | {row.nombre_proyecto} | {row.region} | {row.estado} | {score} |"
        )

    lines.extend(["", "## Conteo por región", ""])
    for region, cnt in region_counts.items():
        lines.append(f"- {region}: {cnt}")

    lines.extend(["", "## Conteo por estado", ""])
    for estado, cnt in estado_counts.items():
        lines.append(f"- {estado}: {cnt}")

    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()

    outdir = ensure_directory(args.outdir)
    data_dir = ensure_directory(args.data_dir)

    raw = read_input_file(args.input)
    clean = clean_projects(raw, region_filter=args.region)
    clean["categoria_objetivo"] = args.categoria

    clean_path = data_dir / "proyectos_limpio.csv"
    clean.to_csv(clean_path, index=False, encoding="utf-8")

    projects_gdf = projects_to_gdf(clean)
    rivers_gdf = get_rivers_data(projects_gdf)

    scored = clean.copy()
    scored["score_rio"] = score_by_river_distance(projects_gdf, rivers_gdf)
    scored["score_pendiente"] = score_slope_stub(scored)
    scored["score_amenaza"] = apply_optional_hazard_layers(projects_gdf, args.hazard_urls)

    scored = compute_total_score(
        scored,
        weight_rio=args.weight_rio,
        weight_pendiente=args.weight_pendiente,
        weight_amenaza=args.weight_amenaza,
    )

    score_path = data_dir / "proyectos_score.csv"
    scored.to_csv(score_path, index=False, encoding="utf-8")

    fmap = create_projects_map(scored)
    map_path = outdir / "mapa_proyectos.html"
    fmap.save(str(map_path))

    report = build_report(scored, args.categoria)
    report_path = outdir / "reporte_resumen.md"
    Path(report_path).write_text(report, encoding="utf-8")

    print(f"[OK] Limpio: {clean_path}")
    print(f"[OK] Score: {score_path}")
    print(f"[OK] Mapa: {map_path}")
    print(f"[OK] Reporte: {report_path}")


if __name__ == "__main__":
    main()
