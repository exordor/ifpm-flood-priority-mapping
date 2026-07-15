# IFPM Conference Work Update PPT Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an editable conference draft PPTX that explains the complete IFPM workflow, completed results, and evidence gaps.

**Architecture:** A single JavaScript ES module will build a 14-slide 16:9 deck with `@oai/artifact-tool`. It will embed governed Peru and Zimbabwe report figures, use editable PowerPoint text and simple shapes for narrative structure, and export all QA renders to an external scratch workspace.

**Tech Stack:** Node.js, `@oai/artifact-tool`, bundled presentation rendering and overflow checks.

## Global Constraints

- Store the final internal presentation under `context/presentations/`.
- Keep generated source, previews, layouts, and QA ledgers outside the repository.
- Use Peru as the active main case and Zimbabwe as a secondary method comparison.
- Describe current maps as prototype or sensitivity results, never validated flood-risk products.
- Use existing governed figures and current manifests as evidence.
- Keep all audience-facing text editable and leave room for mentor additions.

---

### Task 1: Verify content and visual assets

**Files:**
- Read: `context/docs/research-map/RESEARCH_OVERVIEW.md`
- Read: `outputs/peru_report_figure_chain/manifest.csv`
- Read: `outputs/zimbabwe_report_figure_chain/manifest.csv`
- Create externally: `<scratch>/source-notes.txt`

**Interfaces:**
- Consumes: current research status, manifests, report figures, QGIS package manifest.
- Produces: a source-to-slide asset list with exact paths and evidence boundaries.

- [ ] **Step 1: Verify every planned visual exists**

Run `test -f` for the Peru board, Peru report figures, Zimbabwe board, Zimbabwe report figures, and QGIS package contact sheets.

- [ ] **Step 2: Extract current metrics**

Read current CSVs for coverage, weights, selected area, event co-location, and QGIS layer QA; record only values used in the slides.

- [ ] **Step 3: Write the external source note**

Record exact file paths, slide use, and claim boundary in `<scratch>/source-notes.txt`.

### Task 2: Build the editable deck

**Files:**
- Create externally: `<scratch>/tmp/build_ifpm_conference_update.mjs`
- Create: `context/presentations/IFPM_Conference_Work_Update_Draft_2026-07-15.pptx`

**Interfaces:**
- Consumes: the verified source-to-slide asset list.
- Produces: a 14-slide editable PPTX and per-slide PNG/layout renders.

- [ ] **Step 1: Initialize the artifact-tool workspace**

Run the bundled `setup_artifact_tool_workspace.mjs` against `<scratch>/tmp`.

- [ ] **Step 2: Implement the 14-slide narrative**

Use 16:9 slides, plain first-person copy, existing map images, editable titles and captions, and short evidence-boundary footers.

- [ ] **Step 3: Export the deck and QA artifacts**

Export the PPTX, individual slide PNGs, layout JSON, and a montage.

### Task 3: Validate and revise

**Files:**
- Inspect: `context/presentations/IFPM_Conference_Work_Update_Draft_2026-07-15.pptx`
- Create externally: `<scratch>/tmp/qa/qa-ledger.txt`

**Interfaces:**
- Consumes: the generated PPTX and renders.
- Produces: a corrected deck with no unintended overlap or unsupported claims.

- [ ] **Step 1: Run automated checks**

Run `slides_test.py` and scan all exported layout files for out-of-bounds objects.

- [ ] **Step 2: Inspect every rendered slide**

Review the montage and each full-size slide for cropping, wrapping, legibility, and map-caption consistency.

- [ ] **Step 3: Run two adversarial reviews**

Ask one reviewer to check scientific claims and evidence boundaries and another to check audience flow, layout, and editability. Fix all P1/P2 findings.

- [ ] **Step 4: Re-export and re-run checks**

Rebuild the PPTX after fixes and repeat automated and visual validation.
