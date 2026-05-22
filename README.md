# pptx-translate-skill

Template-first PPTX generation for AI workflows.

This repository packages a reusable skill and Python CLI that analyze a PowerPoint template into editable slots, let an AI write structured `deck_content.json`, compile a stable patch plan, and export a finished `.pptx` without hand-editing OOXML.

[中文说明](README.zh-CN.md)

## Why this exists

Most PPTX automation tools either rebuild slides from scratch or expose too much low-level XML. `pptx-translate-skill` takes a narrower path:

- keep the original PPTX package and layout
- expose only safe, editable slots
- let AI write content JSON instead of XML
- preserve non-editable objects by default
- export a final PPTX through a predictable pipeline

That makes it a good fit for template-based deck generation, report production, and agent workflows where structure matters more than freeform slide drawing.

## What you get

- `SKILL.md` for agent-driven PPTX generation
- a Python CLI for setup, init, build, validation, and export
- JSON contracts for manifest, content, and patch plans
- examples, references, and tests

Supported editable slot types today:

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

## Repository layout

```text
.
├── skills/pptx-translate-skill/
│   ├── SKILL.md
│   ├── scripts/
│   ├── references/
│   ├── examples/
│   └── tests/
├── templates/
└── workspaces/
```

The implementation lives under `skills/pptx-translate-skill/`. Root-level `templates/` and `workspaces/` are convenient places to store source PPTX files and generated project workspaces.

## Requirements

- Python 3.10+
- [`uv`](https://docs.astral.sh/uv/) recommended
- macOS, Linux, or Windows via WSL

Runtime code uses the Python standard library only. `uv` is mainly for environment and command management.

## Quick start

From the skill directory:

```bash
cd skills/pptx-translate-skill
uv sync
uv run python scripts/pptx_json_cli.py setup
```

Initialize a workspace from a template:

```bash
uv run python scripts/pptx_json_cli.py init ../../templates/template.pptx -w ../../workspaces/my-deck
```

This creates a workspace with:

- copied source template
- `template_manifest.json`
- slot summary
- `deck_content.skeleton.json`

Write `deck_content.json`, then build:

```bash
uv run python scripts/pptx_json_cli.py build ../../workspaces/my-deck
```

Output:

```text
workspaces/my-deck/exports/output.pptx
```

## AI workflow

The intended flow is short and strict:

1. Analyze the PPTX template into `template_manifest.json`
2. Write `deck_content.json` using only declared slots
3. Validate content against slot rules and capacity
4. Compile `patch_plan.json`
5. Export the final PPTX

The core rule is simple: AI writes content JSON, not raw XML.

## Example content

```json
{
  "schema_version": "1.0",
  "title": "2026 Market Growth Strategy",
  "slides": [
    {
      "template_slide": "template-slide-001",
      "content": {
        "cover_title": {
          "content": "2026 Market Growth Strategy"
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

## CLI commands

One-shot commands:

```bash
uv run python scripts/pptx_json_cli.py setup
uv run python scripts/pptx_json_cli.py init <template.pptx> -w <workspace>
uv run python scripts/pptx_json_cli.py build <workspace>
```

Granular commands are also available:

```bash
uv run python scripts/pptx_json_cli.py analyze-template <template.pptx> -o <workspace>
uv run python scripts/pptx_json_cli.py inspect-manifest <workspace> --for-ai
uv run python scripts/pptx_json_cli.py draft-content <workspace> -o <workspace>/deck_content.skeleton.json
uv run python scripts/pptx_json_cli.py validate-content <workspace> <workspace>/deck_content.json
uv run python scripts/pptx_json_cli.py compile-patch <workspace> <workspace>/deck_content.json
uv run python scripts/pptx_json_cli.py export-pptx <workspace> -o <workspace>/exports/output.pptx
uv run python scripts/pptx_json_cli.py verify-pptx <workspace>/exports/output.pptx --old-terms ... --new-terms ...
```

## Contracts and references

The deeper docs live with the skill:

- [`skills/pptx-translate-skill/SKILL.md`](skills/pptx-translate-skill/SKILL.md)
- [`skills/pptx-translate-skill/references/workflow.md`](skills/pptx-translate-skill/references/workflow.md)
- [`skills/pptx-translate-skill/references/manifest-json.md`](skills/pptx-translate-skill/references/manifest-json.md)
- [`skills/pptx-translate-skill/references/content-json.md`](skills/pptx-translate-skill/references/content-json.md)
- [`skills/pptx-translate-skill/references/patch-plan-json.md`](skills/pptx-translate-skill/references/patch-plan-json.md)
- [`skills/pptx-translate-skill/references/ooxml-boundaries.md`](skills/pptx-translate-skill/references/ooxml-boundaries.md)

## Testing

From `skills/pptx-translate-skill/`:

```bash
uv run python -m unittest discover -s tests -t tests -v
```

Unit tests only:

```bash
uv run python -m unittest discover -s tests/unit -t tests -v
```

## Design notes

This project is intentionally conservative:

- preserve template fidelity first
- keep the public interface JSON-based
- keep patch compilation deterministic
- reject unsupported edits instead of pretending they are safe

If validation fails because of missing slots, stale bindings, path issues, or over-capacity text, the correct next step is to fix the template or content rather than bypass the workflow.
