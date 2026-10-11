import importlib
import unittest

import numpy as np


class TestMapBiomasPeruChange(unittest.TestCase):
    def _load_module(self):
        try:
            return importlib.import_module("bin.factors.derive_peru_former_mapbiomas_change")
        except ModuleNotFoundError:
            self.fail("MapBiomas change module has not been implemented")

    def test_vegetation_loss_requires_a_vegetated_to_nonvegetated_transition(self):
        module = self._load_module()
        old = np.array([[12, 66, 68, 12, 12]], dtype="uint8")
        new = np.array([[25, 24, 68, 33, 30]], dtype="uint8")

        result = module.derive_change_masks(old, new)

        np.testing.assert_array_equal(
            result["vegetation_loss"],
            np.array([[1, 1, 0, 0, 0]], dtype="uint8"),
        )

    def test_bare_state_excludes_natural_desert_and_mining_classes(self):
        module = self._load_module()
        old = np.array([[68, 68, 68, 68, 68]], dtype="uint8")
        new = np.array([[25, 68, 29, 61, 30]], dtype="uint8")

        result = module.derive_change_masks(old, new)

        np.testing.assert_array_equal(
            result["anthropogenic_bare_state"],
            np.array([[1, 0, 0, 0, 0]], dtype="uint8"),
        )

    def test_built_and_agricultural_expansion_are_new_family_footprints(self):
        module = self._load_module()
        old = np.array([[68, 24, 12, 18, 30]], dtype="uint8")
        new = np.array([[24, 24, 18, 40, 24]], dtype="uint8")

        result = module.derive_change_masks(old, new)

        np.testing.assert_array_equal(
            result["built_up_expansion"],
            np.array([[1, 0, 0, 0, 0]], dtype="uint8"),
        )
        np.testing.assert_array_equal(
            result["agricultural_expansion"],
            np.array([[0, 0, 1, 0, 0]], dtype="uint8"),
        )

    def test_bv_combines_current_anthropogenic_bare_state_and_observed_loss(self):
        module = self._load_module()
        old = np.array([[68, 12, 68, 12]], dtype="uint8")
        new = np.array([[25, 24, 68, 30]], dtype="uint8")

        result = module.derive_change_masks(old, new)

        np.testing.assert_array_equal(
            result["bare_soil_vegetation_loss"],
            np.array([[1, 1, 0, 0]], dtype="uint8"),
        )

    def test_stable_classification_uses_three_year_pixel_majority(self):
        module = self._load_module()
        annual = np.array(
            [
                [[12, 24, 68]],
                [[12, 68, 68]],
                [[24, 24, 68]],
            ],
            dtype="uint8",
        )

        try:
            stable = module.stable_classification(annual)
        except AttributeError:
            self.fail("three-year stable classification has not been implemented")

        np.testing.assert_array_equal(stable, np.array([[12, 24, 68]], dtype="uint8"))


if __name__ == "__main__":
    unittest.main()
