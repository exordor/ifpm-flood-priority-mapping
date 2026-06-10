#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DELIVERABLE="ifpm-flood-pipeline"
FAILURES=0

fail() {
  echo "ERROR: $*" >&2
  FAILURES=$((FAILURES + 1))
}

grep_tool() {
  local pattern="$1"
  shift
  if command -v rg >/dev/null 2>&1; then
    rg -n "$pattern" "$@" 2>/dev/null || true
  else
    grep -RInE "$pattern" "$@" 2>/dev/null || true
  fi
}

find_data_artifacts() {
  find context "$DELIVERABLE" \
    \( -path "$DELIVERABLE/.git" \
    -o -path "$DELIVERABLE/.git/*" \
    -o -path "$DELIVERABLE/.venv" \
    -o -path "$DELIVERABLE/.venv/*" \
    -o -path "$DELIVERABLE/.pytest_cache" \
    -o -path "$DELIVERABLE/.pytest_cache/*" \
    -o -path "$DELIVERABLE/.ruff_cache" \
    -o -path "$DELIVERABLE/.ruff_cache/*" \
    -o -path "$DELIVERABLE/__pycache__" \
    -o -path "$DELIVERABLE/__pycache__/*" \
    \) -prune -o -type f \
    \( -iname '*.tif' \
    -o -iname '*.tiff' \
    -o -iname '*.geotiff' \
    -o -iname '*.shp' \
    -o -iname '*.shx' \
    -o -iname '*.dbf' \
    -o -iname '*.prj' \
    -o -iname '*.cpg' \
    -o -iname '*.gpkg' \
    -o -iname '*.geojson' \
    -o -iname '*.kml' \
    -o -iname '*.kmz' \
    -o -iname '*.nc' \
    -o -iname '*.grib' \
    -o -iname '*.grb' \
    -o -iname '*.hdf' \
    -o -iname '*.h5' \
    -o -iname '*.parquet' \
    -o -iname '*.zip' \
    -o -iname '*.tar' \
    -o -iname '*.tar.gz' \
    -o -iname '*.7z' \
    \) -print 2>/dev/null | while IFS= read -r path; do
    case "$path" in
      "$DELIVERABLE/tests/fixtures/synthetic/"*|"$DELIVERABLE/examples/synthetic/"*)
        ;;
      *)
        printf '%s\n' "$path"
        ;;
    esac
  done
}

find_reviewable_symlinks() {
  find "$DELIVERABLE" \
    \( -path "$DELIVERABLE/.git" \
    -o -path "$DELIVERABLE/.git/*" \
    -o -path "$DELIVERABLE/.venv" \
    -o -path "$DELIVERABLE/.venv/*" \
    -o -path "$DELIVERABLE/.pytest_cache" \
    -o -path "$DELIVERABLE/.pytest_cache/*" \
    -o -path "$DELIVERABLE/.ruff_cache" \
    -o -path "$DELIVERABLE/.ruff_cache/*" \
    \) -prune -o -type l -print 2>/dev/null || true
}

cd "$WORKSPACE"

echo "== root git boundary =="
root_top="$(git rev-parse --show-toplevel)"
printf 'root git top-level: %s\n' "$root_top"
if [[ "$root_top" != "$WORKSPACE" ]]; then
  fail "workspace is not the root git top-level"
fi

git status --short

if ! git check-ignore -v "$DELIVERABLE/" data/ outputs/ exports/ tmp/ .tmp/ .env; then
  fail "expected local/output/deliverable paths are not all ignored"
fi

if [[ -n "$(git ls-files -s "$DELIVERABLE" 2>/dev/null || true)" ]]; then
  fail "root repo tracks $DELIVERABLE path or gitlink"
fi

if [[ -f .gitmodules ]]; then
  fail ".gitmodules exists; submodule use requires explicit review"
fi

echo "== deliverable repo =="
deliverable_top="$(git -C "$DELIVERABLE" rev-parse --show-toplevel)"
printf 'deliverable git top-level: %s\n' "$deliverable_top"
if [[ "$deliverable_top" != "$WORKSPACE/$DELIVERABLE" ]]; then
  fail "deliverable repo top-level is unexpected"
fi

git -C "$DELIVERABLE" status --short

private_pattern='../context|../data|../outputs|'
private_pattern+='/User'
private_pattern+='s/|/home/|/Volumes/|C:\\Users|\\.lark-cli|\\.feishu-cli'
private_hits="$(
  git -C "$DELIVERABLE" ls-files -z |
    while IFS= read -r -d '' file; do
      path="$DELIVERABLE/$file"
      [[ -f "$path" ]] || continue
      grep_tool "$private_pattern" "$path"
    done
)"
if [[ -n "$private_hits" ]]; then
  printf '%s\n' "$private_hits"
  fail "private references found in deliverable repo"
fi

misplaced_data_hits="$(find_data_artifacts)"
if [[ -n "$misplaced_data_hits" ]]; then
  printf '%s\n' "$misplaced_data_hits"
  fail "GIS/archive data artifacts found outside approved data or synthetic paths"
fi

symlink_hits="$(find_reviewable_symlinks)"
if [[ -n "$symlink_hits" ]]; then
  printf '%s\n' "$symlink_hits"
  fail "symlinks in deliverable repo require manual review"
fi

if [[ "$FAILURES" -gt 0 ]]; then
  echo "validation failed with $FAILURES issue(s)" >&2
  exit 1
fi

echo "validation completed"
