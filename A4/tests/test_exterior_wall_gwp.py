"""Tests for the exterior wall GWP analysis.

Run from the A4 folder:  python -m unittest discover -s tests
They build a tiny IFC (one exterior and one interior wall) so no real model is needed.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import ifcopenshell
import ifcopenshell.api.material
import ifcopenshell.api.pset
import ifcopenshell.api.root
import ifcopenshell.api.unit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from exterior_wall_gwp.src.main import analyse  # noqa: E402
from runall import save_result  # noqa: E402


def tiny_model():
    """One exterior wall (100 mm brick, 10 m x 3 m) and one interior wall."""
    model = ifcopenshell.file(schema="IFC4")
    ifcopenshell.api.root.create_entity(model, ifc_class="IfcProject")
    ifcopenshell.api.unit.assign_unit(model)  # millimetres
    brick = ifcopenshell.api.material.add_material(model, name="Brick, Common(yellow)")
    layers = ifcopenshell.api.material.add_material_set(model, name="Brick", set_type="IfcMaterialLayerSet")
    layer = ifcopenshell.api.material.add_layer(model, layer_set=layers, material=brick)
    ifcopenshell.api.material.edit_layer(model, layer=layer, attributes={"LayerThickness": 100.0})
    for external in (True, False):
        wall = ifcopenshell.api.root.create_entity(model, ifc_class="IfcWall")
        ifcopenshell.api.material.assign_material(model, products=[wall], type="IfcMaterialLayerSet",
                                                  material=layers)
        pset = ifcopenshell.api.pset.add_pset(model, product=wall, name="Pset_WallCommon")
        ifcopenshell.api.pset.edit_pset(model, pset=pset, properties={"IsExternal": external})
        qto = ifcopenshell.api.pset.add_qto(model, product=wall, name="Qto_WallBaseQuantities")
        ifcopenshell.api.pset.edit_qto(model, qto=qto, properties={"Length": 10000.0, "Height": 3000.0})
    return model


class ExteriorWallGwpTests(unittest.TestCase):
    def test_only_the_exterior_wall_is_counted(self):
        result = analyse(tiny_model(), area=100.0)
        brick = result["materials"]["Brick, Not red"]
        self.assertAlmostEqual(brick["volume"], 0.1 * 10 * 3)          # 3 m3, interior wall excluded
        self.assertAlmostEqual(result["gwp_total"], 3 * brick["gwp_factor"])
        self.assertAlmostEqual(result["gwp_m2_year"], result["gwp_total"] / (100.0 * 50))

    def test_result_can_be_saved_as_json(self):
        result = analyse(tiny_model(), area=100.0)
        with tempfile.TemporaryDirectory() as directory:
            output = save_result(result, directory)
            self.assertEqual(json.loads(output.read_text())["floor_area"], 100.0)

    def test_import_has_no_model_loading_or_output_side_effects(self):
        with tempfile.TemporaryDirectory() as directory:
            process = subprocess.run(
                [sys.executable, "-B", "-c",
                 f"import sys; sys.path.insert(0, {str(ROOT)!r}); import exterior_wall_gwp.src.main, runall"],
                cwd=directory, capture_output=True, text=True,
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual(process.stdout, "")


if __name__ == "__main__":
    unittest.main()
