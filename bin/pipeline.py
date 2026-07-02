#!/usr/bin/env python3
"""IFPM bin/ pipeline orchestrator.

A lightweight static-DAG orchestrator for the bin/ scripts. Scripts declare their
inputs and outputs as module-level ``INPUTS`` / ``OUTPUTS`` constants (lists of
Path objects); this orchestrator scans those declarations to build a dependency
graph and runs scripts in topological order.

Subcommands
-----------
    python bin/pipeline.py list                 list stages and scripts
    python bin/pipeline.py dot                  print a Graphviz DOT graph
    python bin/pipeline.py deps <script>        show direct upstream of a script
    python bin/pipeline.py run <stage>          run all scripts in a stage
    python bin/pipeline.py run --target <name>  run a script and its full upstream
    python bin/pipeline.py run --target <name> --no-deps  run only that script

Stage assignment
----------------
Scripts live under bin/ (flat, today) or bin/<stage>/ (after the stage-1
reorg). The stage is inferred from the subdirectory name, or — for flat scripts —
from a verb-prefix mapping that mirrors the 7 pipeline stages:

    acquire     download_, plan_, inventory_, intake_, check_data, discover_, extract_
    factors     preprocess_, derive_            (terrain/USLE factor derivation)
    criteria    build_                          (criteria-stack assembly)
    scenarios   run_                            (weighted-overlay scenarios)
    visualize   plot_                           (figure/board generation)
    package     prepare_, standardize_, export_, diagnose_
    investigate explore_, compute_, compare_, verify_

Scripts under bin/_archive/ and bin/_deprecated/ are ignored.

Idempotency
-----------
A script is considered up-to-date (and skipped) if ALL its declared OUTPUTS exist
and are newer than ALL its declared INPUTS. Missing INPUTS are allowed (they may
be raw downloads or outputs of scripts outside the declared set). Use --force to
re-run regardless.

Note: until scripts gain INPUTS/OUTPUTS declarations (stage 1), every script is
treated as a standalone node with no detected dependencies; the stage grouping and
run/list/dot commands still work.
"""

from __future__ import annotations

import argparse
import ast
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT: Path = Path(__file__).resolve().parents[1]
BIN: Path = ROOT / "bin"

# Stage classification by filename verb-prefix (for flat-layout scripts).
# Order defines the canonical pipeline flow.
STAGE_PREFIXES: list[tuple[str, tuple[str, ...]]] = [
    ("acquire", ("download_", "plan_", "inventory_", "intake_", "check_data", "discover_", "extract_")),
    ("factors", ("preprocess_", "derive_")),
    ("criteria", ("build_")),
    ("scenarios", ("run_",)),
    ("visualize", ("plot_",)),
    ("package", ("prepare_", "standardize_", "export_", "diagnose_", "check_v1_raster_grid")),
    ("investigate", ("explore_", "compute_", "compare_", "verify_")),
]

IGNORED_DIRS = {"_archive", "_deprecated", "_lib", "__pycache__"}


# ---------------------------------------------------------------------------
# Script discovery and stage classification
# ---------------------------------------------------------------------------

def classify_stage(name: str) -> str:
    """Infer the pipeline stage from a script's filename."""
    stem = name[:-3] if name.endswith(".py") else name
    for stage, prefixes in STAGE_PREFIXES:
        if any(stem == p or stem.startswith(p) for p in prefixes):
            return stage
    return "unsorted"


@dataclass
class Script:
    path: Path
    name: str          # filename without extension
    stage: str
    inputs: list[Path] = field(default_factory=list)
    outputs: list[Path] = field(default_factory=list)

    @property
    def rel(self) -> str:
        """Path relative to ROOT, for display."""
        try:
            return str(self.path.relative_to(ROOT))
        except ValueError:
            return str(self.path)


