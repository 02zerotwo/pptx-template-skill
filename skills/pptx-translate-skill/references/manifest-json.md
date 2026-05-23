# template_manifest.json Contract

`template_manifest.json` 是模板分析器输出给 AI 的模板结构摘要。它不是 PPTX 的完整镜像，只描述可编辑槽位、容量、绑定位置和保留对象。

## 1. Top-Level Fields

| Field | Type | Notes |
|---|---|---|
| `schema_version` | string | 当前为 `1.0` |
| `template_id` | string | 模板标识，默认来自文件名 |
| `source` | object | 原始模板文件名和格式 |
| `presentation` | object | 页面尺寸，单位 EMU |
| `slides` | array | 模板页列表 |
| `assets` | object | 静态资源摘要 |
| `warnings` | array | 分析警告 |

---

## 2. Slide Fields

| Field | Type | Notes |
|---|---|---|
| `slide_id` | string | AI 在 `deck_content.json` 中引用的模板页 id |
| `source_part` | string | OOXML slide part |
| `role` | string | `cover`、`content`、`closing` |
| `index` | number | 模板原始页序 |
| `slots` | array | 可编辑槽位 |
| `preserved_objects` | array | 保留对象摘要 |

---

## 3. Slot Fields

| Field | Type | Notes |
|---|---|---|
| `slot_id` | string | AI 填写内容时使用的字段名 |
| `type` | string | `text`、`image`、`table`、`chart`、`shape` |
| `required` | boolean | 是否必填 |
| `editable_fields` | array | AI 允许填写的字段 |
| `capacity` | object | 字数、行数、比例等限制；翻译超限时用于计算自动缩小字号 |
| `binding` | object | 导出器定位 OOXML 对象的绑定信息 |
| `source` | object | 识别来源和当前内容摘要 |

---

## 4. Slot Detection

| Priority | Strategy |
|---|---|
| 1 | 显式 `{{slot_id}}` 占位符 |
| 2 | PowerPoint placeholder 类型 |
| 3 | shape name / alt text |
| 4 | 简单启发式 |

推荐模板作者显式使用 `{{slot_id}}`，这样生成最稳定。

---

## 5. Current Slot Types

| Type | Source Summary |
|---|---|
| `text` | `current_text`、`paragraphs`、placeholder 信息；翻译后可自动 autofit |
| `image` | 当前 media target、图片描述 |
| `table` | `cells` 二维数组、行列容量 |
| `chart` | `categories`、`series`，来自 chart XML cache |
| `shape` | `fill`、`line`、`geometry`，面向简单形状和图标式矢量对象 |
