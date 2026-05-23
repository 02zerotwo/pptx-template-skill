# pptx-translate-skill

一个面向 AI agent 的 template-first PowerPoint skill。

`pptx-translate-skill` 可以在不重建整份演示文稿的前提下翻译或改写已有 `.pptx`。它先把源 PPTX 分析成安全可编辑的槽位，再让 AI 编写结构化的 `deck_content.json`，随后编译成确定性的 patch plan，最后导出新的 PPTX，同时尽量保留原始版式、主题、媒体和 OOXML 包结构。

[English README](README.md)

## 快速安装

`npx skills add` CLI 会扫描这个仓库里的 `skills/` 目录，所以可以用一条命令安装：

```bash
npx skills add https://github.com/02zerotwo/pptx-translate-skill
```

如果只想安装这个 skill，可以用 install name 指定。这里使用的是 `SKILL.md` frontmatter 里的 `name:` 字段，不是文件夹名：

```bash
npx skills add https://github.com/02zerotwo/pptx-translate-skill --skill "pptx-translate-skill"
```

安装后，直接让 agent 在翻译或改写 PPTX 时使用这个 skill：

```text
使用 pptx-translate-skill 把 ./deck.pptx 翻译成英文。
保留原始版式、图表、图片和动画。
```

这个 skill 自带 `SKILL.md`、参考文档和 Python 脚本。实际使用时，用户给 agent 一个 PPTX，agent 返回翻译后的 PPTX。临时分析文件、工作区、缓存和生成过程都属于实现细节。

如果没有 skills installer，也可以把 `skills/pptx-translate-skill/SKILL.md` 复制到自己的项目里，或者直接粘贴到 ChatGPT / Codex 对话中使用。

## Agent 使用方式

推荐使用面向结果的 prompt：

```text
使用 pptx-translate-skill 把 ./q3-report.pptx 翻译成中文。
保留页数、版式、主题、图片、图表和动画行为。
产品名、URL、日期和数字保持不变。
```

```text
使用 pptx-translate-skill 把 ./sales-deck.pptx 本地化成面向日本市场的版本。
使用 ./glossary.md 里的术语表，并导出最终 .pptx。
```

agent 内部工作流是：

1. 把源 PPTX 分析成可编辑槽位 manifest。
2. 只填写 manifest 中声明的槽位到 `deck_content.json`。
3. 导出前校验内容。
4. 编译确定性的 patch plan。
5. 导出并返回最终 PPTX 路径。

## 为什么需要这个项目

很多 PPTX 自动化方案容易走向两个高风险方向：要么从零重绘每一页，要么把底层 OOXML 过多暴露给 AI。这两种方式都很容易破坏版式、主题关系、媒体位置、图表绑定或隐藏的包结构。

这个 skill 使用更收敛的契约：

- 原始 PPTX 包始终是 source of truth
- 只暴露经过分析和校验的可编辑槽位
- AI 写内容 JSON，而不是 XML
- 内容变更会先编译成稳定的 patch plan
- 导出时只修改受支持的 OOXML 目标
- 遇到不支持的编辑明确拒绝，而不是假装安全

因此它适合翻译、本地化、模板化报告生成，以及所有需要保留原设计的 agent 工作流。

## 实现思路

引擎围绕五段流水线实现。

1. `analyze-template` 打开 PPTX 包，读取 slide relationships 和受支持的 OOXML parts，生成 `template_manifest.json`。
2. `inspect-manifest` 把可编辑槽位整理成适合 AI 阅读的摘要，包括文本框、表格、图表标签、图片 alt 文本和受支持的形状文本。
3. AI 只基于 manifest 中声明的 slot ID 编写 `deck_content.json`。
4. `validate-content` 和 `compile-patch` 校验内容契约、容量限制、资源路径和过期绑定，然后生成 `patch_plan.json`。
5. `export-pptx` 把 patch plan 应用到源 PPTX 的副本上，导出最终演示文稿。