def discover_scripts() -> list[Script]:
    """Find all .py scripts under bin/, excluding ignored dirs and non-script files."""
    scripts: list[Script] = []
    # Flat layout: bin/*.py
    for p in sorted(BIN.glob("*.py")):
        if p.name in {"pipeline.py", "__init__.py"}:
            continue
        scripts.append(_make_script(p, p.stem))
    # Nested layout: bin/<stage>/*.py
    for subdir in sorted(BIN.iterdir()):
        if not subdir.is_dir() or subdir.name in IGNORED_DIRS:
            continue
        for p in sorted(subdir.glob("*.py")):
            if p.name == "__init__.py":
                continue
            scripts.append(_make_script(p, p.stem, subdir.name))
    return scripts


def _make_script(path: Path, name: str, stage_hint: str | None = None) -> Script:
    stage = stage_hint if stage_hint and stage_hint in {s for s, _ in STAGE_PREFIXES} else classify_stage(name)
    inputs, outputs = _scan_io(path)
    return Script(path=path, name=name, stage=stage, inputs=inputs, outputs=outputs)


def _scan_io(path: Path) -> tuple[list[Path], list[Path]]:
    """Parse a script's module-level INPUTS / OUTPUTS constants.

    Uses AST to read the literal list assigned to these names. Only Path(...)
    constructions or string literals are recognised. If the script has no such
    declarations, returns two empty lists.
    """
    try:
        tree = ast.parse(path.read_text())
    except SyntaxError:
        return [], []
    return _extract_lists(tree)


def _extract_lists(tree: ast.Module) -> tuple[list[Path], list[Path]]:
    """Extract INPUTS and OUTPUTS module-level assignments from an AST.

    Supports both list format (``[ROOT / "...", ...]``) and dict format
    (``{"key": ROOT / "...", ...}``) -- the latter is used by criteria-stack
    builders that need named criteria. For dicts, the values are extracted.
    """
    result: dict[str, list[Path]] = {"INPUTS": [], "OUTPUTS": []}
    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name) or target.id not in result:
                continue
            if isinstance(node.value, ast.Dict):
                # Dict format: extract values.
                result[target.id] = [
                    p for v in node.value.values if (p := _eval_path_expr(v)) is not None
                ]
            else:
                result[target.id] = _eval_path_list(node.value)
    return result["INPUTS"], result["OUTPUTS"]


def _eval_path_list(node: ast.AST) -> list[Path]:
    """Evaluate a list literal of Path(...) or string literals to Path objects.

    Recognises a common pattern: ``[ROOT / "outputs/..." / "x.tif"]`` where ROOT
    is already resolved to ROOT. Since we cannot resolve ROOT without executing,
    we look for string literals (possibly joined by / via BinOp) and reconstruct
    the path relative to ROOT.
    """
    if not isinstance(node, ast.List):
        return []
    paths: list[Path] = []
    for elt in node.elts:
        p = _eval_path_expr(elt)
        if p is not None:
            paths.append(p)
    return paths


def _eval_path_expr(node: ast.AST) -> Path | None:
    """Best-effort: reconstruct a Path from ROOT / "a" / "b" ... expressions.

    Handles:
      - bare string literals -> treated as project-root-relative
      - ROOT / "str" / "str" ... (BinOp chain) -> joined under ROOT
    """
    # Bare string literal.
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return ROOT / node.value
    # ROOT / "a" / "b" ...
    parts: list[str] = []
    cur = node
    while isinstance(cur, ast.BinOp) and isinstance(cur.op, ast.Div):
        right = cur.right
        if isinstance(right, ast.Constant) and isinstance(right.value, str):
            parts.append(right.value)
        else:
            return None  # non-string operand, give up
        cur = cur.left
    # cur is now the leftmost operand; accept ROOT (Name) or a string.
    if parts:
        if isinstance(cur, ast.Name) or isinstance(cur, ast.Constant):
            # Rebuild: leftmost is ROOT or a string root; parts are right-to-left.
            parts_rev = list(reversed(parts))
            base = ROOT
            if isinstance(cur, ast.Constant) and isinstance(cur.value, str):
                base = ROOT / cur.value
            return base.joinpath(*parts_rev) if parts_rev else base
    return None


