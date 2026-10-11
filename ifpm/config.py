"""Read configs/<area>.yaml and configs/datasets.yaml.

``Config`` is a thin wrapper: the YAML is used as plain dicts, plus a few helpers that
turn dataset ids into paths under the workspace root.
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "configs"


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def areas() -> list[str]:
    """Area names that have a config file (everything except datasets.yaml)."""
    return sorted(p.stem for p in CONFIG_DIR.glob("*.yaml") if p.stem != "datasets")


class Config:
    def __init__(self, area: str, root: Path = ROOT, config_dir: Path = CONFIG_DIR):
        path = config_dir / f"{area}.yaml"
        if not path.exists():
            raise SystemExit(f"no config for area '{area}' ({path}); choose from {areas()}")
        self.root = root
        self.area = area
        self.data = load_yaml(path)
        self.datasets = load_yaml(config_dir / "datasets.yaml")

    def __getitem__(self, key):
        return self.data[key]

    def get(self, key, default=None):
        return self.data.get(key, default)

    @property
    def extents(self) -> list[str]:
        return list(self.data["extents"])

    def extent(self, name: str) -> dict:
        if name not in self.data["extents"]:
            raise SystemExit(f"unknown extent '{name}' for {self.area}; choose from {self.extents}")
        return self.data["extents"][name]

    def entry(self, dataset_id: str) -> dict:
        if dataset_id not in self.datasets:
            raise KeyError(f"dataset id '{dataset_id}' is not in configs/datasets.yaml")
        return self.datasets[dataset_id]

    def path(self, dataset_id: str, **fields) -> Path:
        """Absolute path of a dataset; ``fields`` fill placeholders such as {year}."""
        return self.root / self.entry(dataset_id)["path"].format(**fields)

    def layer(self, dataset_id: str):
        return self.entry(dataset_id).get("layer")

    def manifest_path(self, dataset_id: str) -> Path:
        return self.root / self.entry(dataset_id)["manifest"]
