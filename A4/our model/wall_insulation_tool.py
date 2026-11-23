"""
Exterior wall insulation tool (A4, group 35)

analyse(model) is the callable function for the manager / runner:

    from wall_insulation_tool import analyse
    result = analyse(my_model)

It runs CAPT -> CONN -> CALC -> CHEK -> COMP and returns plain Python data
(lists / dicts) so it can be reused by other tools. COMM (printing, Excel and the
chart) is done by main.py or by the __main__ block below.
"""
import json
from pathlib import Path

from capt import CAPT_AREA, CAPT_EXTERIOR_WALLS, CAPT_LAYERS, CAPT_TABLE7, CAPT_UVALUE, CAPT_WALL_TYPES
from conn import CONN_LAMBDA, CONN_MATERIAL, CONN_TABLE7
from calc import CALC_GWP, CALC_LAYER_R, CALC_QUANTITY, CALC_UVALUE
from chek import CHEK_AREA, CHEK_UVALUE
from comp import COMP_INSULATION

HERE = Path(__file__).resolve().parent
DEFAULT_CONFIG = HERE / "input" / "config.json"
DEFAULT_TABLE7 = HERE / "input" / "Tabel-7-2025.xlsx"


def _analyse_wall_type(model, type_name, walls, config, table7, gaps):
    """CAPT + CONN + CALC + CHEK for one wall type."""
    Rsi, Rse = config["surface_resistance"]["Rsi"], config["surface_resistance"]["Rse"]

    # --- CAPT ---------------------------------------------------------------
    layers = CAPT_LAYERS(model, walls[0])  # same type -> same layer set
    areas = [CAPT_AREA(model, w) for w in walls]
    area = sum(a for a, _ in areas if a)
    area_sources = sorted({src for _, src in areas})
    u_values_ifc = sorted({round(u, 4) for u in (CAPT_UVALUE(w) for w in walls) if u is not None})
    u_ifc = u_values_ifc[0] if u_values_ifc else None

    if not layers:
        gaps.append(f"{type_name}: no IfcMaterialLayerSet - skipped")
        return None

    # --- CONN + CALC per layer ----------------------------------------------
    for layer in layers:
        rule = CONN_MATERIAL(layer, config)
        if not rule:
            gaps.append(f"{type_name}: material '{layer['material']}' not in config['materials']")
        lam, lam_src = CONN_LAMBDA(layer, rule)
        layer["lambda"] = lam if "R" not in rule else None
        layer["lambda_source"] = lam_src if "R" not in rule else "fixed R (air layer)"
        layer["R"] = CALC_LAYER_R(layer["thickness_m"], lam, rule.get("R"))
        layer["is_insulation"] = bool(rule.get("insulation"))

        epd = CONN_TABLE7(rule.get("table7_id"), table7)
        if rule.get("table7_id") and epd is None:
            gaps.append(f"{type_name}: Table 7 id {rule['table7_id']} not found")
        layer["sorterings_id"] = epd["sorterings_id"] if epd else None
        layer["epd_name"] = epd["epd_name"] if epd else None
        layer["epd_unit"] = epd["unit"] if epd else None
        layer["volume_m3"] = area * layer["thickness_m"]

        qty, note = (CALC_QUANTITY(epd, area, layer["thickness_m"], layer["R"]) if epd else (None, ""))
        if note:
            gaps.append(f"{type_name}: {layer['material']}: {note}")
        layer["quantity_FU"] = qty
        gwp = CALC_GWP(epd, qty)
        layer["GWP_total"] = gwp["GWP_total"] if gwp else None
        layer["GWP_D"] = gwp["GWP_D"] if gwp else None

    u_calc = CALC_UVALUE([l["R"] for l in layers], Rsi, Rse)
    gwp_total = sum(l["GWP_total"] for l in layers if l["GWP_total"] is not None)

    # --- CHEK ---------------------------------------------------------------
    checks = CHEK_UVALUE(u_calc, u_ifc, config["u_value_requirement"], config["u_value_tolerance"])
    checks.append(CHEK_AREA([a for a, _ in areas]))
    if len(u_values_ifc) > 1:
        checks.append({"check": "One U-value per wall type in IFC", "status": "WARNING",
                       "detail": f"values found: {u_values_ifc}"})

    return {
        "wall_type": type_name,
        "count": len(walls),
        "area_m2": area,
        "area_source": ", ".join(area_sources),
        "thickness_mm": sum(l["thickness_m"] for l in layers) * 1000,
        "U_ifc": u_ifc,
        "U_calc": u_calc,
        "GWP_total": gwp_total,
        "GWP_per_m2": gwp_total / area if area else None,
        "has_insulation": any(l["is_insulation"] for l in layers),
        "layers": layers,
        "checks": checks,
    }


def analyse(model, config_path=DEFAULT_CONFIG, table7_path=DEFAULT_TABLE7, wall_types=None):
    """Primary callable.

    model        : an opened ifcopenshell model
    config_path  : JSON with lambda values, Table 7 mapping and insulation alternatives
    table7_path  : BR18 Table 7 (xlsx)
    wall_types   : optional list of wall type names to analyse (default: all exterior)

    Returns {"walls": [...], "comparison": [...], "gaps": [...], "assumptions": {...}}
    """
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    table7 = CAPT_TABLE7(table7_path)
    Rsi, Rse = config["surface_resistance"]["Rsi"], config["surface_resistance"]["Rse"]

    groups = CAPT_WALL_TYPES(model, CAPT_EXTERIOR_WALLS(model))
    if wall_types:
        groups = {k: v for k, v in groups.items() if k in wall_types}

    gaps, walls, comparison = [], [], []
    for type_name in sorted(groups):
        wall = _analyse_wall_type(model, type_name, groups[type_name], config, table7, gaps)
        if wall is None:
            continue
        walls.append(wall)
        comparison += COMP_INSULATION(wall, config["insulation_alternatives"], table7, Rsi, Rse)

    return {
        "walls": walls,
        "comparison": comparison,
        "gaps": sorted(set(gaps)),
        "assumptions": {
            "Rsi": Rsi, "Rse": Rse,
            "U requirement [W/m2K]": config["u_value_requirement"],
            "GWP scope": "A1-A3 + C3 + C4 (BR18 Table 7); module D reported separately per layer",
            "Equivalence": "alternative insulation sized for the same thermal resistance R as the original "
                           "insulation, so the wall U-value is unchanged",
        },
    }


# this checks to see if it is running directly or has been called as a library.
if __name__ == "__main__":
    import sys
    import ifcopenshell
    import comm

    if len(sys.argv) < 2:
        sys.exit("usage: python wall_insulation_tool.py <model.ifc>")
    result = analyse(ifcopenshell.open(sys.argv[1]))
    comm.COMM_CONSOLE(result)