# ---------------------------------------------------------------------------
# DAG construction and topological sort
# ---------------------------------------------------------------------------

def build_dag(scripts: list[Script]) -> dict[str, list[str]]:
    """Build an adjacency list: script_name -> [dependent script names].

    A dependency exists when script A's output is script B's input.
    """
    # Map output paths to producing scripts.
    output_to_script: dict[Path, str] = {}
    for s in scripts:
        for o in s.outputs:
            output_to_script[o] = s.name
    # For each script, find which of its inputs are produced by another script.
    deps: dict[str, list[str]] = {s.name: [] for s in scripts}
    for s in scripts:
        for i in s.inputs:
            producer = output_to_script.get(i)
            if producer and producer != s.name and producer not in deps[s.name]:
                deps[s.name].append(producer)
    return deps


def topo_sort(scripts: list[Script], deps: dict[str, list[str]]) -> list[Script]:
    """Topological sort of scripts respecting dependencies.

    Scripts with no declared I/O all sort as independent (alphabetical within stage).
    """
    by_name = {s.name: s for s in scripts}
    visited: set[str] = set()
    order: list[str] = []

    def visit(name: str, stack: set[str] | None = None) -> None:
        if name in visited:
            return
        if stack and name in stack:
            # Cycle: break it by visiting anyway (best-effort).
            return
        stack = (stack or set()) | {name}
        for dep in deps.get(name, []):
            visit(dep, stack)
        if name not in visited:
            visited.add(name)
            order.append(name)

    # Visit in stage order, then alphabetical, for deterministic output.
    stage_order = {stage: i for i, (stage, _) in enumerate(STAGE_PREFIXES)}
    stage_order["unsorted"] = len(STAGE_PREFIXES)
    for s in sorted(scripts, key=lambda x: (stage_order.get(x.stage, 99), x.name)):
        visit(s.name)

    return [by_name[n] for n in order if n in by_name]


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

def is_fresh(script: Script) -> bool:
    """A script is fresh (skip it) iff all outputs exist and are newer than all inputs."""
    if not script.outputs:
        return False  # no declared outputs -> never skip
    for o in script.outputs:
        if not o.exists():
            return False
    out_mtime = min(o.stat().st_mtime for o in script.outputs)
    for i in script.inputs:
        if i.exists() and i.stat().st_mtime > out_mtime:
            return False
    return True


def run_script(script: Script, force: bool = False) -> int:
    """Run a single script via subprocess. Returns exit code."""
    if not force and is_fresh(script):
        print(f"  [fresh] {script.rel}  (outputs newer than inputs)")
        return 0
    print(f"  [run]   {script.rel}")
    completed = subprocess.run([sys.executable, str(script.path)], cwd=str(ROOT))
    if completed.returncode != 0:
        print(f"  [FAIL]  {script.rel} (exit {completed.returncode})", file=sys.stderr)
    return completed.returncode


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------

def cmd_list(scripts: list[Script]) -> int:
    stages: dict[str, list[Script]] = {}
    for s in scripts:
        stages.setdefault(s.stage, []).append(s)
    stage_order = [st for st, _ in STAGE_PREFIXES] + ["unsorted"]
    for stage in stage_order:
        members = stages.get(stage, [])
        if not members:
            continue
        n_io = sum(1 for m in members if m.outputs)
        print(f"\n[{stage}]  {len(members)} scripts ({n_io} with declared I/O)")
        for m in sorted(members, key=lambda x: x.name):
            tag = ""
            if m.outputs:
                tag = f"  -> {len(m.outputs)} out"
            if m.inputs:
                tag += f"  <- {len(m.inputs)} in"
            print(f"    {m.name}{tag}")
    print(f"\nTotal: {len(scripts)} scripts across {len(stages)} stages")
    return 0


