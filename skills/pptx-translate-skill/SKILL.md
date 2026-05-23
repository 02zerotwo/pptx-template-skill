---
name: pptx-translate-skill
description: >
  Use when the user wants to translate an existing PPTX while preserving
  slide layout, theme, media, animations, and OOXML package structure.
---

# PPTX Translate Skill

Use this skill to translate a PPTX into another language without rebuilding the deck. The workflow is source-deck-first: analyze translatable slots, write translated `deck_content.json`, compile a controlled patch plan, export a translated PPTX, and verify visible text.

## Core Rules

AI writes `deck_content.json` by default. AI does not directly edit XML, handwrite OOXML patches, or modify preserved objects.

Preserve slide count, slide order, layout, theme, media placement, crop, animation, transitions, and non-translatable styling unless the user explicitly asks for a supported edit.

Translate meaning, not geometry. Keep numbers, units, product names, URLs, emails, legal names, and brand terms unchanged unless the user provides a glossary.

## Workflow

All commands run from `skills/pptx-translate-skill/` via `uv run python scripts/pptx_json_cli.py`.

### Step 0 — Setup Environment

```bash
cd skills/pptx-translate-skill
uv sync
uv run python scripts/pptx_json_cli.py setup
```

### Step 1 — Initialize Translation Workspace

```bash
uv run python scripts/pptx_json_cli.py init <source.pptx> -w <workspace>
```

Output: `template_manifest.json`, translatable slot summary, and `deck_content.skeleton.json`.

### Step 2 — Inspect Translatable Slots

```bash
uv run python scripts/pptx_json_cli.py inspect-manifest <workspace> --for-ai
```

Check every slide. Do not translate only obvious text boxes; inspect table, chart, and image-alt slots too.

### Step 3 — Write Translated `deck_content.json`

Use only slots declared by the manifest.

Translate these elements when present:

| Element | What to Translate | What to Preserve |
| --- | --- | --- |
| Text boxes and placeholders | `text.content` or `text.paragraphs` | Paragraph intent, bullets, emphasis, line breaks where practical |
| Tables | Text in `table.cells` | Row/column count, numeric values, alignment intent |
| Charts | Category labels and `series.name` | Numeric `series.values`, chart type, embedded workbook assumptions |
| Images | `image.alt` descriptions | `src`, crop, size, position unless replacing media is requested |
| Shape text | Detected as `text` slots | Shape geometry and style |

Do not translate unsupported or non-visible objects: SmartArt internals, speaker notes, comments, animation labels, video/audio content, OLE objects, macros, or arbitrary embedded files.

### Step 4 — Build Translated PPTX

```bash
uv run python scripts/pptx_json_cli.py build <workspace>
```

Output: `<workspace>/exports/output.pptx`.

If translated text exceeds the original slot capacity, validation emits a warning and export automatically enables PowerPoint text autofit (`normAutofit`) with reduced `fontScale`. Do not manually resize boxes or move objects unless the user explicitly asks and the object is supported.

### Step 5 — Verify Translation

```bash
uv run python scripts/pptx_json_cli.py verify-pptx <workspace>/exports/output.pptx --old-terms <old...> --new-terms <new...>
```

Manually sanity-check: no source-language residue in visible slots, no accidental numeric changes, charts and tables still align, and long translated labels remain inside their original boxes.

## Failure Behavior

Stop and report if validation shows missing required slots, unknown slots, non-editable fields, invalid resource paths, stale bindings, or broken relationships.

Capacity overflow is not fatal for translation. Treat it as a layout-risk warning; the build will shrink text automatically, and severe cases may still need shorter translation wording.

## References

| File | Use |
| --- | --- |
| `references/workflow.md` | Full translation workflow, commands, rules, and verification |
| `references/manifest-json.md` | `template_manifest.json` slot contract |
| `references/content-json.md` | `deck_content.json` translation contract |
| `references/patch-plan-json.md` | Stable `patch_plan.json` contract, including text autofit |
| `references/ooxml-boundaries.md` | Translatable objects, preserved objects, and refusal boundaries |
