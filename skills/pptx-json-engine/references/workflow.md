# PPTX JSON Engine Workflow

本文定义 AI 用户基于 PPTX 模板生成新 PPTX 的实际流程。

## 1. 使用场景

当用户提供 PPTX 模板，并要求“基于这个模板生成新的 PPTX”时，使用本 skill。不要进入 SVG 生成流程，不要把 PPTX 全量转换成可自由编辑 JSON。

---

## 2. 系统要求

| 项目       | 要求                             |
| ---------- | -------------------------------- |
| Python     | >= 3.10                          |
| 操作系统   | macOS / Linux / Windows (WSL)    |
| 包管理工具 | [uv](https://docs.astral.sh/uv/) |

引擎仅使用 Python 标准库，无第三方运行依赖。

安装 uv（首次）：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# 或 brew install uv
```

手动安装（不使用 uv）：

```bash
python3 -m venv .venv && source .venv/bin/activate
```

---

## 3. AI 快速流程（3 条命令）

所有命令从 `skills/pptx-json-engine/` 目录运行。

| Step         | Command                                                                      | Output                       |
| ------------ | ---------------------------------------------------------------------------- | ---------------------------- |
| 环境准备     | `uv sync && uv run python scripts/pptx_json_cli.py setup`                    | 环境检查报告                 |
| 初始化工作区 | `uv run python scripts/pptx_json_cli.py init <template.pptx> -w <workspace>` | 工作区 + 槽位摘要 + 内容骨架 |
| 生成内容     | AI 写 `<workspace>/deck_content.json`                                        | 内容 JSON                    |
| 一键构建     | `uv run python scripts/pptx_json_cli.py build <workspace>`                   | 校验 + 编译 + 导出 PPTX      |

---

## 4. 细粒度命令（按需使用）

| Step      | Command                                                                                                              | Output                   |
| --------- | -------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| 分析模板  | `uv run python scripts/pptx_json_cli.py analyze-template <template.pptx> -o <workspace>`                             | `template_manifest.json` |
| 检查槽位  | `uv run python scripts/pptx_json_cli.py inspect-manifest <workspace> --for-ai`                                       | AI 友好的槽位摘要        |
| 生成骨架  | `uv run python scripts/pptx_json_cli.py draft-content <workspace> -o <workspace>/deck_content.skeleton.json`         | 可编辑内容骨架           |
| 校验内容  | `uv run python scripts/pptx_json_cli.py validate-content <workspace> <workspace>/deck_content.json`                  | 校验报告                 |
| 编译补丁  | `uv run python scripts/pptx_json_cli.py compile-patch <workspace> <workspace>/deck_content.json`                     | `patch_plan.json`        |
| 导出 PPTX | `uv run python scripts/pptx_json_cli.py export-pptx <workspace> -o <workspace>/exports/output.pptx`                  | 新 PPTX                  |
| 导出验证  | `uv run python scripts/pptx_json_cli.py verify-pptx <workspace>/exports/output.pptx --old-terms ... --new-terms ...` | 可见文本残留检查         |

---

## 5. AI 操作规则

**Hard rule**: AI 默认只写 `deck_content.json`。

**Hard rule**: 只填写 `template_manifest.json` 中存在的 slot。

**Hard rule**: 如果校验失败，停止导出并报告错误。

**Forbidden**:

- 直接编辑 `package/` 中的 XML。
- 直接手写自由 OOXML patch。
- 修改 preserved objects。
- 把图片写成 base64 放入 JSON。
- 编辑 P4 对象：SmartArt 内部结构、动画、备注页、视频、音频、任意 OLE 对象。

---

## 6. 推荐用户体验

用户只需要提供模板和生成意图：

```text
用 template.pptx，生成一份 2026 年市场增长策略汇报。
```

AI 执行流程：

```bash
# 1. 环境确认
uv run python scripts/pptx_json_cli.py setup

# 2. 初始化工作区
uv run python scripts/pptx_json_cli.py init template.pptx -w ../../workspaces/market-growth

# 3. AI 写 deck_content.json ...

# 4. 一键构建
uv run python scripts/pptx_json_cli.py build ../../workspaces/market-growth
```

---

## 7. 图片资源

如果模板包含图片槽位，在写 `deck_content.json` 前将替换图片放入 `<workspace>/assets/media/`。

支持格式：`.png`, `.jpg`, `.jpeg`, `.gif`, `.emf`, `.wmf`。不支持 `.svg`。

在 `deck_content.json` 中使用相对于 `assets/` 的路径引用：

```json
{
  "slot_id": "image_s1_pic1",
  "src": "media/photo.png",
  "alt": "示例图片"
}
```

---

## 8. 运行测试

```bash
# 从 skills/pptx-json-engine/ 目录运行
uv run python -m unittest discover -s tests -t tests -v

# 仅单元测试
uv run python -m unittest discover -s tests/unit -t tests -v
```
