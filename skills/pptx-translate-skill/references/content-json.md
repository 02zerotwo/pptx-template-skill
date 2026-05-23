# deck_content.json Translation Contract

`deck_content.json` 是 AI 默认生成的文件。用于 PPTX 翻译时，它表达要复用哪些源 slide，以及每个可翻译槽位的译文。

## 1. Top-Level Fields

| Field | Type | Notes |
|---|---|---|
| `schema_version` | string | 当前为 `1.0` |
| `title` | string | 翻译版演示文稿标题 |
| `slides` | array | 输出页列表 |

---

## 2. Slide Content

```json
{
  "template_slide": "template-slide-001",
  "content": {
    "cover_title": {
      "content": "2026 Market Growth Strategy"
    },
    "hero_image": {
      "src": "assets/generated/hero.png",
      "alt": "Hero image for a market strategy presentation"
    }
  }
}
```

| Field | Notes |
|---|---|
| `template_slide` | 必须来自 `template_manifest.json` |
| `content` | key 必须是该模板页存在的 `slot_id` |

翻译场景通常保持 slide 数量和顺序不变：每个源 slide 对应一个输出 slide，`template_slide` 使用 manifest 中的对应 slide id。

---

## 3. Slot Value Types

| Slot Type | Allowed Fields |
|---|---|
| `text` | `content`、`paragraphs` |
| `image` | `src`、`alt` |
| `table` | `cells` |
| `chart` | `categories`、`series` |
| `shape` | `fill`、`line`、`opacity`、`geometry` |

`text.paragraphs` 可使用字符串、`{"text": "...", "bullet": true}`，或 `{"runs": [{"text": "...", "bold": true}]}`。

`table.cells` 是二维数组，只替换模板中已经存在的行列。翻译文本，保留数字、单位、日期和空单元格。

`chart.series` 示例：

```json
{
  "categories": ["2026", "2027"],
  "series": [
    {"name": "Adoption", "values": [30, 70]}
  ]
}
```

图表翻译时只翻译 `categories` 中的文本标签和 `series.name`；`series.values` 必须保持数值不变。

`shape` 颜色使用十六进制 RGB，例如 `"#00AAFF"`；`opacity` 为 `0` 到 `1`。

**Hard rule**: 字段必须在 slot 的 `editable_fields` 中。

**Hard rule**: 图片 `src` 必须是 workspace 内相对路径。

**Hard rule**: 文本超过 `capacity.max_chars` 时保留译文，构建流程会自动启用文本溢出字号缩小。严重拥挤时优先压缩译文表达，不要自行移动或拉伸文本框。

**Hard rule**: 不要在 JSON 中表达 P4 对象编辑，例如 SmartArt 内部结构、动画、视频、音频、备注页或 OLE。
