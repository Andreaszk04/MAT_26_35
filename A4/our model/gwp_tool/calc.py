"""
CALC - Calculate: "What can we derive?"

Step 1 (before CONN): volume of each material, per wall type.
Step 2 (after CONN):  GWP of each material over the 50-year reference period,
                      including replacements (BR18 module B4).
Step 3:               GWP per m2 floor area per year, per building part.
"""
import math
from collections import defaultdict

from capt import CAPT_ELEMENT_AREA, CAPT_LAYERS, CAPT_TYPE_NAME


# ----------------------------------------------------------------------------
# Step 1 - volumes
# ----------------------------------------------------------------------------
def CALC_VOLUMES(model, elements, gaps):
    """Volume = layer thickness x element area, summed per material.

    Returns {part: {type_name: {material: {"volume_m3", "area_m2", "thickness_m",
                                           "element_count"}}}}
    'area_m2' is the layer area summed over all layers of that material, so two
    layers of the same board count as twice the area (needed for m2-based EPDs)."""
    volumes = {}
    for part, part_elements in elements.items():
        by_type = defaultdict(lambda: defaultdict(lambda: {
            "volume_m3": 0.0, "area_m2": 0.0, "thickness_m": set(), "element_count": 0}))
        for el in part_elements:
            type_name = CAPT_TYPE_NAME(el)
            area, _ = CAPT_ELEMENT_AREA(model, el)
            layers = CAPT_LAYERS(model, el)
            if area is None:
                gaps.append(f"{part} / {type_name}: element #{el.id()} has no area - skipped")
                continue
            if not layers:
                gaps.append(f"{part} / {type_name}: element #{el.id()} has no material layers - skipped")
                continue
            for layer in layers:
                if layer["thickness_m"] is None:
                    gaps.append(f"{part} / {type_name}: '{layer['material']}' has no thickness - skipped")
                    continue
                entry = by_type[type_name][layer["material"]]
                entry["volume_m3"] += layer["thickness_m"] * area
                entry["area_m2"] += area
                entry["thickness_m"].add(round(layer["thickness_m"], 4))
            for material in {l["material"] for l in layers}:
                by_type[type_name][material]["element_count"] += 1
        volumes[part] = {t: {m: dict(v, thickness_m=sorted(v["thickness_m"]))
                             for m, v in mats.items()}
                         for t, mats in by_type.items()}
    return volumes


def CALC_TYPE_AREAS(model, elements):
    """Wall area per type [m2] -> {part: {type_name: area}} (for kg CO2e per m2 wall)."""
    areas = {}
    for part, part_elements in elements.items():
        per_type = defaultdict(float)
        for el in part_elements:
            area, _ = CAPT_ELEMENT_AREA(model, el)
            per_type[CAPT_TYPE_NAME(el)] += area or 0.0
        areas[part] = dict(per_type)
    return areas


def CALC_VOLUME_TOTALS(volumes):
    """Sum the volume of each material per building part (all types together)."""
    totals = {}
    for part, types in volumes.items():
        per_material = defaultdict(float)
        for materials in types.values():
            for material, v in materials.items():
                per_material[material] += v["volume_m3"]
        totals[part] = dict(per_material)
    return totals


# ----------------------------------------------------------------------------
# Step 2 - GWP
# ----------------------------------------------------------------------------
def CALC_QUANTITY(epd, volume_m3, area_m2, thickness_m, lam=None, board_thickness_m=None):
    """Convert a material amount into the declared unit (FU) of its Table 7 entry.
    Returns (quantity, note); quantity is None if the conversion is not possible."""
    fu = epd["unit"]
    rho, rho_unit = epd["mass_factor"], epd["mass_unit"]

    if fu == "m3":
        return volume_m3, ""
    if "R=1" in fu:  # 'm2 with R=1 m2K/W' -> amount = sum(area x R) = volume / lambda
        if not lam:
            return None, "lambda missing - cannot convert to 'm2 with R=1'"
        return volume_m3 / lam, ""
    if fu == "m2":
        if board_thickness_m and thickness_m:  # e.g. a 25 mm gypsum layer = 2 boards
            boards = max(1, round(max(thickness_m) / board_thickness_m))
            return area_m2 * boards, f"{boards} board(s) per layer" if boards > 1 else ""
        return area_m2, ""
    if fu in ("kg", "ton"):
        if rho_unit == "kg/m3":
            mass = volume_m3 * rho
        elif rho_unit == "kg/m2":
            mass = area_m2 * rho
        elif rho_unit == "kg/m2/mm":
            mass = volume_m3 * 1000 * rho  # area x thickness[mm] x factor
        elif rho_unit == "ton/m3":
            mass = volume_m3 * rho * 1000
        elif rho_unit == "kg/kg":
            return None, "Table 7 gives no density (kg/kg) - add a density"
        else:
            return None, f"mass unit '{rho_unit}' not handled"
        return (mass if fu == "kg" else mass / 1000.0), ""
    return None, f"declared unit '{fu}' not handled"


def CALC_REPLACEMENTS(lifetime, period=50):
    """Number of replacements within the reference period (BR18 module B4).
    lifetime 40 -> 1, lifetime 15 -> 3, lifetime >= 50 -> 0."""
    if not lifetime or lifetime >= period:
        return 0
    return math.ceil(period / lifetime) - 1


def CALC_GWP(epd, quantity, lifetime, period=50):
    """GWP over the reference period [kg CO2e].
    Scope as in BR18: A1-A3 + C3 + C4, and each replacement adds the same again (B4).
    Module D is reported separately and NOT included in the total."""
    if epd is None or quantity is None:
        return None
    n = CALC_REPLACEMENTS(lifetime, period)
    one_life = (epd["gwp_A1A3"] + epd["gwp_C3"] + epd["gwp_C4"]) * quantity
    return {
        "A1-A3": epd["gwp_A1A3"] * quantity,
        "C3+C4": (epd["gwp_C3"] + epd["gwp_C4"]) * quantity,
        "replacements": n,
        "B4": one_life * n,
        "total": one_life * (1 + n),
        "D (not in total)": epd["gwp_D"] * quantity * (1 + n),
    }


# ----------------------------------------------------------------------------
# Step 3 - per m2 floor area per year
# ----------------------------------------------------------------------------
def CALC_PER_M2_YEAR(gwp_kg, floor_area_m2, period=50):
    """kg CO2e  ->  kg CO2e / m2 / year (the unit of the BR18 limit)."""
    if gwp_kg is None or not floor_area_m2:
        return None
    return gwp_kg / floor_area_m2 / period
