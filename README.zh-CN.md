# pptx-template-engine

一个面向 AI 工作流的 Template-first PPTX 生成引擎。

这个仓库提供了一个可复用的 skill 和一套 Python CLI：先把 PowerPoint 模板分析成可编辑槽位，再让 AI 写结构化的 `deck_content.json`，随后编译成稳定的 patch plan，最终导出新的 `.pptx`，整个过程不需要直接手改 OOXML。

[English README](README.md)

## 这个项目解决什么问题

很多 PPTX 自动化方案要么从零重建页面，要么把底层 XML 暴露得太多。`pptx-template-engine` 走的是一条更收敛的路线：

- 保留原始 PPTX 包和版式
- 只暴露安全、可编辑的槽位
- 让 AI 写内容 JSON，而不是 XML
- 默认保留不可编辑对象
- 通过稳定的流水线导出最终 PPTX

这很适合模板化演示文稿生成、报告生产，以及要求结构稳定的 agent 工作流。

## 你会得到什么

- 用于 agent 调用的 `SKILL.md`
- 用于 setup、init、build、validate、export 的 Python CLI
- manifest、content、patch plan 的 JSON contract
- examples、references 和 tests

当前支持的可编辑槽位类型：

- `text`
- `image`
- `table`
- `chart`
- `shape`

当前默认不处理的对象：

- SmartArt 内部结构
- 动画编辑
- 备注页
- 视频 / 音频
- 任意嵌入对象编辑

## 仓库结构

```text
.
├── skills/pptx-template-engine/
│   ├── SKILL.md
│   ├── scripts/
│   ├── references/
│   ├── examples/
│   └── tests/
├── templates/
└── workspaces/
```

核心实现都在 `skills/pptx-template-engine/` 下面。根目录的 `templates/` 和 `workspaces/` 适合存放源模板和生成过程中的工作区。

## 环境要求

- Python 3.10+
- 推荐使用 [`uv`](https://docs.astral.sh/uv/)
- macOS / Linux / Windows(WSL)

运行时代码只依赖 Python 标准库。`uv` 主要用于环境初始化和命令管理。

## 快速开始

进入 skill 目录：

```bash
cd skills/pptx-template-engine
uv sync
uv run python scripts/pptx_json_cli.py setup
```

基于模板初始化一个 workspace：

```bash
uv run python scripts/pptx_json_cli.py init ../../templates/template.pptx -w ../../workspaces/my-deck
```

这一步会生成：

- 复制后的源模板
- `template_manifest.json`
- 槽位摘要
- `deck_content.skeleton.json`

然后编写 `deck_content.json`，再执行构建：

```bash
uv run python scripts/pptx_json_cli.py build ../../workspaces/my-deck
```

输出文件：

```text
workspaces/my-deck/exports/output.pptx
```

## AI 工作流

推荐流程非常明确：

1. 把 PPTX 模板分析成 `template_manifest.json`
2. 只基于已声明槽位编写 `deck_content.json`
3. 按槽位规则和容量约束做校验
4. 编译 `patch_plan.json`
5. 导出最终 PPTX

核心原则只有一句话：AI 写的是内容 JSON，不是底层 XML。

## 内容 JSON 示例

```json
{
  "schema_version": "1.0",
  "title": "2026 年市场增长策略",
  "slides": [
    {
      "template_slide": "template-slide-001",
      "content": {
        "cover_title": {
          "content": "2026 年市场增长策略"
        },
        "hero_image": {
          "src": "assets/generated/hero.png",
          "alt": "market strategy hero image"
        }
      }
    }
  ]
}
```

## CLI 命令

一键式命令：

```bash
uv run python scripts/pptx_json_cli.py setup
uv run python scripts/pptx_json_cli.py init <template.pptx> -w <workspace>
uv run python scripts/pptx_json_cli.py build <workspace>
```

也支持拆开的细粒度命令：

```bash
uv run python scripts/pptx_json_cli.py analyze-template <template.pptx> -o <workspace>
uv run python scripts/pptx_json_cli.py inspect-manifest <workspace> --for-ai
uv run python scripts/pptx_json_cli.py draft-content <workspace> -o <workspace>/deck_content.skeleton.json
uv run python scripts/pptx_json_cli.py validate-content <workspace> <workspace>/deck_content.json
uv run python scripts/pptx_json_cli.py compile-patch <workspace> <workspace>/deck_content.json
uv run python scripts/pptx_json_cli.py export-pptx <workspace> -o <workspace>/exports/output.pptx
uv run python scripts/pptx_json_cli.py verify-pptx <workspace>/exports/output.pptx --old-terms ... --new-terms ...
```

## Contracts 与参考文档

更细的说明都放在 skill 目录里：

- [`skills/pptx-template-engine/SKILL.md`](skills/pptx-template-engine/SKILL.md)
- [`skills/pptx-template-engine/references/workflow.md`](skills/pptx-template-engine/references/workflow.md)
- [`skills/pptx-template-engine/references/manifest-json.md`](skills/pptx-template-engine/references/manifest-json.md)
- [`skills/pptx-template-engine/references/content-json.md`](skills/pptx-template-engine/references/content-json.md)
- [`skills/pptx-template-engine/references/patch-plan-json.md`](skills/pptx-template-engine/references/patch-plan-json.md)
- [`skills/pptx-template-engine/references/ooxml-boundaries.md`](skills/pptx-template-engine/references/ooxml-boundaries.md)

## 测试

在 `skills/pptx-template-engine/` 目录下运行：

```bash
uv run python -m unittest discover -s tests -t tests -v
```

只跑单元测试：

```bash
uv run python -m unittest discover -s tests/unit -t tests -v
```

## 设计取向

这个项目的设计非常克制：

- 优先保留模板保真度
- 对外接口保持 JSON 化
- patch 编译尽量稳定、可预测
- 对不支持的编辑明确拒绝，而不是假装安全

如果校验因为缺失槽位、绑定失效、路径错误或文本超容量而失败，正确做法通常是修改模板或内容，而不是绕过流程。