关键设计选择是职责分离：AI 负责决定内容，引擎负责判断内容是否能安全落到 PPTX 里，以及应该如何落地。

当前支持的可编辑槽位类型：

- `text`
- `image`
- `table`
- `chart`
- `shape`

默认不处理的对象：

- SmartArt 内部编辑
- 动画编辑
- 备注页
- 视频 / 音频编辑
- 任意嵌入对象编辑
- 自由 OOXML patch

## Skill 工作方式

agent 使用这个 skill 时，核心规则只有一句：

```text
AI 写 deck_content.json，不直接编辑 OOXML。
```

内置 CLI 主要给 agent 和维护者使用。agent 可以用它创建临时工作区、检查槽位、校验内容、构建最终文件，并验证术语。终端用户通常只需要安装 skill、提供源 PPTX，然后向 agent 描述想要的翻译版 PPTX 输出。

做翻译时，事实信息默认不改：数字、单位、日期、URL、邮箱、产品名、公司名、人名和法律名称都应保持原样，除非用户提供术语表。

译文较长时可能超过原文本框容量。此时校验会给出 warning，导出阶段会写入 PowerPoint 原生 autofit 设置，让文本在原始边界内自动缩小。

## 维护者 CLI

在本仓库开发或调试 skill 时，从 `skills/pptx-translate-skill/` 目录运行：

```bash
python3 scripts/pptx_json_cli.py init <source.pptx> -w <workspace>
python3 scripts/pptx_json_cli.py build <workspace>
```

也可以使用细粒度命令：

```bash
python3 scripts/pptx_json_cli.py analyze-template <source.pptx> -o <workspace>
python3 scripts/pptx_json_cli.py inspect-manifest <workspace> --for-ai
python3 scripts/pptx_json_cli.py draft-content <workspace> -o <workspace>/deck_content.skeleton.json
python3 scripts/pptx_json_cli.py validate-content <workspace> <workspace>/deck_content.json
python3 scripts/pptx_json_cli.py compile-patch <workspace> <workspace>/deck_content.json
python3 scripts/pptx_json_cli.py export-pptx <workspace> -o <workspace>/exports/output.pptx
python3 scripts/pptx_json_cli.py verify-pptx <workspace>/exports/output.pptx --old-terms ... --new-terms ...
```

## 仓库结构

```text
.
├── skills/pptx-translate-skill/
│   ├── SKILL.md
│   ├── scripts/
│   ├── references/
│   └── tests/
└── README.md
```

可复用的 skill 和 CLI 位于 `skills/pptx-translate-skill/`。用户提供的 PPTX 和生成过程中的工作区都是运行时产物，不属于仓库契约。

## 环境要求

- Python 3.10+
- macOS / Linux / Windows(WSL)

运行时代码只依赖 Python 标准库。

## 参考文档

- [`skills/pptx-translate-skill/SKILL.md`](skills/pptx-translate-skill/SKILL.md)
- [`skills/pptx-translate-skill/references/workflow.md`](skills/pptx-translate-skill/references/workflow.md)
- [`skills/pptx-translate-skill/references/manifest-json.md`](skills/pptx-translate-skill/references/manifest-json.md)
- [`skills/pptx-translate-skill/references/content-json.md`](skills/pptx-translate-skill/references/content-json.md)
- [`skills/pptx-translate-skill/references/patch-plan-json.md`](skills/pptx-translate-skill/references/patch-plan-json.md)
- [`skills/pptx-translate-skill/references/ooxml-boundaries.md`](skills/pptx-translate-skill/references/ooxml-boundaries.md)

## 测试

在 `skills/pptx-translate-skill/` 目录运行：

```bash
python3 -m unittest discover -s tests -t tests -v
```

只跑单元测试：

```bash
python3 -m unittest discover -s tests/unit -t tests -v
```
