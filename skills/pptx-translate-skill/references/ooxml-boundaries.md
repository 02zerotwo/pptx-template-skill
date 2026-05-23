# OOXML Boundaries

本文定义 PPTX 翻译流程中的可翻译对象、保留对象和拒绝导出的边界。

## 1. Editable Objects

| Object | Editable Fields | Notes |
|---|---|---|
| 文本槽位 | `content`、`paragraphs` | 翻译可见文本；保留文本框位置、尺寸，超长译文自动启用字号缩小 |
| 图片槽位 | `alt` | 翻译图片描述；默认不替换 `src` |
| 表格槽位 | `cells` | 翻译已有行列中的文本；保留数值和行列数量 |
| 图表槽位 | `categories`、`series` | 翻译 category 标签和 series 名称；保留数值 |
| 形状/矢量槽位 | `fill`、`line`、`opacity`、`geometry` | 非翻译内容；仅在用户明确要求样式调整时使用 |

---

## 2. Summary-Only Objects

| Object | Strategy |
|---|---|
| 嵌入图表 workbook | 当前不保证同步编辑 |
| 复杂自定义矢量路径 | 当前只保留或做颜色级编辑 |

---

## 3. Preserved Objects

| Object | Strategy |
|---|---|
| 母版、版式、主题 | 原样保留 |
| 动画、切换 | 原样保留 |
| SmartArt | 原样保留 |
| 备注页、评论 | 原样保留 |
| OLE / embedded objects | 原样保留或按安全策略拒绝 |
| 宏 / VBA | 默认拒绝 `.pptm`，启用后只保留不编辑 |

P4 明确不做：SmartArt 内容编辑、动画编辑、备注页编辑、视频/音频编辑、任意 OLE 内容编辑。

---

## 4. Refusal Conditions

| Error | Behavior |
|---|---|
| 必填槽位缺失 | 停止导出 |
| 未知槽位 | 停止导出 |
| 越权字段 | 停止导出 |
| 资源路径不存在 | 停止导出 |
| 资源路径逃逸 workspace | 停止导出 |
| 文本超过容量 | 继续导出并启用字号缩小；报告 warning |
| OOXML binding 失效 | 停止导出，要求重新分析模板 |
| broken relationship | 停止写出最终 PPTX |
