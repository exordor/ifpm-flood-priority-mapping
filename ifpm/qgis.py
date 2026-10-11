"""QGIS review packages: ``python -m ifpm qgis <area> [--package NAME|all] [--qa] [--out DIR|--in-place]``.

Ported from bin/package/build_goslar_qgis_full_audit.py (and the Secocha and ReviewMap
wrappers around it) and bin/validate/validate_goslar_qgis_layer_rendering.py. The layer
lists, package texts and QA settings are in the ``qgis`` section of configs/<area>.yaml.

Each package is written twice: a workspace-linked project (relative paths to data/ and
outputs/) under ``out_dir`` and a self-contained portable copy under ``portable_dir`` plus a
deterministic zip; exports/qgis_packages/package_index.json lists the portable packages.
Like ``run``, the build goes under --out (default outputs/_rerun/<area>/); --in-place
rebuilds the live packages.

Two halves: the workspace Python resolves the config into a JSON spec (``build``), then
this file is executed as a script by the QGIS application Python (``_qgis_main``), which
has PyQGIS but not the workspace packages. The QGIS half uses only the standard library,
PyQGIS, GDAL and NumPy, and does not import the rest of ifpm.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import uuid
import zipfile
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]

# Same discrete five-class palettes as the PIM overview figures (ColorBrewer, equal-interval 0-1).
PRIORITY_COLORS = ["#ffffcc", "#ffeda0", "#feb24c", "#f03b20", "#bd0026"]
CRITERIA_COLORS = {
    "flood_hazard": ["#f7fbff", "#deebf7", "#9ecae1", "#3182bd", "#08519c"],
    "sediment": ["#fff7ec", "#fee8c8", "#fdbb84", "#e34a33", "#7f0000"],
    "landuse_asm": ["#f7fcf5", "#c7e9c0", "#74c476", "#238b45", "#00441b"],
    "environmental": ["#f7f4f9", "#e7e1ef", "#c994c7", "#dd1c77", "#980043"],
    "socioeconomic": ["#ffffe5", "#fff7bc", "#fec44f", "#fe9929", "#cc4c02"],
}
STANDARD_CLASS_UPPER_BOUNDS = (0.2, 0.4, 0.6, 0.8, 1.0)
STANDARD_CLASS_LABELS = ("0.0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1.0")
INPUT_PALETTES = {
    "terrain": ["#f7fcf5", "#d9f0a3", "#addd8e", "#41ab5d", "#005a32"],
    "slope": ["#fff7ec", "#fee8c8", "#fdbb84", "#e34a33", "#7f0000"],
    "hydrology": ["#f7fbff", "#deebf7", "#9ecae1", "#3182bd", "#08519c"],
    "erosion": ["#ffffd4", "#fed98e", "#fe9929", "#d95f0e", "#993404"],
    "rainfall": ["#fff7ec", "#fdd49e", "#fc8d59", "#d7301f", "#7f0000"],
    "land": ["#f7fcf5", "#c7e9c0", "#74c476", "#238b45", "#00441b"],
    "population": ["#fff7f3", "#fcc5c0", "#fa9fb5", "#c51b8a", "#7a0177"],
    "wetness": ["#f7fbff", "#c6dbef", "#6baed6", "#2171b5", "#08306b"],
    "distance": ["#084081", "#2b8cbe", "#7bccc4", "#ccece6", "#f7fcfd"],
}
LAYER_DEFAULTS = {"palette": "", "layer_name": "", "unit": "", "claim_level": "diagnostic_only", "notes": ""}
MANIFEST_FIELDS = [
    "site", "layer_key", "display_name", "group", "role",
    "source_path", "source_type", "provider_crs", "unit", "visible_by_default",
    "claim_level", "style_path", "portable_source_path", "source_size_bytes",
    "source_sha256", "portable_size_bytes", "portable_sha256", "load_status", "notes",
]
PORTABLE_MANIFEST_FIELDS = [
    "site", "layer_key", "display_name", "group", "role", "source_type",
    "provider_crs", "unit", "visible_by_default", "claim_level",
    "portable_source_path", "portable_size_bytes", "portable_sha256",
    "load_status", "notes",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


# --- workspace side: config -> spec -> QGIS subprocess ------------------------------------

def discover_qgis_app() -> Path:
    configured = os.environ.get("QGIS_APP_PATH")
    candidates = [Path(configured)] if configured else [
        Path("/Applications/QGIS.app"), Path("/Applications/QGIS-LTR.app"),
        Path.home() / "Applications/QGIS.app", Path.home() / "Applications/QGIS-LTR.app",
        *sorted(Path("/Applications").glob("QGIS*.app")),
        *sorted((Path.home() / "Applications").glob("QGIS*.app")),
    ]
    for candidate in dict.fromkeys(candidates):
        if (candidate / "Contents/MacOS/python").exists():
            return candidate
    raise SystemExit("QGIS application not found; set QGIS_APP_PATH to the QGIS .app bundle")


def qgis_environment(app: Path) -> dict[str, str]:
    prefix = app / "Contents/Resources/qgis"
    env = os.environ.copy()
    env.update({
        "QT_QPA_PLATFORM": "offscreen",
        "QGIS_PREFIX_PATH": str(prefix),
        "PROJ_LIB": str(prefix / "proj"),
        "GDAL_DATA": str(prefix / "gdal"),
        "QT_PLUGIN_PATH": str(app / "Contents/PlugIns"),
        "GDAL_PAM_ENABLED": "NO",
    })
    return env


def package_spec(cfg, name: str, out: Path) -> dict:
    """Resolve one package of configs/<area>.yaml into the JSON spec the QGIS half reads."""
    q = cfg["qgis"]
    pkg = q["packages"][name]
    tokens = {key: item["template"].format(sha256=sha256(cfg.root / item["path"]))
              for key, item in q.get("lineage", {}).items()}
    layers = []
    for layer in q["layers"]:
        if "keys" in pkg and layer["key"] not in pkg["keys"]:
            continue
        layer = {**LAYER_DEFAULTS, **layer}
        layer.setdefault("visible", layer["kind"] == "vector")
        if "visible" in pkg:
            layer["visible"] = layer["key"] in pkg["visible"]
        layer["notes"] = layer["notes"].format(**tokens) if tokens else layer["notes"]
        layers.append(layer)
    if "keys" in pkg and len(layers) != len(pkg["keys"]):
        raise SystemExit(f"{cfg.area}/{name}: keys not in the layer list")
    return {
        "root": str(cfg.root), "site_key": q["site_key"], "project_crs": q["project_crs"],
        "package": name, "name": pkg["name"], "project_file": pkg["project_file"],
        "index_key": f"{q['site_key']}_{name.lower()}",
        "out_dir": str(out / pkg["out_dir"]), "portable_dir": str(out / pkg["portable_dir"]),
        "index_root": str(out / Path(pkg["portable_dir"]).parent.parent),
        "readme": pkg["readme"], "portable_readme": pkg["portable_readme"],
        "qa": pkg.get("qa"), "layers": layers,
        "generator_sha256": sha256(Path(__file__)),
        "config_sha256": sha256(cfg.root / "configs" / f"{cfg.area}.yaml"),
    }


def build(cfg, packages: list[str], out: Path, qa: bool = False) -> None:
    """Build the packages with the QGIS application Python, one subprocess per package."""
    app = discover_qgis_app()
    for name in packages:
        spec = package_spec(cfg, name, out)
        if not qa:
            spec["qa"] = None
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump(spec, handle)
        try:
            print(f"== {cfg.area} QGIS {name} -> {spec['out_dir']}", flush=True)
            # -P keeps ifpm/ off sys.path, so its modules cannot shadow standard-library names.
            done = subprocess.run([str(app / "Contents/MacOS/python"), "-P", str(Path(__file__).resolve()), handle.name],
                                  cwd=cfg.root, env=qgis_environment(app), check=False)
        finally:
            os.unlink(handle.name)
        if done.returncode:
            raise SystemExit(f"QGIS build of {cfg.area}/{name} failed ({done.returncode})")


# --- QGIS side ------------------------------------------------------------------------------

class Package:
    """Paths and layers of one package (from the JSON spec)."""

    def __init__(self, spec: dict):
        self.spec = spec
        self.root = Path(spec["root"])
        self.site = spec["site_key"]
        self.out_dir = Path(spec["out_dir"])
        self.style_dir = self.out_dir / "styles"
        self.manifest = self.out_dir / "manifest.csv"
        self.portable_dir = Path(spec["portable_dir"])
        self.project_name = spec["project_file"]
        self.layers = spec["layers"]
        self.layer_names = {layer["key"]: layer["layer_name"] for layer in self.layers}


def _palette(name: str) -> tuple[str, ...]:
    if name == "priority":
        return tuple(PRIORITY_COLORS)
    return tuple(CRITERIA_COLORS.get(name) or INPUT_PALETTES[name])


def _raster_range(layer, spec: dict) -> tuple[float, float]:
    if spec["unit"] == "0-1" or spec["role"] in {"priority_result", "criterion"}:
        return 0.0, 1.0
    from osgeo import gdal
    gdal.UseExceptions()
    dataset = gdal.Open(layer.source().split("|", 1)[0])
    if dataset is None:
        raise RuntimeError(f"GDAL could not open {layer.source()}")
    minimum, maximum = (float(v) for v in dataset.GetRasterBand(1).GetStatistics(False, True)[:2])
    dataset = None
    return (minimum, maximum) if minimum < maximum else (minimum, minimum + 1.0)


def apply_raster_style(layer, spec: dict, style_path: Path) -> None:
    from qgis.PyQt.QtGui import QColor
    from qgis.core import QgsColorRampShader, QgsRasterShader, QgsSingleBandPseudoColorRenderer

    minimum, maximum = _raster_range(layer, spec)
    colors = _palette(spec["palette"])
    # Priority and the five criteria keep the discrete equal-interval classes
    # (upper bounds 0.2/0.4/0.6/0.8/1.0) of the report maps; inputs get a ramp.
    if spec["role"] in {"priority_result", "criterion"}:
        values, labels, ramp_type = STANDARD_CLASS_UPPER_BOUNDS, STANDARD_CLASS_LABELS, QgsColorRampShader.Discrete
    else:
        fractions = (0.0, 0.25, 0.5, 0.75, 1.0)
        if spec["key"] in {"flow_accumulation", "population"} and minimum >= 0:
            low, high = math.log1p(minimum), math.log1p(maximum)
            values = tuple(math.expm1(low + f * (high - low)) for f in fractions)
        else:
            values = tuple(minimum + f * (maximum - minimum) for f in fractions)
        labels = tuple(f"{value:.4g}" for value in values)
        ramp_type = QgsColorRampShader.Interpolated
    items = [QgsColorRampShader.ColorRampItem(v, QColor(c), lab) for v, c, lab in zip(values, colors, labels)]
    color_shader = QgsColorRampShader(minimum, maximum)
    color_shader.setColorRampType(ramp_type)
    color_shader.setColorRampItemList(items)
    color_shader.setClip(spec["role"] in {"priority_result", "criterion"})
    raster_shader = QgsRasterShader()
    raster_shader.setRasterShaderFunction(color_shader)
    renderer = QgsSingleBandPseudoColorRenderer(layer.dataProvider(), 1, raster_shader)
    renderer.setClassificationMin(minimum)
    renderer.setClassificationMax(maximum)
    layer.setRenderer(renderer)
    layer.setOpacity(0.92 if spec["role"] == "priority_result" else 1.0)
    layer.triggerRepaint()
    _save_style(layer, style_path)


# Simple vector symbols per role: (symbol type, properties).
FILL, MARKER = "fill", "marker"
VECTOR_SYMBOLS = {
    "study_area_anchor": (FILL, {"color": "255,255,255,0", "outline_color": "230,126,34,255", "outline_width": "1.2", "outline_style": "dash"}),
    "boundary": (FILL, {"color": "255,255,255,0", "outline_color": "35,35,35,255", "outline_width": "0.8"}),
    "protected_polygons": (FILL, {"color": "46,204,113,90", "outline_color": "26,118,64,255", "outline_width": "0.7"}),
    "roads": (FILL, {"color": "255,255,255,0", "outline_color": "120,120,120,255", "outline_width": "0.4"}),
    "hydrologic_context": (FILL, {"color": "129,207,224,35", "outline_color": "34,112,141,235", "outline_width": "0.9"}),
    "flood_hazard_context": (FILL, {"color": "187,120,160,45", "outline_color": "120,32,105,235", "outline_width": "0.8"}),
    "event_huaico": (FILL, {"color": "0,255,255,35", "outline_color": "0,190,190,255", "outline_width": "0.9"}),
    "event_mudflow": (FILL, {"color": "255,234,0,35", "outline_color": "190,150,0,255", "outline_width": "0.9"}),
    "event_footprint": (FILL, {"color": "255,255,255,0", "outline_color": "0,255,255,255", "outline_width": "1.2"}),
    "original_hazard": (FILL, {"color": "118,190,200,75", "outline_color": "70,90,95,220", "outline_width": "0.7"}),
}
EVENT_CATEGORIES = (
    ("Confirmed affected location", "Confirmed affected locations", "30,136,229,240", "circle"),
    ("Evacuation location", "Evacuation locations", "123,31,162,240", "square"),
    ("Infrastructure damage", "Infrastructure damage locations", "211,47,47,240", "triangle"),
    ("Affected river/street reach reference", "Affected street / river reach references", "0,137,123,240", "diamond"),
)


def _label_settings(field: str, color, size: float, placement, expression: bool = False):
    from qgis.PyQt.QtGui import QColor, QFont
    from qgis.core import QgsPalLayerSettings, QgsTextBufferSettings, QgsTextFormat, QgsVectorLayerSimpleLabeling
    text_format = QgsTextFormat()
    text_format.setFont(QFont("Arial"))
    text_format.setColor(QColor(*color))
    text_format.setSize(size)
    buffer = QgsTextBufferSettings()
    buffer.setEnabled(True)
    buffer.setColor(QColor(255, 255, 255))
    buffer.setSize(1.0)
    text_format.setBuffer(buffer)
    settings = QgsPalLayerSettings()
    settings.fieldName = field
    settings.isExpression = expression
    settings.placement = placement
    settings.setFormat(text_format)
    return QgsVectorLayerSimpleLabeling(settings)


def apply_vector_style(layer, spec: dict, style_path: Path) -> None:
    from qgis.core import (Qgis, QgsCategorizedSymbolRenderer, QgsFillSymbol, QgsMarkerSymbol,
                           QgsRendererCategory, QgsSingleSymbolRenderer)
    role = spec["role"]
    polygon = layer.geometryType() == 2
    symbol = None
    if role in VECTOR_SYMBOLS:
        kind, props = VECTOR_SYMBOLS[role]
        symbol = (QgsFillSymbol if kind == FILL else QgsMarkerSymbol).createSimple(props)
    elif role == "infrastructure_context" and polygon:
        symbol = QgsMarkerSymbol.createSimple({"name": "square", "color": "214,69,129,225", "outline_color": "255,255,255,255", "size": "2.8"})
    elif role == "mining_context_overlay" and polygon:
        symbol = QgsFillSymbol.createSimple({"color": "230,126,34,40", "outline_color": "180,80,15,230", "outline_width": "0.7"})
    elif role == "mining_context_overlay":
        symbol = QgsMarkerSymbol.createSimple({"name": "diamond", "color": "211,84,0,230", "outline_color": "255,255,255,255", "size": "3.0"})
    elif role == "historical_event_location_evidence":
        categories = [QgsRendererCategory(value, QgsMarkerSymbol.createSimple(
            {"name": shape, "color": color, "outline_color": "255,255,255,255", "outline_width": "0.6", "size": "4.0"}), label)
            for value, label, color, shape in EVENT_CATEGORIES]
        layer.setRenderer(QgsCategorizedSymbolRenderer("evidence_group", categories))
        layer.setLabeling(_label_settings("location_name", (40, 40, 40), 8.5, Qgis.LabelPlacement.AroundPoint))
        layer.setLabelsEnabled(True)
    else:
        symbol = QgsMarkerSymbol.createSimple({"name": "triangle", "color": "31,120,180,235", "outline_color": "255,255,255,255", "size": "3.2"})
    if symbol is not None:
        layer.setRenderer(QgsSingleSymbolRenderer(symbol))
    if role == "study_area_anchor":
        layer.setLabeling(_label_settings("'Original project focus extent'", (166, 78, 0), 9.5,
                                          Qgis.LabelPlacement.OverPoint, expression=True))
        layer.setLabelsEnabled(True)
    layer.triggerRepaint()
    _save_style(layer, style_path)


def _save_style(layer, style_path: Path) -> None:
    style_path.parent.mkdir(parents=True, exist_ok=True)
    message, success = layer.saveNamedStyle(str(style_path))
    if not success:
        raise RuntimeError(f"could not save style {style_path}: {message}")


def load_layer(p: Package, spec: dict):
    from qgis.core import QgsRasterLayer, QgsVectorLayer
    source = p.root / spec["path"]
    if not source.exists():
        raise FileNotFoundError(f"missing required {p.site} layer: {source}")
    if spec["kind"] == "raster":
        layer = QgsRasterLayer(str(source), spec["name"])
    else:
        uri = f"{source}|layername={spec['layer_name']}" if spec["layer_name"] else str(source)
        layer = QgsVectorLayer(uri, spec["name"], "ogr")
    if not layer.isValid():
        raise RuntimeError(f"QGIS could not load {p.site}/{spec['key']}: {source}")
    for key in ("role", "claim_level", "unit"):
        layer.setCustomProperty(f"ifpm/{key}", spec[key])
    layer.setCustomProperty("ifpm/site", p.site)
    if spec["notes"]:
        layer.serverProperties().setAbstract(spec["notes"])
    return layer


def add_site_to_project(p: Package, project, parent_group, rows: list[dict]):
    groups = {}
    for group_name in dict.fromkeys(layer["group"] for layer in p.layers):
        group = parent_group.addGroup(group_name)
        group.setExpanded(group_name.startswith("1."))
        groups[group_name] = group
    priority_extent = None
    for spec in p.layers:
        layer = load_layer(p, spec)
        project.addMapLayer(layer, False)
        groups[spec["group"]].addLayer(layer).setItemVisibilityChecked(spec["visible"])
        style_path = p.style_dir / f"{p.site}_{spec['key']}.qml"
        (apply_raster_style if spec["kind"] == "raster" else apply_vector_style)(layer, spec, style_path)
        if spec["role"] == "priority_result":
            priority_extent = layer.extent()
        rows.append({
            "site": p.site, "layer_key": spec["key"], "display_name": spec["name"], "group": spec["group"],
            "role": spec["role"], "source_path": spec["path"], "source_type": spec["kind"],
            "provider_crs": layer.crs().authid(), "unit": spec["unit"],
            "visible_by_default": str(spec["visible"]).lower(), "claim_level": spec["claim_level"],
            "style_path": str(style_path.relative_to(p.out_dir)), "load_status": "valid", "notes": spec["notes"],
        })
    return priority_extent


def configure_project(project, title: str, crs_authid: str, output_path: Path) -> None:
    from qgis.core import Qgis, QgsCoordinateReferenceSystem
    project.clear()
    project.setTitle(title)
    project.setFileName(str(output_path))
    project.setFilePathStorage(Qgis.FilePathType.Relative)
    project.setCrs(QgsCoordinateReferenceSystem(crs_authid))
    project.setCustomVariables({
        "ifpm_status": "prototype map; not a validated flood-risk result",
        "ifpm_weighting": "current five-criterion weights; no pairwise matrix or consistency ratio supplied",
        "ifpm_workspace": "IFPM",
    })
    project.writeEntry("Paths", "Absolute", False)
    for part in ("Red", "Green", "Blue"):
        project.writeEntry("Gui", f"CanvasColor{part}Part", 248)


def set_default_extent(project, extent, crs_authid: str) -> None:
    from qgis.core import QgsCoordinateReferenceSystem, QgsReferencedRectangle
    if extent is None or extent.isNull():
        raise RuntimeError("priority layer has no valid extent")
    referenced = QgsReferencedRectangle(extent, QgsCoordinateReferenceSystem(crs_authid))
    project.viewSettings().setPresetFullExtent(referenced)
    project.viewSettings().setDefaultViewExtent(referenced)


RENDER_ORDER = {"study_area_anchor": 0, "boundary": 1, "event_huaico": 2, "event_mudflow": 2,
                "event_footprint": 2, "evidence_points": 2, "original_hazard": 2,
                "mining_context_overlay": 2, "roads": 3, "protected_polygons": 4,
                "priority_result": 5, "input_factor": 6, "criterion": 7}


def set_render_order(project) -> None:
    layers = sorted(project.mapLayers().values(), key=lambda layer: (
        RENDER_ORDER.get(layer.customProperty("ifpm/role"), 99), layer.name(), layer.source()))
    root = project.layerTreeRoot()
    root.setHasCustomLayerOrder(True)
    root.setCustomLayerOrder(layers)


def _read_qml_ramp(path: Path) -> dict:
    shader = ElementTree.fromstring(path.read_bytes()).find(".//colorrampshader")
    if shader is None:
        raise RuntimeError(f"missing color ramp shader in {path}")
    items = shader.findall("item")
    return {
        "type": shader.attrib.get("colorRampType", ""), "clip": shader.attrib.get("clip", ""),
        "values": tuple(float(item.attrib["value"]) for item in items),
        "labels": tuple(item.attrib.get("label", "") for item in items),
        "colors": tuple(item.attrib["color"].lower() for item in items),
    }


# Field-editing elements that make portable XML depend on the provider; removed for stable output.
EDIT_TAGS = {"aliases", "attributetableconfig", "conditionalstyles", "constraintExpressions",
             "constraints", "defaults", "duplicatePolicies", "editable", "expressionfields",
             "fieldConfiguration", "labelOnTop", "reuseLastValue", "splitPolicies", "storedexpressions"}
DOCTYPE = "<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>\n"


def _rewrite_project_for_portable_export(p: Package, source_project: Path, target_project: Path, rows: list[dict]) -> None:
    replacements: dict[str, str] = {}
    vector_sources: set[str] = set()
    for row in rows:
        old = os.path.relpath(p.root / row["source_path"], p.out_dir).replace(os.sep, "/")
        suffix = ".gpkg" if row["source_type"] == "vector" else Path(row["source_path"]).suffix.lower()
        new = f"layers/{p.site}/{row['layer_key']}/{p.site}_{row['layer_key']}{suffix}"
        layer_name = p.layer_names[row["layer_key"]]
        if layer_name:
            old = f"{old}|layername={layer_name}"
            new = f"{new}|layername={p.site}_{row['layer_key']}"
            vector_sources.add(old)
        replacements[old] = new

    with zipfile.ZipFile(source_project) as archive:
        qgs_names = [name for name in archive.namelist() if name.endswith(".qgs")]
        if len(qgs_names) != 1:
            raise RuntimeError(f"{source_project} must contain exactly one QGS document")
        qgs_name = qgs_names[0]
        root = ElementTree.fromstring(archive.read(qgs_name))
    for attribute in ("saveUser", "saveUserFull", "saveDateTime"):
        root.attrib.pop(attribute, None)

    layer_ids: dict[str, str] = {}
    for index, map_layer in enumerate(root.findall(".//maplayer")):
        old_id = map_layer.findtext("id")
        layer_name = map_layer.findtext("layername") or f"layer_{index}"
        data_source = map_layer.findtext("datasource") or ""
        if old_id:
            stable = uuid.uuid5(uuid.NAMESPACE_URL, f"ifpm:{source_project.name}:{data_source}:{layer_name}").hex[:16]
            layer_ids[old_id] = f"{re.sub(r'[^a-z0-9]+', '_', layer_name.lower()).strip('_')}_{stable}"
        if data_source in vector_sources:
            for parent in map_layer.iter():
                for child in list(parent):
                    if child.tag in EDIT_TAGS:
                        parent.remove(child)

    replaced = 0
    for element in root.iter():
        if element.attrib.get("source") in replacements:
            element.set("source", replacements[element.attrib["source"]])
            replaced += 1
        if element.tag == "datasource" and element.text in replacements:
            element.text = replacements[element.text]
            replaced += 1
        if element.tag in {"author", "creation"}:
            element.text = ""
    for dates in root.findall(".//dates"):
        dates.clear()
    for parent in root.iter():
        for child in list(parent):
            if child.tag in {"elevation", "main-annotation-layer"}:
                parent.remove(child)
    for settings in root.findall(".//individual-layer-settings"):
        settings[:] = sorted(settings, key=lambda child: child.attrib.get("id", ""))
    for project_layers in root.findall(".//projectlayers"):
        project_layers[:] = sorted(project_layers, key=lambda child: (
            child.findtext("datasource") or "", child.findtext("layername") or ""))
    for settings in root.findall(".//ProjectStyleSettings"):
        settings.set("projectStyleId", "")
        settings.set("iccProfileId", "")
    for element in root.iter():
        if element.text in layer_ids:
            element.text = layer_ids[element.text]
        for key, value in list(element.attrib.items()):
            if value in layer_ids:
                element.set(key, layer_ids[value])
    if replaced == 0:
        raise RuntimeError(f"no data sources were rewritten in {source_project.name}")

    counter = 0

    def stable_uuid(_match) -> str:
        nonlocal counter
        value = uuid.uuid5(uuid.NAMESPACE_URL, f"ifpm:{source_project.name}:symbol:{counter}")
        counter += 1
        return "{" + str(value) + "}"

    xml_text = re.sub(r"\{[0-9a-fA-F-]{36}\}", stable_uuid, ElementTree.tostring(root, encoding="unicode"))
    xml_bytes = (DOCTYPE + ElementTree.canonicalize(xml_data=xml_text, strip_text=True)).encode("utf-8")
    info = zipfile.ZipInfo(qgs_name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    with zipfile.ZipFile(target_project, "w") as target:
        target.writestr(info, xml_bytes)


def _normalize_portable_qml(path: Path) -> None:
    root = ElementTree.fromstring(path.read_bytes())
    for parent in root.iter():
        for child in list(parent):
            if child.tag in EDIT_TAGS | {"elevation"}:
                parent.remove(child)
    counter = 0

    def stable_id(_match) -> str:
        nonlocal counter
        value = uuid.uuid5(uuid.NAMESPACE_URL, f"ifpm:{path.name}:{counter}")
        counter += 1
        return f'id="{{{value}}}"'

    text = re.sub(r'id="\{[0-9a-fA-F-]{36}\}"', stable_id, ElementTree.tostring(root, encoding="unicode"))
    path.write_text(DOCTYPE + ElementTree.canonicalize(xml_data=text, strip_text=True), encoding="utf-8")


def build_portable_export(p: Package, rows: list[dict]) -> Path:
    temp_dir = p.portable_dir.parent / f".{p.portable_dir.name}.tmp"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True)
    for row in rows:
        source = p.root / row["source_path"]
        target_dir = temp_dir / "layers" / p.site / row["layer_key"]
        target_dir.mkdir(parents=True, exist_ok=True)
        if row["source_type"] == "vector":
            # One single-layer GPKG per vector, named <site>_<key>: no shapefile sidecars.
            from osgeo import gdal
            target = target_dir / f"{p.site}_{row['layer_key']}.gpkg"
            source_dataset = gdal.OpenEx(str(source), gdal.OF_VECTOR)
            if source_dataset is None:
                raise RuntimeError(f"GDAL could not open vector source {source}")
            options = gdal.VectorTranslateOptions(format="GPKG", layers=[p.layer_names[row["layer_key"]]],
                                                  layerName=f"{p.site}_{row['layer_key']}")
            result = gdal.VectorTranslate(str(target), source_dataset, options=options)
            source_dataset = None
            if result is None:
                raise RuntimeError(f"could not export portable vector layer {row['layer_key']}")
            result = None
            with sqlite3.connect(target) as connection:
                connection.execute("UPDATE gpkg_contents SET last_change = ?", ("1980-01-01T00:00:00.000Z",))
                connection.commit()
                connection.execute("VACUUM")
        else:
            target = target_dir / f"{p.site}_{row['layer_key']}{Path(row['source_path']).suffix.lower()}"
            shutil.copy2(source, target)
        row["portable_source_path"] = (Path("layers") / p.site / row["layer_key"] / target.name).as_posix()
        row["source_size_bytes"] = str(source.stat().st_size)
        row["source_sha256"] = sha256(source)
        row["portable_size_bytes"] = str(target.stat().st_size)
        row["portable_sha256"] = sha256(target)

    shutil.copytree(p.style_dir, temp_dir / "styles")
    for style_path in (temp_dir / "styles").glob("*.qml"):
        _normalize_portable_qml(style_path)
    _rewrite_project_for_portable_export(p, p.out_dir / p.project_name, temp_dir / p.project_name, rows)
    write_rows(temp_dir / "manifest.csv", rows, PORTABLE_MANIFEST_FIELDS)
    (temp_dir / "README.txt").write_text(p.spec["portable_readme"], encoding="utf-8")
    if p.portable_dir.exists():
        shutil.rmtree(p.portable_dir)
    temp_dir.replace(p.portable_dir)
    return p.portable_dir / p.project_name


def build_portable_zip(package_dir: Path, archive_path: Path) -> Path:
    """Deterministic, metadata-free ZIP of a portable package."""
    temp_archive = archive_path.with_name(f".{archive_path.name}.tmp")
    with zipfile.ZipFile(temp_archive, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source in sorted(path for path in package_dir.rglob("*") if path.is_file()):
            relative = source.relative_to(package_dir)
            if any(part.startswith(".") for part in relative.parts):
                continue
            info = zipfile.ZipInfo((Path(package_dir.name) / relative).as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, source.read_bytes())
    temp_archive.replace(archive_path)
    return archive_path


def refresh_index(index_root: Path, key: str, package_dir: Path) -> None:
    """Update this package's entry in <index_root>/package_index.json."""
    index_path = index_root / "package_index.json"
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else {}
    with (package_dir / "manifest.csv").open(newline="", encoding="utf-8") as stream:
        layer_count = len(list(csv.DictReader(stream)))
    projects = sorted(package_dir.glob("*.qgz"))
    archive = package_dir.with_suffix(".zip")
    if len(projects) != 1 or not archive.is_file():
        raise RuntimeError(f"incomplete package: {package_dir}")
    record = {"path": package_dir.relative_to(index_root).as_posix(), "project": projects[0].name,
              "layer_count": layer_count, "zip": archive.relative_to(index_root).as_posix(),
              "zip_sha256": sha256(archive)}
    if "claim_boundary" in index.get(key, {}):
        record["claim_boundary"] = index[key]["claim_boundary"]
    index[key] = record
    index_path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_rows(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row[field] for field in fields} for row in rows)


