"""
CAPT - Capture: "What information do we have?"

Reads from the IFC model:
  * the exterior walls (grouped later by wall type),
  * the material layers of each wall (material name + thickness),
  * the area of each wall,
  * the floor area of the building (reference area for BR18),
and reads BR18 Table 7 (generic emission data) from Excel.
"""
import re
from pathlib import Path

import pandas as pd
import ifcopenshell.util.element as element_util
import ifcopenshell.util.unit as unit_util


# ----------------------------------------------------------------------------
# Building elements
# ----------------------------------------------------------------------------
def CAPT_EXTERIOR_WALLS(model):
    """All IfcWall (incl. IfcWallStandardCase) with Pset_WallCommon.IsExternal = True.
    get_psets() also returns properties inherited from the wall type."""
    walls = []
    for wall in model.by_type("IfcWall"):
        if element_util.get_psets(wall).get("Pset_WallCommon", {}).get("IsExternal") is True:
            walls.append(wall)
    return walls


ROOF_WORDS = ("roof", "tag ", "tagterrasse", "tagdæk")


def _named_as_roof(slab):
    """A slab whose TYPE name says 'roof' (e.g. 'Floor:Rooftop terrace') is not a floor."""
    name = CAPT_TYPE_NAME(slab).lower()
    return any(w in name for w in ROOF_WORDS)


def CAPT_FLOORS(model):
    """Floor slabs (PredefinedType FLOOR or BASESLAB, not roof terraces).
    Only used as a fallback for the floor area when the model has no IfcSpace areas."""
    return [s for s in model.by_type("IfcSlab")
            if element_util.get_predefined_type(s) in ("FLOOR", "BASESLAB")
            and not _named_as_roof(s)]


def CAPT_ELEMENTS(model):
    """{building part: [elements]}. The tool is scoped to exterior walls only;
    the dict form is kept so other parts could be added later."""
    return {"Exterior wall": CAPT_EXTERIOR_WALLS(model)}


def CAPT_TYPE_NAME(element):
    """Name of the element *type* (e.g. 'Basic Wall:Exterior - Brick on Mtl. Stud').
    Uses IfcRelDefinesByType when present, otherwise ObjectType/Name with a trailing
    Revit id (':123456') removed so that elements of the same type are grouped."""
    element_type = element_util.get_type(element)
    if element_type is not None and element_type.Name:
        return element_type.Name
    name = element.ObjectType or element.Name or f"Unnamed #{element.id()}"
    return re.sub(r":\d+$", "", name)


# ----------------------------------------------------------------------------
# Material layers
# ----------------------------------------------------------------------------
def _layer_set(element):
    material = element_util.get_material(element)
    if material is None:
        return None
    if material.is_a("IfcMaterialLayerSetUsage"):
        return material.ForLayerSet
    if material.is_a("IfcMaterialLayerSet"):
        return material
    return None


def CAPT_LAYERS(model, element):
    """Material layers of an element -> [{"material", "thickness_m"}].
    Thickness is converted from the project length unit to metres.
    An element with a single IfcMaterial (no layer set) returns one layer whose
    thickness is taken from the quantity Width (walls) / Depth (slabs) if available."""
    scale = unit_util.calculate_unit_scale(model)  # project length unit -> m
    layer_set = _layer_set(element)
    if layer_set is not None:
        return [{
            "material": layer.Material.Name if layer.Material else "Unnamed material",
            "thickness_m": float(layer.LayerThickness or 0.0) * scale,
        } for layer in layer_set.MaterialLayers]

    material = element_util.get_material(element)
    if material is not None and material.is_a("IfcMaterial"):
        qto = _quantities(element)
        thickness = qto.get("Width") or qto.get("Depth") or qto.get("Thickness")
        return [{
            "material": material.Name,
            "thickness_m": float(thickness) * scale if thickness else None,
        }]
    return []


# ----------------------------------------------------------------------------
# Areas
# ----------------------------------------------------------------------------
def _quantities(element):
    qtos = element_util.get_psets(element, qtos_only=True)
    merged = {}
    for name in ("Qto_WallBaseQuantities", "Qto_SlabBaseQuantities",
                 "Qto_RoofBaseQuantities", "BaseQuantities"):
        merged.update({k: v for k, v in qtos.get(name, {}).items() if isinstance(v, (int, float))})
    return merged


def CAPT_ELEMENT_AREA(model, element):
    """Area of one wall (or slab) element in m2 -> (area, source).
    Walls: NetSideArea -> GrossSideArea. Slabs/roofs: NetArea -> GrossArea.
    Fallback: NetVolume / Width (or Depth)."""
    length = unit_util.calculate_unit_scale(model, "LENGTHUNIT")
    area = unit_util.calculate_unit_scale(model, "AREAUNIT")
    volume = unit_util.calculate_unit_scale(model, "VOLUMEUNIT")
    q = _quantities(element)

    for key in ("NetSideArea", "GrossSideArea", "NetArea", "GrossArea"):
        if q.get(key):
            return float(q[key]) * area, key
    thickness = q.get("Width") or q.get("Depth")
    if q.get("NetVolume") and thickness:
        return float(q["NetVolume"]) * volume / (float(thickness) * length), "NetVolume / thickness"
    return None, "missing"


def CAPT_FLOOR_AREA(model):
    """Floor area of the building in m2 -> (area, source).
    1st choice: sum of IfcSpace GrossFloorArea (closest to BR18 'etageareal').
    2nd choice: sum of IfcSpace NetFloorArea (underestimates etageareal).
    3rd choice: sum of the areas of the floor slabs."""
    area_scale = unit_util.calculate_unit_scale(model, "AREAUNIT")
    spaces = model.by_type("IfcSpace")
    for key in ("GrossFloorArea", "NetFloorArea"):
        values = []
        for space in spaces:
            q = element_util.get_psets(space, qtos_only=True)
            value = (q.get("Qto_SpaceBaseQuantities", {}) or q.get("BaseQuantities", {})).get(key)
            if isinstance(value, (int, float)):
                values.append(value)
        if values and len(values) == len(spaces):
            return sum(values) * area_scale, f"IfcSpace {key} ({len(values)} spaces)"

    slab_areas = [CAPT_ELEMENT_AREA(model, s)[0] for s in CAPT_FLOORS(model)]
    slab_areas = [a for a in slab_areas if a]
    if slab_areas:
        return sum(slab_areas), f"floor slab areas ({len(slab_areas)} slabs)"
    return None, "missing"


# ----------------------------------------------------------------------------
# BR18 Table 7 (Excel)
# ----------------------------------------------------------------------------
TABLE7_COLUMNS = [
    "Sorterings ID", "Navn DK",
    "Global Opvarmning, modul A1-A3", "Global Opvarmning, modul C3",
    "Global Opvarmning, modul C4", "Global Opvarmning, modul D",
    "Deklareret enhed (FU)", "Masse faktor", "Masse enhed",
]


def CAPT_TABLE7(path):
    """BR18 Table 7 as a DataFrame indexed by 'Sorterings ID'."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"BR18 Table 7 not found at {path}")
    df = pd.read_excel(path, sheet_name=0)
    df.columns = [str(c).strip() for c in df.columns]
    missing = [c for c in TABLE7_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Columns missing in Table 7: {missing}")
    df["Sorterings ID"] = df["Sorterings ID"].astype(str).str.strip()
    return df.drop_duplicates("Sorterings ID").set_index("Sorterings ID", drop=False)
