# QGIS External Overlay Group Standardization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give Secocha and Goslar QGIS projects the same `7. External validation and overlays` group while retaining only source-backed regional layers.

**Architecture:** Keep each existing `LayerSpec` and data path unchanged. Standardize only the Secocha and Goslar group contract, then rebuild both packages from their existing builders. A cross-builder test binds the exact group name and the region-specific overlay keys. Legacy Peru/Zimbabwe remain outside this work package.

**Tech Stack:** Python `unittest`, PyQGIS package builders, QGZ/CSV package validation.

## Global Constraints

- Do not add empty or fabricated historical-event layers.
- Mining and historical-event evidence remain external overlays unless an existing manifest explicitly says otherwise.
- Preserve existing palettes, layer roles, data paths, visibility, and claim levels.
- Do not stage or commit the dirty workspace automatically.
- Rebuild outputs only under `outputs/` and portable exports only under ignored `exports/`.

---

### Task 1: Bind the shared overlay-group contract with a failing test

**Files:**
- Create: `tests/test_qgis_external_overlay_group_standardization.py`
- Test: `tests/test_qgis_external_overlay_group_standardization.py`

**Interfaces:**
- Consumes: `GOSLAR_LAYERS` and Secocha wrapper `layers`.
- Produces: exact required group string `7. External validation and overlays` for explicit overlay keys.

- [x] **Step 1: Write the failing test**

```python
EXPECTED_GROUP = "7. External validation and overlays"

def test_region_overlay_layers_use_one_group():
    for layers, keys in REGION_OVERLAY_KEYS:
        by_key = {layer.key: layer for layer in layers}
        assert all(by_key[key].group == EXPECTED_GROUP for key in keys)
```

- [x] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m unittest tests.test_qgis_external_overlay_group_standardization -v`

Expected: FAIL because Secocha uses `7. Historical event and mining overlays` and Goslar uses `7. Context and evidence`.

### Task 2: Apply the minimal group-name change

**Files:**
- Modify: `bin/package/build_peru_secocha_qgis_project_package.py`
- Modify: `bin/package/build_goslar_qgis_project_package.py`
- Modify: `tests/test_goslar_qgis_project_package.py`

**Interfaces:**
- Consumes: existing `LayerSpec.group` strings.
- Produces: the shared exact string `7. External validation and overlays` without changing layer membership.

- [x] **Step 1: Replace only overlay group strings in the two builders**

```python
EXTERNAL_OVERLAY_GROUP = "7. External validation and overlays"
```

Use this constant for the existing Secocha overlay layers and Goslar context/mining layers.

- [x] **Step 2: Update the existing Goslar group-order assertion**

Replace `7. Context and evidence` with `7. External validation and overlays`.

- [x] **Step 3: Run focused tests**

Run: `.venv/bin/python -m unittest tests.test_qgis_external_overlay_group_standardization tests.test_goslar_qgis_project_package tests.test_peru_secocha_chain -v`

Expected: PASS after regenerated-package-dependent tests are refreshed in Task 3.

### Task 3: Rebuild and validate the two QGIS packages

**Files:**
- Modify outputs: `outputs/peru_secocha_qgis_project_package/`
- Modify outputs: `outputs/goslar_qgis_project_package/`
- Modify exports: corresponding portable package directories under `exports/`

**Interfaces:**
- Consumes: standardized builder configurations.
- Produces: QGZ projects and manifests whose overlay rows use the shared group name.

- [x] **Step 1: Build Secocha and Goslar packages**

Run:

```text
.venv/bin/python bin/package/build_peru_secocha_qgis_project_package.py
.venv/bin/python bin/package/build_goslar_qgis_project_package.py
```

- [x] **Step 2: Run focused tests and QGIS readback validation**

Run: `.venv/bin/python -m unittest tests.test_qgis_external_overlay_group_standardization tests.test_goslar_qgis_project_package tests.test_peru_secocha_chain -v`

Expected: all tests pass, all manifests load, and portable hashes match.

- [x] **Step 3: Run workspace diff validation**

Run: `git diff --check`

Expected: no whitespace errors.

### Task 4: Adversarial review

**Files:**
- Review only: the two builders, test, manifests, and generated QGZ packages.

**Interfaces:**
- Consumes: completed implementation and regenerated outputs.
- Produces: severity-ranked engineering and scientific/semantic findings.

- [x] **Step 1: Request independent engineering and semantic reviews**

Review questions: Do Secocha and Goslar expose the same overlay group? Is Goslar's missing historical-event layer represented honestly? Were palette, scoring, paths, visibility, and claim levels preserved?

- [x] **Step 2: Fix any P1/P2 findings and rerun the focused test command**

- [x] **Step 3: Hand off exact Secocha/Goslar QGIS package locations and regional differences**
