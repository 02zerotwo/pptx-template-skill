# OOXML Boundaries

本文定义第一阶段可编辑对象、保留对象和拒绝导出的边界。

## 1. Editable Objects

| Object | Editable Fields | Notes |
|---|---|---|
| 文本槽位 | `content`、`paragraphs` | 保留文本框位置、尺寸，尽量复用原段落/run 样式 |
| 图片槽位 | `src`、`alt` | 保留位置、尺寸、裁剪和边框；`alt` 写入图片描述 |
| 表格槽位 | `cells` | 只替换已有行列中的文本 |
| 图表槽位 | `categories`、`series` | 更新 chart XML cache；嵌入 workbook 不保证同步 |
| 形状/矢量槽位 | `fill`、`line`、`opacity`、`geometry` | 面向简单形状和图标式 preset geometry |

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
| 文本超过硬容量 | 停止导出 |
| OOXML binding 失效 | 停止导出，要求重新分析模板 |
| broken relationship | 停止写出最终 PPTX |
