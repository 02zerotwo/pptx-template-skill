"""Apply chart cache replacement patches."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from pptx_json.package.opc import write_xml
from pptx_json.xmlns import NS, qn


def _reset_cache(cache, values: list, *, numeric: bool = False) -> None:
    for child in list(cache):
        if child.tag in {qn("c", "ptCount"), qn("c", "pt")}:
            cache.remove(child)
    ET.SubElement(cache, qn("c", "ptCount"), {"val": str(len(values))})
    for index, value in enumerate(values):
        point = ET.SubElement(cache, qn("c", "pt"), {"idx": str(index)})
        node = ET.SubElement(point, qn("c", "v"))
        node.text = str(value)


def _cache(parent, path: str):
    return parent.find(path, NS) if parent is not None else None


def apply_chart_patch(package_dir: Path, operation: dict) -> None:
    chart_part = operation.get("binding", {}).get("chart_part")
    if not chart_part:
        return
    chart_path = package_dir / chart_part
    tree = ET.parse(chart_path)
    root = tree.getroot()
    categories = operation.get("categories", [])
    series_values = operation.get("series", [])
    series_nodes = root.findall(".//c:ser", NS)
    for index, series_node in enumerate(series_nodes):
        if categories:
            cat_cache = _cache(series_node, "c:cat/c:strRef/c:strCache")
            if cat_cache is not None:
                _reset_cache(cat_cache, categories)
        if index >= len(series_values):
            continue
        series = series_values[index] if isinstance(series_values[index], dict) else {}
        name = series.get("name")
        if name is not None:
            tx_cache = _cache(series_node, "c:tx/c:strRef/c:strCache")
            if tx_cache is not None:
                _reset_cache(tx_cache, [name])
        values = series.get("values", [])
        val_cache = _cache(series_node, "c:val/c:numRef/c:numCache")
        if val_cache is not None:
            _reset_cache(val_cache, values, numeric=True)
    write_xml(chart_path, tree)
