# AIGC Background Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Chinese PPTX deck about AIGC development background from the provided SWO template and export a final editable presentation.

**Architecture:** Initialize a template workspace with `pptx-translate-skill`, write slot-safe content into `deck_content.json`, run the template build pipeline, then verify the exported PPTX has the intended replacement text and no obvious template leftovers in editable slots.

**Tech Stack:** Python CLI via `uv`, `pptx-translate-skill`, JSON content contract, PowerPoint template package export

---

### Task 1: Initialize Template Workspace

**Files:**

- Create: `workspaces/aigc-background-2026/`
- Read: `skills/pptx-translate-skill/scripts/pptx_json_cli.py`

**Step 1: Run environment setup**

Run: `uv run python scripts/pptx_json_cli.py setup`

Expected: environment check passes and uv/python availability is confirmed.

**Step 2: Initialize the workspace from the source template**

Run: `uv run python scripts/pptx_json_cli.py init '/Users/tianjie.li/Downloads/SWO Template-1775543916744.pptx' -w '/Users/tianjie.li/pptx-json-engine/workspaces/aigc-background-2026'`

Expected: source PPTX is copied and `template_manifest.json` plus `deck_content.skeleton.json` are created.

### Task 2: Map Story To Template Slots

**Files:**

- Modify: `workspaces/aigc-background-2026/deck_content.json`
- Read: `workspaces/aigc-background-2026/template_manifest.json`

**Step 1: Review slot capacities**

Run: `uv run python scripts/pptx_json_cli.py inspect-manifest '/Users/tianjie.li/pptx-json-engine/workspaces/aigc-background-2026' --for-ai`

Expected: each template slide lists editable text, image, and table slots with capacity constraints.

**Step 2: Write the deck content**

Populate slides for cover, section overview, concept framing, timeline, drivers, value chain, applications, landscape, trends, and closing while staying within each slot capacity.

**Step 3: Save the final content JSON**

Expected: `deck_content.json` is valid JSON and uses only declared slot ids.

### Task 3: Build And Verify The Deck

**Files:**

- Read: `workspaces/aigc-background-2026/deck_content.json`
- Output: `workspaces/aigc-background-2026/exports/aigc-development-background.pptx`

**Step 1: Build the PPTX**

Run: `uv run python scripts/pptx_json_cli.py build '/Users/tianjie.li/pptx-json-engine/workspaces/aigc-background-2026' -c '/Users/tianjie.li/pptx-json-engine/workspaces/aigc-background-2026/deck_content.json' -o '/Users/tianjie.li/pptx-json-engine/workspaces/aigc-background-2026/exports/aigc-development-background.pptx'`

Expected: validation, patch compilation, and PPTX export all succeed.

**Step 2: Verify visible text replacement**

Run: `uv run python scripts/pptx_json_cli.py verify-pptx '/Users/tianjie.li/pptx-json-engine/workspaces/aigc-background-2026/exports/aigc-development-background.pptx' --old-terms 'Transformation. All in one.' 'Performance Assessment' 'Next Steps' 'Get in touch' --new-terms 'AIGC 发展背景' '概念与边界' '未来三大趋势判断' 'Thank You'`

Expected: old editable text is not found where replaced, and key new terms are present.

### Task 4: Deliverable Review

**Files:**

- Final: `workspaces/aigc-background-2026/exports/aigc-development-background.pptx`
- Supporting: `docs/plans/2026-05-22-aigc-background-design.md`

**Step 1: Confirm final output path**

Check that the exported PPTX exists and is non-empty.

**Step 2: Report outcome**

Summarize the deck structure, output location, and any residual limitations such as preserved template imagery.
