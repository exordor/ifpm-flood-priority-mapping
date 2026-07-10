from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_exporter():
    path = ROOT / "bin/visualize/export_peru_raw_input_factor_maps.py"
    spec = importlib.util.spec_from_file_location("export_peru_raw_input_factor_maps", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PeruRawInputMapPaletteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_exporter()

    def test_physical_factors_use_variable_specific_sequential_palettes(self):
        specs = {item.slug: item for item in self.module.RASTER_SPECS}

        self.assertEqual(
            specs["rainfall_climatology"].colors,
            ("#eff3ff", "#c6dbef", "#9ecae1", "#6baed6", "#3182bd", "#08519c"),
        )
        self.assertEqual(
            specs["elevation"].colors,
            ("#006837", "#78c679", "#d9ef8b", "#fee08b", "#d8b365", "#8c510a"),
        )
        self.assertEqual(
            specs["upstream_area"].colors,
            ("#f6eff7", "#d0d1e6", "#a6bddb", "#67a9cf", "#1c9099", "#016c59"),
        )
        self.assertEqual(
            specs["ls_factor"].colors,
            ("#ffffd4", "#fee391", "#fec44f", "#fe9929", "#d95f0e", "#993404"),
        )

    def test_distance_maps_avoid_diverging_or_hazard_palettes(self):
        specs = {item.slug: item for item in self.module.VECTOR_DISTANCE_SPECS}

        self.assertEqual(
            specs["distance_to_roads"].colors,
            ("#f7f7f7", "#d9d9d9", "#bdbdbd", "#969696", "#636363", "#252525"),
        )
        self.assertEqual(
            specs["distance_to_ingemmet_small_mining"].colors,
            ("#f2f0f7", "#dadaeb", "#bcbddc", "#9e9ac8", "#756bb1", "#54278f"),
        )


if __name__ == "__main__":
    unittest.main()