def build_projects(p: Package) -> tuple[list[dict], list[dict]]:
    from qgis.core import QgsProject
    p.style_dir.mkdir(parents=True, exist_ok=True)
    expected = {f"{p.site}_{layer['key']}.qml" for layer in p.layers}
    for stale in p.style_dir.glob("*.qml"):
        if stale.name not in expected:
            stale.unlink()
    rows: list[dict] = []
    readback: list[dict] = []
    project = QgsProject.instance()
    try:
        output_path = p.out_dir / p.project_name
        configure_project(project, f"IFPM - {p.spec['name']}", p.spec["project_crs"], output_path)
        site_group = project.layerTreeRoot().addGroup(p.spec["name"])
        extent = add_site_to_project(p, project, site_group, rows)
        set_default_extent(project, extent, p.spec["project_crs"])
        set_render_order(project)
        if not project.write(str(output_path)):
            raise RuntimeError(f"QGIS failed to write {output_path}")
        for path in (output_path, build_portable_export(p, rows)):
            project.clear()
            read_success = bool(project.read(str(path)))
            invalid = [layer.name() for layer in project.mapLayers().values() if not layer.isValid()]
            count = len(project.mapLayers())
            if not read_success or invalid or count != len(p.layers):
                raise RuntimeError(f"QGIS read-back failed for {path.name}: read={read_success}, "
                                   f"invalid={invalid}, layers={count}, expected={len(p.layers)}")
            view = project.viewSettings().defaultViewExtent()
            readback.append({
                "project": path.name,
                "package_type": "portable" if p.portable_dir in path.parents else "workspace_linked",
                "read_success": read_success, "layer_count": count, "expected_layer_count": len(p.layers),
                "invalid_layers": invalid, "project_crs": project.crs().authid(),
                "default_extent": [view.xMinimum(), view.yMinimum(), view.xMaximum(), view.yMaximum()],
            })
    finally:
        project.clear()
    return rows, readback


