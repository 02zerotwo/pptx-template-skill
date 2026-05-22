# patch_plan.json Contract

`patch_plan.json` 是长期公开稳定格式。它由 `compile_patch.py` 根据合法 `deck_content.json` 生成，描述导出器要执行的受控 OOXML 操作。

## 1. Top-Level Fields

| Field | Type | Notes |
|---|---|---|
| `schema_version` | string | 当前为 `1.0` |
| `title` | string | 输出标题 |
| `operations` | array | 按顺序执行的 patch 操作 |

---

## 2. Operation Types

| Type | Purpose |
|---|---|
| `copy_slide` | 复制模板 slide 到输出 slide |
| `replace_text` | 替换指定 shape 的文本 |
| `replace_image` | 替换指定 relationship 的图片目标 |
| `replace_table_cells` | 替换指定表格的单元格文本 |
| `replace_chart_data` | 替换指定图表的 XML cache 数据 |
| `replace_shape_style` | 替换简单形状/矢量对象样式 |

---

## 3. copy_slide

```json
{
  "type": "copy_slide",
  "source_slide": "ppt/slides/slide1.xml",
  "target_slide": "ppt/slides/slide1.xml",
  "new_slide_id": 256,
  "presentation_rel_id": "rId1",
  "template_slide": "template-slide-001"
}
```

---

## 4. replace_text

```json
{
  "type": "replace_text",
  "target_slide": "ppt/slides/slide1.xml",
  "binding": {
    "shape_id": "2",
    "xpath": ".//p:sp[p:nvSpPr/p:cNvPr/@id='2']/p:txBody"
  },
  "slot_id": "cover_title",
  "content": "2026 年市场增长策略"
}
```

---

## 5. replace_image

```json
{
  "type": "replace_image",
  "target_slide": "ppt/slides/slide1.xml",
  "binding": {
    "shape_id": "3",
    "rel_id": "rId2"
  },
  "slot_id": "hero_image",
  "src": "assets/generated/hero.png",
  "alt": "market strategy hero image"
}
```

`src` 和 `alt` 可单独出现：只写 `alt` 时仅更新图片描述。

---

## 6. replace_table_cells

```json
{
  "type": "replace_table_cells",
  "target_slide": "ppt/slides/slide1.xml",
  "binding": {"shape_id": "5"},
  "slot_id": "sales_table",
  "cells": [["Market", "Share"], ["AIGC", "42"]]
}
```

---

## 7. replace_chart_data

```json
{
  "type": "replace_chart_data",
  "target_slide": "ppt/slides/slide1.xml",
  "binding": {
    "shape_id": "6",
    "chart_part": "ppt/charts/chart1.xml"
  },
  "slot_id": "growth_chart",
  "categories": ["2026", "2027"],
  "series": [{"name": "Adoption", "values": [30, 70]}]
}
```

---

## 8. replace_shape_style

```json
{
  "type": "replace_shape_style",
  "target_slide": "ppt/slides/slide1.xml",
  "binding": {"shape_id": "7"},
  "slot_id": "brand_shape",
  "fill": "#00AAFF",
  "line": "#111111",
  "geometry": "roundRect"
}
```

**Hard rule**: Even though this format is public, AI should not handwrite freeform XML operations. Generate `deck_content.json` first, then run `compile_patch.py`.
