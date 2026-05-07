# MVP reproducible: proyectos SEIA (Chile)

Este repositorio implementa un **MVP en Python** para procesar un archivo exportado del mapa de proyectos sometidos al SEIA, calcular un riesgo simple y generar salidas tabulares y visuales.


## Portafolio minimalista

Este repositorio también incluye una landing page estática para un perfil profesional orientado a datos, geografía, análisis geográfico y ciencia de datos.

Archivos principales:

- `index.html`: estructura semántica del portafolio.
- `styles.css`: sistema visual minimalista, responsive y centrado en contenido.

Para verlo localmente:

```bash
python3 -m http.server 8000
```

Luego abre `http://localhost:8000` en el navegador.

## Qué genera

Al ejecutar el pipeline se crean:

- `data/proyectos_limpio.csv`
- `data/proyectos_score.csv` (incluye `score_total` y componentes)
- `outputs/mapa_proyectos.html`
- `outputs/reporte_resumen.md`

## Estructura

- `src/pipeline.py`: CLI principal
- `src/io.py`: compatibilidad de nombre solicitado
- `src/seia_io.py`: lectura, mapeo de columnas, limpieza y validación
- `src/scoring.py`: cálculo de score por ríos, pendiente (stub) y amenazas (stub no bloqueante)
- `src/mapping.py`: creación de mapa Folium
- `src/utils.py`: utilidades comunes

## Requisitos

- Python 3.10+
- Conexión a internet opcional para datos de ríos (Overpass/Natural Earth)

## Instalación (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> Si aparece política de ejecución bloqueada:
>
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

## Ejecución

Ejemplo con el archivo de muestra:

```powershell
python src/pipeline.py --input data/seia_export_sample.csv --outdir outputs
```

Comando objetivo solicitado:

```powershell
python src/pipeline.py --input data/seia_export.csv --outdir outputs
```

Parámetros relevantes:

- `--region "Región Metropolitana"` filtra región.
- `--categoria "inmobiliarios"` etiqueta la categoría objetivo.
- `--weight-rio`, `--weight-pendiente`, `--weight-amenaza` ajustan ponderaciones.
- `--hazard-urls` acepta URLs WMS/WFS opcionales (en MVP quedan como stub, no interrumpen ejecución).

## Lógica de scoring (MVP)

- `score_rio`: distancia al río más cercano en km (Overpass; fallback Natural Earth).
- `score_pendiente`: **stub** (NaN) documentado para futura integración SRTM.
- `score_amenaza`: **stub** (NaN) para capas de amenaza externas opcionales.
- `score_total`: promedio ponderado usando solo componentes disponibles.

## Validaciones de entrada

Se mapean sinónimos de columnas y se validan campos mínimos:

- `nombre_proyecto`, `empresa/titular`, `region`, `comuna`, `estado`, `tipo`, `lat`, `lon`.

También se normaliza texto, se eliminan duplicados y coordenadas inválidas.

## Troubleshooting común en Windows

1. **Error con `fiona`/`geopandas`**:
   - Actualiza pip: `python -m pip install --upgrade pip setuptools wheel`
   - Reintenta `pip install -r requirements.txt`
2. **Codificación CSV (`UnicodeDecodeError`)**:
   - El pipeline intenta UTF-8 y fallback `latin-1` automáticamente.
3. **No hay red / falla Overpass**:
   - Se intenta fallback a Natural Earth.
   - Si ambos fallan, `score_rio` queda `NaN` sin romper la ejecución.

## Consideraciones de datos

- No se realiza scraping de LinkedIn ni se usan datos privados.
- Se trabaja con el archivo exportado manualmente por el usuario y fuentes públicas.
