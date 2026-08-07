import importlib
import unittest

import numpy as np
from rasterio.transform import from_origin


class PeruMapBiomasChangeSensitivityTest(unittest.TestCase):
    def _load_module(self):
        try:
            return importlib.import_module(
                "bin.scenarios.run_peru_mapbiomas_change_sensitivity"
            )
        except ModuleNotFoundError:
            self.fail("MapBiomas change sensitivity runner has not been implemented")

    def test_be_combines_expansion_family_with_current_road_pressure(self):
        module = self._load_module()
        built = np.array([[0.2, 1.0]], dtype="float32")
        agriculture = np.array([[0.8, 0.0]], dtype="float32")
        road = np.array([[0.6, 0.4]], dtype="float32")

        result = module.build_supplementary_be(built, agriculture, road)

        np.testing.assert_allclose(result, np.array([[0.7, 0.7]], dtype="float32"))

    def test_supplementary_pim_retains_weights_and_ignores_mining(self):
        module = self._load_module()
        components = {
            "flood_hazard": np.array([[0.19]], dtype="float32"),
            "sediment": np.array([[0.495]], dtype="float32"),
            "land_cover_pressure": np.array([[0.7]], dtype="float32"),
            "bare_soil_vegetation_loss": np.array([[0.4]], dtype="float32"),
            "built_up_expansion": np.array([[0.2]], dtype="float32"),
            "agricultural_expansion": np.array([[0.8]], dtype="float32"),
            "road_access_proximity": np.array([[0.6]], dtype="float32"),
            "environmental": np.array([[0.8]], dtype="float32"),
            "socioeconomic": np.array([[0.9]], dtype="float32"),
            "mining_pressure": np.array([[1.0]], dtype="float32"),
        }

        result = module.calculate_supplementary_pim(components)

        self.assertAlmostEqual(float(result["be"][0, 0]), 0.7, places=6)
        self.assertAlmostEqual(float(result["land_use"][0, 0]), 0.595, places=6)
        self.assertAlmostEqual(float(result["pim"][0, 0]), 0.47725, places=6)

    def test_missing_supplementary_evidence_remains_unscored(self):
        module = self._load_module()
        components = {
            "flood_hazard": np.array([[0.2]], dtype="float32"),
            "sediment": np.array([[0.3]], dtype="float32"),
            "land_cover_pressure": np.array([[0.4]], dtype="float32"),
            "bare_soil_vegetation_loss": np.array([[np.nan]], dtype="float32"),
            "built_up_expansion": np.array([[0.0]], dtype="float32"),
            "agricultural_expansion": np.array([[0.0]], dtype="float32"),
            "road_access_proximity": np.array([[0.5]], dtype="float32"),
            "environmental": np.array([[0.6]], dtype="float32"),
            "socioeconomic": np.array([[0.7]], dtype="float32"),
        }

        result = module.calculate_supplementary_pim(components)

        self.assertTrue(np.isnan(result["land_use"][0, 0]))
        self.assertTrue(np.isnan(result["pim"][0, 0]))

    def test_comparison_footer_does_not_overlap_axis_labels(self):
        module = self._load_module()
        values = np.linspace(0.1, 0.9, 25, dtype="float32").reshape(5, 5)
        profile = {
            "transform": from_origin(780000, 8220000, 30, 30),
            "width": 5,
            "height": 5,
        }
        metrics = {"top20_jaccard": 0.9, "mean_absolute_delta": 0.05}

        try:
            figure, axes, footer = module.build_comparison_figure(
                values,
                values * 0.9,
                values * -0.1,
                np.zeros_like(values),
                profile,
                metrics,
            )
        except AttributeError:
            self.fail("comparison figure layout contract has not been implemented")

        figure.canvas.draw()
        renderer = figure.canvas.get_renderer()
        footer_box = footer.get_window_extent(renderer)
        label_bottom = min(
            axis.xaxis.label.get_window_extent(renderer).y0 for axis in axes.flat
        )
        self.assertLess(footer_box.y1 + 2.0, label_bottom)
        module.plt.close(figure)


if __name__ == "__main__":
    unittest.main()