def _single_qgs(project_path: Path) -> tuple[str, bytes]:
    with zipfile.ZipFile(project_path) as archive:
        names = [name for name in archive.namelist() if name.endswith(".qgs")]
        if len(names) != 1:
            raise RuntimeError(f"{project_path.name} contains {len(names)} QGS documents")
        return names[0], archive.read(names[0])


def validate_package(p: Package, readback: list[dict]) -> dict:
    project_path = p.out_dir / p.project_name
    qgs_name, xml_bytes = _single_qgs(project_path)
    ElementTree.fromstring(xml_bytes)
    if str(p.root) in xml_bytes.decode("utf-8"):
        raise RuntimeError(f"absolute workspace path found in {project_path.name}")
    checks = [{"project": project_path.name, "qgs_document": qgs_name, "xml_valid": True,
               "absolute_path_free": True, "size_bytes": project_path.stat().st_size}]

    portable_project = p.portable_dir / p.project_name
    qgs_name, xml_bytes = _single_qgs(portable_project)
    root = ElementTree.fromstring(xml_bytes)
    sources = [e.attrib["source"] for e in root.iter()
               if "source" in e.attrib and not e.attrib["source"].startswith("attachment://")]
    sources += [e.text for e in root.iter("datasource") if e.text]
    external = [s for s in sources if s.startswith(("/", "../", "file://")) or ":\\" in s]
    if external:
        raise RuntimeError(f"external data sources found in portable {portable_project.name}: {external}")
    portable_checks = [{"project": portable_project.name, "qgs_document": qgs_name, "package_local_sources": True,
                        "source_reference_count": len(sources), "size_bytes": portable_project.stat().st_size}]

    with p.manifest.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    missing_sources = [r["source_path"] for r in rows if not (p.root / r["source_path"]).exists()]
    missing_styles = [r["style_path"] for r in rows if not (p.out_dir / r["style_path"]).exists()]
    missing_portable = [r["portable_source_path"] for r in rows if not (p.portable_dir / r["portable_source_path"]).exists()]
    if missing_sources or missing_styles or missing_portable:
        raise RuntimeError(f"missing sources={missing_sources}; missing styles={missing_styles}; "
                           f"missing portable sources={missing_portable}")
    checksum_errors = []
    for r in rows:
        if sha256(p.root / r["source_path"]) != r["source_sha256"]:
            checksum_errors.append(f"source checksum changed: {r['site']}/{r['layer_key']}")
        if sha256(p.portable_dir / r["portable_source_path"]) != r["portable_sha256"]:
            checksum_errors.append(f"portable checksum mismatch: {r['site']}/{r['layer_key']}")
    expected_files = {p.project_name, "README.txt", "manifest.csv", "validation.json",
                      *(r["portable_source_path"] for r in rows),
                      *(f"styles/{Path(r['style_path']).name}" for r in rows)}
    actual_files = {path.relative_to(p.portable_dir).as_posix() for path in p.portable_dir.rglob("*") if path.is_file()}
    unexpected = sorted(actual_files - expected_files)
    if checksum_errors or unexpected:
        raise RuntimeError(f"checksum errors={checksum_errors}; unexpected portable files={unexpected}")

    semantic_errors = []
    roles = [r["role"] for r in rows]
    if roles.count("priority_result") != 1:
        semantic_errors.append("expected exactly one priority_result layer")
    if roles.count("criterion") != 5:
        semantic_errors.append("expected exactly five criterion layers")
    units = {r["layer_key"]: r["unit"] for r in rows}
    if units.get("distance_drainage") != "m":
        semantic_errors.append("drainage-distance unit is not metres")
    if units.get("twi") != "TWI":
        semantic_errors.append("TWI unit is not TWI")
    palettes = {"priority": tuple(PRIORITY_COLORS), **{k: tuple(v) for k, v in CRITERIA_COLORS.items()}}
    for key, colors in palettes.items():
        for label, style_root in (("workspace", p.style_dir), ("portable", p.portable_dir / "styles")):
            ramp = _read_qml_ramp(style_root / f"{p.site}_{key}.qml")
            if ramp["type"] != "DISCRETE":
                semantic_errors.append(f"{label}/{key} color ramp is not discrete")
            if ramp["clip"] != "1":
                semantic_errors.append(f"{label}/{key} color ramp is not clipped")
            if ramp["values"] != STANDARD_CLASS_UPPER_BOUNDS:
                semantic_errors.append(f"{label}/{key} thresholds differ from 0.2 equal intervals")
            if ramp["labels"] != STANDARD_CLASS_LABELS:
                semantic_errors.append(f"{label}/{key} class labels differ")
            if ramp["colors"] != colors:
                semantic_errors.append(f"{label}/{key} color codes differ")
    if semantic_errors:
        raise RuntimeError(f"semantic validation failed: {semantic_errors}")

    from osgeo import gdal
    from qgis.core import Qgis, QgsProjUtils
    result = {
        "qgis_version": Qgis.QGIS_VERSION,
        "gdal_version": gdal.VersionInfo("RELEASE_NAME"),
        "proj_version": f"{QgsProjUtils.projVersionMajor()}.{QgsProjUtils.projVersionMinor()}",
        "generator_sha256": p.spec["generator_sha256"],
        "config_sha256": p.spec["config_sha256"],
        "projects": checks,
        "portable_projects": portable_checks,
        "manifest_layer_count": len(rows),
        "style_count": len(list(p.style_dir.glob("*.qml"))),
        "qgis_readback": readback,
        "missing_sources": missing_sources,
        "missing_styles": missing_styles,
        "missing_portable_sources": missing_portable,
        "checksum_errors": checksum_errors,
        "unexpected_portable_files": unexpected,
        "semantic_errors": semantic_errors,
        "status": "package_integrity_valid",
    }
    text = json.dumps(result, indent=2) + "\n"
    (p.out_dir / "validation.json").write_text(text, encoding="utf-8")
    (p.portable_dir / "validation.json").write_text(text, encoding="utf-8")
    return result


