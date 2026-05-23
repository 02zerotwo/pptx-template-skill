# PPTX Translation Workflow

本文定义 AI 基于已有 PPTX 生成翻译版 PPTX 的实际流程。目标是翻译可见内容，同时保持原 PPTX 的版式、主题、媒体关系和 OOXML 包结构稳定。

## 1. 使用场景

当用户提供 PPTX，并要求“翻译成英文/中文/日文/...”或“保留排版翻译整份 PPT”时，使用本 skill。不要进入从零生成 PPTX、SVG 重绘、截图覆盖或全量 OOXML 自由编辑流程。

---

## 2. 系统要求

| 项目 | 要求 |
| --- | --- |
| Python | >= 3.10 |
| 操作系统 | macOS / Linux / Windows (WSL) |
| 包管理工具 | 不需要 |

引擎仅使用 Python 标准库，无第三方运行依赖。

---

## 3. AI 快速流程

命令由 agent 调用内置 `scripts/pptx_json_cli.py`。`<skill-root>` 指包含本 `SKILL.md` 的 skill 目录。不要要求用户手动初始化环境，也不要要求用户创建 `templates/`、`workspaces/`、manifest 或 content JSON；普通使用时用户只需要提供源 PPTX，agent 返回翻译后的 PPTX。

| Step | Command | Output |
| --- | --- | --- |
| 初始化临时工作区 | `python3 <skill-root>/scripts/pptx_json_cli.py init <source.pptx> -w <workspace>` | 工作区 + 槽位摘要 + 内容骨架 |
| 检查槽位 | `python3 <skill-root>/scripts/pptx_json_cli.py inspect-manifest <workspace> --for-ai` | AI 友好的可翻译槽位摘要 |
| 写翻译内容 | AI 写 `<workspace>/deck_content.json` | 翻译内容 JSON |
| 一键构建 | `python3 <skill-root>/scripts/pptx_json_cli.py build <workspace>` | 校验 + 编译 + 导出 PPTX |
| 翻译验证 | `python3 <skill-root>/scripts/pptx_json_cli.py verify-pptx <workspace>/exports/output.pptx --old-terms ... --new-terms ...` | 可见文本残留检查 |
| 返回结果 | 把 `<workspace>/exports/output.pptx` 提供给用户 | 翻译后的 PPTX |

---

## 4. 可翻译元素清单

| 元素 | 需要翻译 | 不要改动 |
| --- | --- | --- |
| 普通文本框、标题、placeholder | `text.content` / `text.paragraphs` | 位置、尺寸、主题、段落意图 |
| 项目符号和多段落文本 | 每段文本和 run 文本 | bullet 层级、强调样式，除非 manifest 无法表达 |
| 表格 | 已有单元格中的文本 | 行列数量、表格尺寸、数值 |
| 图表 | category 标签、series 名称 | series 数值、图表类型、坐标轴结构 |
| 图片 | `alt` 描述文本 | 图片文件、裁剪、位置，除非用户要求换图 |
| 形状中的文字 | 作为 `text` slot 翻译 | shape 样式、几何、颜色 |

暂不翻译：SmartArt 内部文本、备注页、评论、视频/音频内容、OLE/嵌入文件、宏、动画内部标签。遇到这些内容时报告限制，不要伪造翻译结果。

---

## 5. 翻译写作规则

**Hard rule**: AI 默认只写 `deck_content.json`。

**Hard rule**: 只填写 `template_manifest.json` 中存在的 slot。

**Hard rule**: 翻译时保留事实信息。数字、单位、货币、日期、URL、邮箱、产品名、公司名、人名、专有名词默认不改写。

**Hard rule**: 保持每个 slot 的语义角色。标题仍像标题，表头仍像表头，图例仍像图例。

**Hard rule**: 不直接编辑 `package/` XML，不手写自由 OOXML patch，不修改 preserved objects。

---

## 6. 文本溢出与自动缩字号

翻译后文本通常比源语言更长。容量超限时：

- `validate-content` 记录 `CAPACITY_EXCEEDED` warning，不阻断导出。
- `compile-patch` 为超长文本生成 `autofit.enabled=true` 和 `font_scale`。
- `export-pptx` 写入 PowerPoint 原生 `a:normAutofit fontScale="..."`，让文本在原文本框中缩小字号。
- 如果缩小后仍明显拥挤，优先压缩译文表达；不要移动文本框或改变版式，除非用户明确要求。

---

## 7. 细粒度命令

| Step | Command | Output |
| --- | --- | --- |
| 分析 PPTX | `python3 <skill-root>/scripts/pptx_json_cli.py analyze-template <source.pptx> -o <workspace>` | `template_manifest.json` |
| 检查槽位 | `python3 <skill-root>/scripts/pptx_json_cli.py inspect-manifest <workspace> --for-ai` | AI 友好的槽位摘要 |
| 生成骨架 | `python3 <skill-root>/scripts/pptx_json_cli.py draft-content <workspace> -o <workspace>/deck_content.skeleton.json` | 内容骨架 |
| 校验内容 | `python3 <skill-root>/scripts/pptx_json_cli.py validate-content <workspace> <workspace>/deck_content.json` | 校验报告 |
| 编译补丁 | `python3 <skill-root>/scripts/pptx_json_cli.py compile-patch <workspace> <workspace>/deck_content.json` | `patch_plan.json` |
| 导出 PPTX | `python3 <skill-root>/scripts/pptx_json_cli.py export-pptx <workspace> -o <workspace>/exports/output.pptx` | 翻译版 PPTX |
| 导出验证 | `python3 <skill-root>/scripts/pptx_json_cli.py verify-pptx <workspace>/exports/output.pptx --old-terms ... --new-terms ...` | 可见文本残留检查 |

---

## 8. 运行测试

```bash
python3 -m unittest discover -s tests -t tests -v
```