def cmd_dot(scripts: list[Script], deps: dict[str, list[str]]) -> int:
    print("digraph ifpm_pipeline {")
    print('  rankdir=LR;')
    # Group nodes by stage.
    stages: dict[str, list[str]] = {}
    for s in scripts:
        stages.setdefault(s.stage, []).append(s.name)
    for stage, names in stages.items():
        print(f'  subgraph "cluster_{stage}" {{')
        print(f'    label="{stage}";')
        for n in names:
            print(f'    "{n}";')
        print("  }")
    # Edges: producer -> consumer.
    for consumer, producers in deps.items():
        for producer in producers:
            print(f'  "{producer}" -> "{consumer}";')
    print("}")
    return 0


def cmd_deps(scripts: list[Script], deps: dict[str, list[str]], name: str) -> int:
    by_name = {s.name: s for s in scripts}
    if name not in by_name:
        print(f"error: script '{name}' not found", file=sys.stderr)
        return 1
    producers = deps.get(name, [])
    print(f"{name} (stage: {by_name[name].stage})")
    print(f"  direct upstream: {producers or 'none'}")
    # Transitive closure.
    seen: set[str] = set()
    stack = list(producers)
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        stack.extend(deps.get(n, []))
    if seen:
        print(f"  full upstream: {sorted(seen)}")
    return 0


def cmd_run(
    scripts: list[Script],
    deps: dict[str, list[str]],
    target: str | None,
    stage: str | None,
    no_deps: bool,
    force: bool,
) -> int:
    by_name = {s.name: s for s in scripts}
    if target:
        if target not in by_name:
            print(f"error: script '{target}' not found", file=sys.stderr)
            return 1
        if no_deps:
            order = [by_name[target]]
        else:
            # Resolve full upstream + target, in topo order.
            full = {target}
            stack = list(deps.get(target, []))
            while stack:
                n = stack.pop()
                if n in full:
                    continue
                full.add(n)
                stack.extend(deps.get(n, []))
            order = [s for s in topo_sort(scripts, deps) if s.name in full]
    elif stage:
        order = [s for s in topo_sort(scripts, deps) if s.stage == stage]
        if not order:
            print(f"error: stage '{stage}' has no scripts", file=sys.stderr)
            return 1
    else:
        print("error: provide --target <name> or a stage name", file=sys.stderr)
        return 1

    print(f"Running {len(order)} script(s):")
    failures = 0
    for s in order:
        rc = run_script(s, force=force)
        if rc != 0:
            failures += 1
            print(f"  stopping: {s.name} failed", file=sys.stderr)
            break
    print(f"\nDone: {len(order) - failures} ok, {failures} failed")
    return 1 if failures else 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="pipeline",
        description="IFPM bin/ pipeline orchestrator (static DAG).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="list stages and scripts")

    sub.add_parser("dot", help="print a Graphviz DOT dependency graph")

    p_deps = sub.add_parser("deps", help="show upstream dependencies of a script")
    p_deps.add_argument("name", help="script name (without .py)")

    p_run = sub.add_parser("run", help="run scripts in dependency order")
    p_run.add_argument("stage", nargs="?", help="stage name (acquire/factors/...)")
    p_run.add_argument("--target", help="run this script and its full upstream")
    p_run.add_argument("--no-deps", action="store_true", help="run only the target, not its upstream")
    p_run.add_argument("--force", action="store_true", help="re-run even if outputs are fresh")

    args = parser.parse_args()

    scripts = discover_scripts()
    deps = build_dag(scripts)

    if args.command == "list":
        return cmd_list(scripts)
    if args.command == "dot":
        return cmd_dot(scripts, deps)
    if args.command == "deps":
        return cmd_deps(scripts, deps, args.name)
    if args.command == "run":
        return cmd_run(scripts, deps, args.target, args.stage, args.no_deps, args.force)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
