# pptx-translate-skill

A template-first PowerPoint skill for AI agents.

`pptx-translate-skill` translates or rewrites an existing `.pptx` without rebuilding the deck from scratch. It analyzes a source PowerPoint file into safe editable slots, asks the AI to write structured `deck_content.json`, compiles that JSON into a deterministic patch plan, and exports a finished PPTX while preserving the original layout, theme, media, and package structure.

[中文说明](README.zh-CN.md)

## Quick Install

The `npx skills add` CLI scans the `skills/` folder in this repo, so install the skill with one command:

```bash
npx skills add https://github.com/02zerotwo/pptx-translate-skill
```

Install only this skill by its install name. Use the `name:` field inside `SKILL.md` frontmatter, not the folder name:

```bash
npx skills add https://github.com/02zerotwo/pptx-translate-skill --skill "pptx-translate-skill"
```

After installation, use it by asking your agent to translate or rewrite a PPTX while preserving layout:

```text
Use pptx-translate-skill to translate ./deck.pptx into English.
Keep the original layout, charts, images, and animations.
```

The skill includes its own `SKILL.md`, reference docs, and Python scripts. In normal use, the user gives the agent a PPTX file and the agent returns a translated PPTX. Temporary analysis files, workspaces, caches, and generated outputs are implementation details.

You can also copy `skills/pptx-translate-skill/SKILL.md` into your project, or paste it into ChatGPT / Codex conversations when a skills installer is not available.

## Agent Usage

Good prompts are outcome-oriented:

```text
Use pptx-translate-skill to translate ./q3-report.pptx to Chinese.
Preserve slide count, layout, theme, images, charts, and animation behavior.
Keep product names, URLs, dates, and numbers unchanged.
```

```text
Use pptx-translate-skill to localize ./sales-deck.pptx for a Japanese audience.
Use the glossary in ./glossary.md and export a finished .pptx.
```

The agent-facing workflow is internal:

1. Analyze the source PPTX into a manifest of editable slots.
2. Fill only declared slots in `deck_content.json`.
3. Validate content before export.
4. Compile a deterministic patch plan.
5. Export and return the final PPTX path.

## Why This Exists

Most PPTX automation tools take one of two risky paths: they either redraw every slide from scratch, or they expose too much raw OOXML to the AI. Both approaches make it easy to break layout, theme relationships, media placement, chart wiring, or hidden package structure.

This skill uses a narrower contract:

- keep the original PPTX package as the source of truth
- expose only editable, validated slots
- let the AI write content JSON, not XML
- compile edits into a stable patch plan
- export by modifying only supported OOXML targets
- reject unsupported edits instead of pretending they are safe

The result is a workflow that fits translation, report localization, template-based deck generation, and agent workflows where preserving the existing design matters.

## Implementation Approach

The engine is built around a five-stage pipeline.

1. `analyze-template` opens the PPTX package, reads slide relationships and supported OOXML parts, and produces `template_manifest.json`.
2. `inspect-manifest` summarizes editable slots for the AI: text boxes, tables, chart labels, image alt text, and supported shape text.
3. The AI writes `deck_content.json` using only slot IDs declared in the manifest.
4. `validate-content` and `compile-patch` check the content contract, capacity limits, resource paths, and stale bindings, then create `patch_plan.json`.
5. `export-pptx` applies the patch plan to a copy of the source PPTX and writes the final deck.

The important design choice is separation of responsibility: AI decides content, while the engine decides whether and how that content can be safely applied.

Supported editable slot types:

- `text`
- `image`
- `table`
- `chart`
- `shape`

Out of scope by default:

- SmartArt internal editing
- animation editing
- notes pages
- video/audio editing
- arbitrary embedded object editing
- freeform OOXML patches

## How The Skill Works

When an agent uses this skill, the core rule is:

```text
AI writes deck_content.json. AI does not directly edit OOXML.
```

The bundled CLI is for agents and maintainers. Agents can use it to create temporary workspaces, inspect slots, validate content, build the final deck, and verify terminology. End users usually only need to install the skill, provide a source PPTX, and ask for the desired translated PPTX output.

For translation, preserve facts by default: numbers, units, dates, URLs, emails, product names, company names, and legal names should stay unchanged unless the user provides a glossary.

Long translated text can exceed the original box capacity. In that case validation emits a warning, and export writes PowerPoint native autofit settings so the text can shrink inside the original bounds.

## Maintainer CLI

When developing or debugging the skill from this repository, run commands from `skills/pptx-translate-skill/`:

```bash
python3 scripts/pptx_json_cli.py init <source.pptx> -w <workspace>
python3 scripts/pptx_json_cli.py build <workspace>
```

Granular commands are also available:

```bash
python3 scripts/pptx_json_cli.py analyze-template <source.pptx> -o <workspace>
python3 scripts/pptx_json_cli.py inspect-manifest <workspace> --for-ai
python3 scripts/pptx_json_cli.py draft-content <workspace> -o <workspace>/deck_content.skeleton.json
python3 scripts/pptx_json_cli.py validate-content <workspace> <workspace>/deck_content.json
python3 scripts/pptx_json_cli.py compile-patch <workspace> <workspace>/deck_content.json
python3 scripts/pptx_json_cli.py export-pptx <workspace> -o <workspace>/exports/output.pptx
python3 scripts/pptx_json_cli.py verify-pptx <workspace>/exports/output.pptx --old-terms ... --new-terms ...
```

## Repository Layout

```text
.
├── skills/pptx-translate-skill/
│   ├── SKILL.md
│   ├── scripts/
│   ├── references/
│   └── tests/
└── README.md
```

The reusable skill and CLI live under `skills/pptx-translate-skill/`. User PPTX files and generated workspaces are runtime artifacts, not part of the repository contract.

## Requirements

- Python 3.10+
- macOS, Linux, or Windows via WSL

Runtime code uses the Python standard library only.

## References

- [`skills/pptx-translate-skill/SKILL.md`](skills/pptx-translate-skill/SKILL.md)
- [`skills/pptx-translate-skill/references/workflow.md`](skills/pptx-translate-skill/references/workflow.md)
- [`skills/pptx-translate-skill/references/manifest-json.md`](skills/pptx-translate-skill/references/manifest-json.md)
- [`skills/pptx-translate-skill/references/content-json.md`](skills/pptx-translate-skill/references/content-json.md)
- [`skills/pptx-translate-skill/references/patch-plan-json.md`](skills/pptx-translate-skill/references/patch-plan-json.md)
- [`skills/pptx-translate-skill/references/ooxml-boundaries.md`](skills/pptx-translate-skill/references/ooxml-boundaries.md)

## Testing

From `skills/pptx-translate-skill/`:

```bash
python3 -m unittest discover -s tests -t tests -v
```

Unit tests only:

```bash
python3 -m unittest discover -s tests/unit -t tests -v
```
