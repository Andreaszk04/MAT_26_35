"""
CAPT – Capture: "What information do we have?"

Reads exterior walls, their material layers, area and U-value from the IFC model,
and reads the BR18 Table 7 generic EPD data.
"""
import re
from collections import defaultdict
from pathlib import Path

import pandas as pd
import ifcopenshell.util.element as element
import ifcopenshell.util.unit as unit


# ----------------------------------------------------------------------------
# Walls
# ----------------------------------------------------------------------------
def CAPT_EXTERIOR_WALLS(model):
    """Return all IfcWall (incl. subtypes such as IfcWallStandardCase) where
    Pset_WallCommon.IsExternal is True (type properties are inherited)."""
    walls = []
    for wall in model.by_type("IfcWall"):
        common = element.get_psets(wall).get("Pset_WallCommon", {})
        if common.get("IsExternal") is True:
            walls.append(wall)
    return walls


def wall_type_name(wall):
    """Name of the wall *type*. Uses IfcRelDefinesByType when present. Otherwise falls
    back to ObjectType/Name with a trailing Revit element id (':123456') removed, so
    that walls of the same type are grouped together."""
    wall_type = element.get_type(wall)
    if wall_type is not None and wall_type.Name:
        return wall_type.Name
    name = wall.ObjectType or wall.Name or f"Unnamed wall #{wall.id()}"
    return re.sub(r":\d+$", "", name)


def CAPT_WALL_TYPES(model, walls=None):
    """Group exterior walls by wall type -> {type_name: [walls]}."""
    walls = CAPT_EXTERIOR_WALLS(model) if walls is None else walls
    groups = defaultdict(list)
    for wall in walls:
        groups[wall_type_name(wall)].append(wall)
    return dict(groups)


# ----------------------------------------------------------------------------
# Layers
# ----------------------------------------------------------------------------
def _layer_set(wall):
    material = element.get_material(wall)  # may be a LayerSetUsage, LayerSet, ...
    if material is None:
        return None
    if material.is_a("IfcMaterialLayerSetUsage"):
        return material.ForLayerSet
    if material.is_a("IfcMaterialLayerSet"):
        return material
    return None


def _lambda_from_ifc(material):
    """Thermal conductivity stored on the IfcMaterial (e.g. Pset_MaterialThermal)."""
    if material is None:
        return None
    try:
        psets = element.get_psets(material)
    except Exception:
        return None
    for props in psets.values():
        value = props.get("ThermalConductivity")
        if isinstance(value, (int, float)) and value > 0:
            return float(value)
    return None


def CAPT_LAYERS(model, wall):
    """Material layers of a wall, outside -> inside as ordered in the layer set.
    Thickness is converted to metres using the project length unit."""
    layer_set = _layer_set(wall)
    if layer_set is None:
        return []
    scale = unit.calculate_unit_scale(model)  # project length unit -> metre
    layers = []
    for i, layer in enumerate(layer_set.MaterialLayers, start=1):
        material = layer.Material
        layers.append({
            "layer_no": i,
            "material": material.Name if material is not None else "Unnamed material",
            "category": getattr(layer, "Category", None) or getattr(material, "Category", None),
            "thickness_m": float(layer.LayerThickness or 0.0) * scale,
            "lambda_ifc": _lambda_from_ifc(material),
        })
    return layers


# ----------------------------------------------------------------------------
# Area and U-value
# ----------------------------------------------------------------------------
def CAPT_AREA(model, wall):
    """Net side area of one wall in m2 -> (area, source).
    Order: Qto NetSideArea -> NetVolume / Width -> GrossSideArea."""
    length_scale = unit.calculate_unit_scale(model)
    area_scale = unit.calculate_unit_scale(model, "AREAUNIT")
    volume_scale = unit.calculate_unit_scale(model, "VOLUMEUNIT")

    qtos = element.get_psets(wall, qtos_only=True)
    q = qtos.get("Qto_WallBaseQuantities", {}) or qtos.get("BaseQuantities", {})

    if q.get("NetSideArea"):
        return float(q["NetSideArea"]) * area_scale, "Qto NetSideArea"
    if q.get("NetVolume") and q.get("Width"):
        return (float(q["NetVolume"]) * volume_scale) / (float(q["Width"]) * length_scale), "NetVolume / Width"
    if q.get("GrossSideArea"):
        return float(q["GrossSideArea"]) * area_scale, "Qto GrossSideArea"
    # last resort: any property called Area / NetSideArea in any pset (old model behaviour)
    for props in element.get_psets(wall).values():
        for key in ("NetSideArea", "GrossSideArea", "Area"):
            if isinstance(props.get(key), (int, float)):
                return float(props[key]) * area_scale, f"Pset {key}"
    return None, "missing"


def CAPT_UVALUE(wall):
    """U-value [W/m2K] stored in the IFC (Pset_WallCommon.ThermalTransmittance)."""
    value = element.get_psets(wall).get("Pset_WallCommon", {}).get("ThermalTransmittance")
    return float(value) if isinstance(value, (int, float)) else None


# ----------------------------------------------------------------------------
# Reference data
# ----------------------------------------------------------------------------
TABLE7_COLUMNS = [
    "Sorterings ID", "Navn DK",
    "Global Opvarmning, modul A1-A3", "Global Opvarmning, modul C3",
    "Global Opvarmning, modul C4", "Global Opvarmning, modul D",
    "Deklareret enhed (FU)", "Masse faktor", "Masse enhed",
]


def CAPT_TABLE7(path):
    """Read BR18 Table 7 (generic emission data) into a DataFrame indexed by Sorterings ID."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Table 7 not found at {path}")
    df = pd.read_excel(path, sheet_name=0)
    df.columns = [str(c).strip() for c in df.columns]
    missing = [c for c in TABLE7_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Columns missing in Table 7: {missing}")
    df["Sorterings ID"] = df["Sorterings ID"].astype(str).str.strip()
    return df.set_index("Sorterings ID", drop=False)
