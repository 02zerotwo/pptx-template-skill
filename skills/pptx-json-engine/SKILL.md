---
name: pptx-json-engine
description: >
  Use when the user wants to generate a PPTX from a template.
  Analyzes the template into editable slots, lets AI write content JSON,
  then builds the final PPTX in one command.
---

# PPTX JSON Engine

Use this skill when the user wants to generate a new PPTX from a PPTX template. The workflow is template-first: preserve the original OOXML package, expose only editable slots, let AI write content JSON, compile a public patch plan, then export PPTX.

## Core Rule

AI writes `deck_content.json` by default. AI does not directly edit XML, does not write freeform OOXML patches, and does not modify preserved objects.

## Workflow

All commands run from `skills/pptx-json-engine/` directory via `uv run python scripts/pptx_json_cli.py`.

### Step 0 — Setup environment (first time only)

```bash
cd skills/pptx-json-engine
uv sync
uv run python scripts/pptx_json_cli.py setup
```

### Step 1 — Initialize workspace from template

Creates workspace, copies template, analyzes slots, generates skeleton — all in one command:

```bash
uv run python scripts/pptx_json_cli.py init <template.pptx> -w <workspace>
```

Output: `template_manifest.json`, slot summary, `deck_content.skeleton.json`.

### Step 2 — Write `deck_content.json`

AI writes `<workspace>/deck_content.json` using only slots declared by the manifest.

Use `inspect-manifest` to review slots if needed:

```bash
uv run python scripts/pptx_json_cli.py inspect-manifest <workspace> --for-ai
```

### Step 3 — Build PPTX

Validates content, compiles patch plan, exports PPTX — all in one command:

```bash
uv run python scripts/pptx_json_cli.py build <workspace>
```

Output: `<workspace>/exports/output.pptx`.

Custom content/output paths:

```bash
uv run python scripts/pptx_json_cli.py build <workspace> -c <content.json> -o <output.pptx>
```

### Step 4 — Verify (optional)

```bash
uv run python scripts/pptx_json_cli.py verify-pptx <workspace>/exports/output.pptx --old-terms <old...> --new-terms <new...>
```

## Editable Slot Types

| Type    | Fields                                | Notes                                                                         |
| ------- | ------------------------------------- | ----------------------------------------------------------------------------- |
| `text`  | `content`, `paragraphs`               | Replaces whole text boxes; structured paragraphs support bullet/run summaries |
| `image` | `src`, `alt`                          | Replaces media relationship and/or writes image description                   |
| `table` | `cells`                               | Replaces existing table cell text within current row/column bounds            |
| `chart` | `categories`, `series`                | Updates chart XML caches; embedded workbook editing is not guaranteed         |
| `shape` | `fill`, `line`, `opacity`, `geometry` | Supports simple shapes and vector/icon-like preset shapes                     |

P4 objects such as SmartArt editing, animation editing, notes, video, audio, and arbitrary embedded object editing are out of scope.

## References

| File                             | Use                                                         |
| -------------------------------- | ----------------------------------------------------------- |
| `references/workflow.md`         | Full workflow: setup, commands, rules, and image resources  |
| `references/manifest-json.md`    | `template_manifest.json` contract                           |
| `references/content-json.md`     | `deck_content.json` contract and AI writing rules           |
| `references/patch-plan-json.md`  | Stable public `patch_plan.json` contract                    |
| `references/ooxml-boundaries.md` | Editable objects, preserved objects, and refusal boundaries |

## Failure Behavior

If validation reports missing required slots, unknown slots, invalid resource paths, over-capacity text, stale bindings, or broken relationships, stop and ask the user to revise the template, content, or resources.