def sample_raster(path: Path, boundary_path: Path, boundary_layer: str) -> dict:
    """GDAL statistics plus valid-cell shares on a <=512x512 overview, inside the boundary."""
    import numpy as np
    from osgeo import gdal
    gdal.UseExceptions()
    dataset = gdal.Open(str(path))
    band = dataset.GetRasterBand(1)
    stats = band.GetStatistics(False, True)
    width, height = min(dataset.RasterXSize, 512), min(dataset.RasterYSize, 512)
    values = band.ReadAsArray(buf_xsize=width, buf_ysize=height)
    nodata = band.GetNoDataValue()
    finite = np.isfinite(values)
    if nodata is not None:
        finite &= ~np.isnan(values) if math.isnan(nodata) else ~np.isclose(values, nodata)
    valid = values[finite]
    t = dataset.GetGeoTransform()
    bounds = [t[0], t[3] + dataset.RasterYSize * t[5], t[0] + dataset.RasterXSize * t[1], t[3]]
    projected = gdal.VectorTranslate("", str(boundary_path), format="MEM",
                                     dstSRS=dataset.GetProjection(), layers=[boundary_layer])
    mask = gdal.Rasterize("", projected, format="MEM", width=width, height=height, outputBounds=bounds,
                          outputSRS=dataset.GetProjection(), layers=[projected.GetLayer(0).GetName()],
                          burnValues=[1], outputType=gdal.GDT_Byte)
    inside = mask.GetRasterBand(1).ReadAsArray() > 0
    return {
        "minimum": float(stats[0]), "maximum": float(stats[1]), "mean": float(stats[2]), "stddev": float(stats[3]),
        "sampled_valid_pixels": int(valid.size),
        "sampled_valid_percent": 100.0 * int(finite.sum()) / int(finite.size),
        "sampled_unique_values": int(np.unique(valid).size) if valid.size else 0,
        "valid_within_boundary_percent": 100.0 * int((finite & inside).sum()) / int(inside.sum()) if inside.sum() else 0.0,
    }


