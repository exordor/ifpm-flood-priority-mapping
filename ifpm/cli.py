"""Command line: ``python -m ifpm run|verify|list``.

    python -m ifpm list
    python -m ifpm run <area> [--extent NAME|all] [--step S[,S...]] [--out DIR]
    python -m ifpm verify <area> [--extent NAME|all] [--out DIR]

``run`` writes under DIR (default outputs/_rerun/<area>) using the same relative paths as
the current outputs, so the current outputs are never overwritten. ``verify`` compares
DIR with the current outputs. Extents run in config order: later Goslar extents read the
earlier ones from DIR when present, else from the current outputs.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .config import ROOT, Config, areas


def _extents(cfg: Config, name: str) -> list[str]:
    if name == "all":
        return cfg.extents
    cfg.extent(name)  # exits with the list of choices when unknown
    return [name]


def _out_dir(area: str, out: str | None) -> Path:
    path = Path(out).resolve() if out else ROOT / "outputs" / "_rerun" / area
    if path == ROOT.resolve():
        raise SystemExit("--out must not be the workspace root; the current outputs are never overwritten")
    if (ROOT / "outputs" / "peru_former_pim_chain").resolve() in [path, *path.parents]:
        raise SystemExit("--out must not be inside the frozen outputs/peru_former_pim_chain/")
    return path


def cmd_list(_args) -> int:
    for area in areas():
        cfg = Config(area)
        for name in cfg.extents:
            ext = cfg.extent(name)
            print(f"{area:<8} {name:<14} {ext['method']:<10} {' '.join(ext['stages'])}")
    return 0


def cmd_run(args) -> int:
    from . import chain, expanded, rescore
    cfg = Config(args.area)
    out = _out_dir(args.area, args.out)
    steps = args.step.split(",") if args.step else None
    names = _extents(cfg, args.extent)
    if steps:
        known = {s for name in names for s in cfg.extent(name)["stages"]}
        unknown = [s for s in steps if s not in known]
        if unknown:
            raise SystemExit(f"unknown step(s) {unknown}; stages of {names}: {sorted(known)}")
    runners = {"basin": chain.run_basin, "abzucht": expanded.run_abzucht,
               "multiriver": expanded.run_multiriver, "rescore": rescore.run_rescore}
    for name in names:
        ext = cfg.extent(name)
        if steps and not set(steps) & set(ext["stages"]):
            continue
        print(f"== {args.area} / {name} -> {out}", flush=True)
        runners[ext["method"]](cfg, name, out, steps)
    return 0


def cmd_verify(args) -> int:
    from .verify import verify
    cfg = Config(args.area)
    ok = verify(args.area, _out_dir(args.area, args.out), _extents(cfg, args.extent))
    return 0 if ok else 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m ifpm", description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="list areas, extents and their stages").set_defaults(func=cmd_list)
    for name, func, text in [("run", cmd_run, "run the chain into a separate output root"),
                             ("verify", cmd_verify, "compare a rerun with the current outputs")]:
        p = sub.add_parser(name, help=text)
        p.add_argument("area", choices=areas())
        p.add_argument("--extent", default="all", help="extent name from configs/<area>.yaml, or 'all' (default)")
        p.add_argument("--out", help="rerun root (default outputs/_rerun/<area>)")
        if name == "run":
            p.add_argument("--step", help="comma-separated stage names; default all stages of the extent")
        p.set_defaults(func=func)
    args = parser.parse_args(argv)
    return args.func(args)
