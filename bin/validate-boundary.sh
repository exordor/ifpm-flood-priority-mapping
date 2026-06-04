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

private_pattern='../context|../data|../outputs|/Users/|/home/|/Volumes/|C:\\Users|\\.lark-cli|\\.feishu-cli'
private_hits="$(grep_tool "$private_pattern" "$DELIVERABLE")"
if [[ -n "$private_hits" ]]; then
  printf '%s\n' "$private_hits"
  fail "private references found in deliverable repo"
fi

symlink_hits="$(find "$DELIVERABLE" -type l -print 2>/dev/null || true)"
if [[ -n "$symlink_hits" ]]; then
  printf '%s\n' "$symlink_hits"
  fail "symlinks in deliverable repo require manual review"
fi

if [[ "$FAILURES" -gt 0 ]]; then
  echo "validation failed with $FAILURES issue(s)" >&2
  exit 1
fi

echo "validation completed"