def render_preview(project_path: Path, title: str, output_path: Path) -> None:
    from qgis.PyQt.QtCore import QSize
    from qgis.PyQt.QtGui import QColor, QPainter
    from qgis.core import QgsMapRendererParallelJob, QgsMapSettings, QgsProject, QgsRectangle
    project = QgsProject.instance()
    if not project.read(str(project_path)):
        raise RuntimeError(f"could not read {project_path}")
    target = next(layer for layer in project.mapLayers().values()
                  if layer.customProperty("ifpm/role") == "priority_result")
    extent = QgsRectangle(target.extent())
    extent.scale(1.04)
    settings = QgsMapSettings()
    settings.setDestinationCrs(project.crs())
    settings.setTransformContext(project.transformContext())
    settings.setExtent(extent)
    settings.setOutputSize(QSize(1000, 760))
    settings.setOutputDpi(120)
    settings.setBackgroundColor(QColor("white"))
    settings.setLayers([target])
    job = QgsMapRendererParallelJob(settings)
    job.start()
    job.waitForFinished()
    image = job.renderedImage()
    painter = QPainter(image)
    painter.setPen(QColor("#222222"))
    painter.drawText(18, 28, title)
    painter.end()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(str(output_path), "PNG")


def run_layer_qa(p: Package) -> None:
    """Coverage of every raster inside the boundary plus a priority preview (layer_qa/)."""
    qa = p.spec["qa"]
    qa_dir = p.out_dir / "layer_qa"
    rows = []
    with p.manifest.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["source_type"] != "raster":
                rows.append({**row, "qa_status": "vector_skipped"})
                continue
            stats = sample_raster(p.root / row["source_path"], p.root / qa["boundary"], qa["boundary_layer"])
            rows.append({**row, **stats, "qa_status": "ok"})
            if row["role"] == "priority_result":
                render_preview(p.out_dir / p.project_name, qa["preview_title"], qa_dir / "previews" / "priority_preview.png")
    coarse = qa.get("coarse_coverage_floor_percent", {})
    floor = lambda key: coarse.get(key, qa["coverage_floor_percent"])  # noqa: E731
    failed = [r for r in rows if r["qa_status"] == "ok" and float(r["valid_within_boundary_percent"]) < floor(r["layer_key"])]
    for r in rows:
        if r["qa_status"] == "ok" and r["layer_key"] in coarse:
            r["coverage_note"] = f"coarse source; floor {coarse[r['layer_key']]}% (documented NoData preserved)"
    with (qa_dir / "layer_qa.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=sorted({k for r in rows for k in r}))
        writer.writeheader()
        writer.writerows(rows)
    result = {"status": "fail" if failed else "pass", "pass_count": len(rows) - len(failed),
              "fail_count": len(failed), "layers": rows}
    (qa_dir / "layer_qa.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if failed:
        raise RuntimeError(f"layer QA failed for {[r['layer_key'] for r in failed]}")
    print(f"layer QA passed for {len(rows)} layers")


def _qgis_main(spec_path: str) -> int:
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    p = Package(spec)
    from qgis.core import QgsApplication
    # One QGIS session per process: a second initQgis after exitQgis crashes.
    QgsApplication.setPrefixPath(os.environ["QGIS_PREFIX_PATH"], True)
    app = QgsApplication([], False)
    app.initQgis()
    try:
        p.out_dir.mkdir(parents=True, exist_ok=True)
        rows, readback = build_projects(p)
        write_rows(p.manifest, rows, MANIFEST_FIELDS)
        (p.out_dir / "README.txt").write_text(spec["readme"], encoding="utf-8")
        result = validate_package(p, readback)
        build_portable_zip(p.portable_dir, p.portable_dir.with_suffix(".zip"))
        refresh_index(Path(spec["index_root"]), spec["index_key"], p.portable_dir)
        if spec.get("qa"):
            run_layer_qa(p)
    finally:
        app.exitQgis()
    print(f"wrote {p.site} {spec['package']} with {result['manifest_layer_count']} layers to {p.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_qgis_main(sys.argv[1]))
