from __future__ import annotations

import importlib.util
import sys
import tempfile
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PIPELINE_PATH = ROOT / "bin/pipeline.py"


def load_pipeline():
    spec = importlib.util.spec_from_file_location("ifpm_pipeline_safety", PIPELINE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {PIPELINE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["ifpm_pipeline_safety"] = module
    spec.loader.exec_module(module)
    return module


class PipelineSafetyTest(unittest.TestCase):
    def test_network_dependency_is_removed_without_explicit_permission(self):
        pipeline = load_pipeline()
        network = pipeline.Script(Path("network.py"), "network", "acquire")
        local = pipeline.Script(Path("local.py"), "local", "criteria")

        selected = pipeline.apply_network_policy(
            [network, local],
            network_script_names={"network"},
            allow_network=False,
            target="local",
        )

        self.assertEqual([script.name for script in selected], ["local"])

    def test_direct_network_target_requires_explicit_permission(self):
        pipeline = load_pipeline()
        network = pipeline.Script(Path("network.py"), "network", "acquire")

        with self.assertRaises(PermissionError):
            pipeline.apply_network_policy(
                [network],
                network_script_names={"network"},
                allow_network=False,
                target="network",
            )

    def test_script_mtime_participates_in_freshness(self):
        pipeline = load_pipeline()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "input.txt"
            script_path = root / "step.py"
            output = root / "output.txt"
            source.write_text("input", encoding="utf-8")
            script_path.write_text("print('old')\n", encoding="utf-8")
            time.sleep(0.01)
            output.write_text("output", encoding="utf-8")
            step = pipeline.Script(script_path, "step", "criteria", [source], [output])
            self.assertTrue(pipeline.is_fresh(step))

            time.sleep(0.01)
            script_path.write_text("print('new')\n", encoding="utf-8")
            self.assertFalse(pipeline.is_fresh(step))

    def test_missing_declared_input_is_not_fresh(self):
        pipeline = load_pipeline()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script_path = root / "step.py"
            output = root / "output.txt"
            script_path.write_text("print('step')\n", encoding="utf-8")
            output.write_text("output", encoding="utf-8")
            step = pipeline.Script(
                script_path,
                "step",
                "criteria",
                [root / "missing.txt"],
                [output],
            )
            self.assertFalse(pipeline.is_fresh(step))


if __name__ == "__main__":
    unittest.main()
