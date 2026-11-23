"""
Exterior wall GWP tool (A4)

analyse(model) is the one callable function for the manager / runner:

    from gwp_tool import analyse
    result = analyse(my_model)

Flow: CAPT -> CALC (volumes) -> CONN -> CALC (GWP) -> CALC (per m2 per year) -> CHEK
It returns plain Python data; COMM (printing / CSV) is done by main.py.
"""
import json
from collections import defaultdict
from pathlib import Path

from capt import CAPT_ELEMENTS, CAPT_FLOOR_AREA, CAPT_TABLE7
from calc import (CALC_GWP, CALC_PER_M2_YEAR, CALC_QUANTITY, CALC_TYPE_AREAS,
                  CALC_VOLUME_TOTALS, CALC_VOLUMES)
from conn import CONN_MATERIAL, CONN_TABLE7
from chek import CHEK_COVERAGE, CHEK_FLOOR_AREA, CHEK_LIMIT

HERE = Path(__file__).resolve().parent
DEFAULT_TABLE7 = HERE / "input" / "Tabel-7-2025.xlsx"
DEFAULT_MATERIALS = HERE / "input" / "material_data.json"
DEFAULT_CONFIG = HERE / "input" / "config.json"
NO_GWP_KEYS = ("air", "landscape")  # recognised, but deliberately not counted


def analyse(model, table7_path=DEFAULT_TABLE7, material_path=DEFAULT_MATERIALS,
            config_path=DEFAULT_CONFIG):
    """Primary callable. Returns
    {"rows", "parts", "types", "volume_totals", "floor_area_m2", "total", "limit", "checks", "gaps"}"""
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    material_data = json.loads(Path(material_path).read_text(encoding="utf-8"))
    period = config["reference_period_years"]
    limit = dict(config["limits"][config["building_type"]], building_type=config["building_type"])
    gaps = []

    # --- CAPT ---------------------------------------------------------------
    table7 = CAPT_TABLE7(table7_path)
    elements = CAPT_ELEMENTS(model)
    floor_area, floor_area_source = CAPT_FLOOR_AREA(model)
    for part, els in elements.items():
        if not els:
            gaps.append(f"{part}: no elements found in the model")

    # --- CALC: volumes per part / type / material ---------------------------
    volumes = CALC_VOLUMES(model, elements, gaps)
    type_areas = CALC_TYPE_AREAS(model, elements)

    # --- CONN + CALC: GWP per material ---------------------------------------
    rows = []
    for part, types in volumes.items():
        for type_name, materials in types.items():
            for material, v in materials.items():
                key = CONN_MATERIAL(material, part)
                epd = CONN_TABLE7(key, material_data, table7)
                row = {"part": part, "type": type_name, "material": material, "key": key,
                       **{k: v[k] for k in ("volume_m3", "area_m2", "thickness_m", "element_count")},
                       "sorterings_id": None, "epd_name": None, "unit": None, "quantity": None,
                       "lifetime": None, "replacements": None,
                       "gwp_A1A3": None, "gwp_B4": None, "gwp_C3C4": None,
                       "gwp_total": None, "gwp_D": None, "note": ""}
                if key is None:
                    gaps.append(f"{part}: material '{material}' not recognised by CONN_MATERIAL")
                elif epd is None:
                    gaps.append(f"{part}: key '{key}' has no valid Table 7 id in material_data.json")
                elif key in NO_GWP_KEYS:
                    row.update(epd_name=f"({key} - not counted)", gwp_total=0.0)
                else:
                    volume, thickness = v["volume_m3"], v["thickness_m"]
                    cap = epd.get("max_thickness_m")
                    if cap and thickness and max(thickness) > cap:
                        # e.g. a 40 mm 'steel finish' layer is not 40 mm of solid steel
                        volume = v["area_m2"] * cap
                        thickness = [cap]
                        gaps.append(f"{part}: '{material}' modelled {max(v['thickness_m'])*1000:.0f} mm - "
                                    f"counted as {cap*1000:.1f} mm solid steel (assumption, see material_data.json)")
                    qty, note = CALC_QUANTITY(epd, volume, v["area_m2"], thickness,
                                              epd.get("lambda"), epd.get("board_thickness_m"))
                    gwp = CALC_GWP(epd, qty, epd["lifetime"], period)
                    if gwp is None:
                        gaps.append(f"{part}: '{material}' -> {epd['sorterings_id']}: {note}")
                    row.update(sorterings_id=epd["sorterings_id"], epd_name=epd["epd_name"],
                               unit=epd["unit"], quantity=qty, lifetime=epd["lifetime"], note=note)
                    if gwp:
                        row.update(replacements=gwp["replacements"], gwp_A1A3=gwp["A1-A3"],
                                   gwp_B4=gwp["B4"], gwp_C3C4=gwp["C3+C4"],
                                   gwp_total=gwp["total"], gwp_D=gwp["D (not in total)"])
                    if "VERIFY" in str(epd.get("lifetime_source", "")) and epd["lifetime"] \
                            and epd["lifetime"] < period:
                        gaps.append(f"{part}: lifetime of '{key}' ({epd['lifetime']} y) is unverified "
                                    f"and causes replacements - check BUILD 2021:32")
                rows.append(row)

    # --- CALC: sum per building part, per m2 floor area per year ------------
    parts = {}
    sums = defaultdict(float)
    for r in rows:
        sums[r["part"]] += r["gwp_total"] or 0.0
    for part in elements:
        parts[part] = {"gwp_kg": sums[part],
                       "gwp_per_m2_year": CALC_PER_M2_YEAR(sums[part], floor_area, period)}
    total_kg = sum(sums.values())

    # summary per wall type: area, GWP, GWP per m2 wall, biggest contributor
    types = []
    for part, per_type in type_areas.items():
        for type_name, area in per_type.items():
            trows = [r for r in rows if r["part"] == part and r["type"] == type_name]
            gwp = sum(r["gwp_total"] or 0.0 for r in trows)
            top = max(trows, key=lambda r: r["gwp_total"] or 0.0, default=None)
            types.append({
                "part": part, "type": type_name, "area_m2": area, "gwp_kg": gwp,
                "gwp_per_m2_wall": gwp / area if area else None,
                "gwp_per_m2_year": CALC_PER_M2_YEAR(gwp, floor_area, period),
                "main_material": top["material"] if top and top["gwp_total"] else "-",
                "complete": all(r["gwp_total"] is not None for r in trows),
            })
    types.sort(key=lambda t: -t["gwp_kg"])
    total = {"gwp_kg": total_kg,
             "gwp_per_m2_year": CALC_PER_M2_YEAR(total_kg, floor_area, period)}

    # --- CHEK ---------------------------------------------------------------
    checks = [
        CHEK_LIMIT(total["gwp_per_m2_year"], limit),
        CHEK_COVERAGE(rows),
        CHEK_FLOOR_AREA(floor_area, floor_area_source),
    ]

    return {
        "rows": rows,
        "parts": parts,
        "types": types,
        "volume_totals": CALC_VOLUME_TOTALS(volumes),
        "floor_area_m2": floor_area,
        "floor_area_source": floor_area_source,
        "reference_period_years": period,
        "total": total,
        "limit": limit,
        "checks": checks,
        "gaps": sorted(set(gaps)),
    }


# this checks to see if it is running directly or has been called as a library.
if __name__ == "__main__":
    import sys
    import ifcopenshell
    import comm

    if len(sys.argv) < 2:
        sys.exit("usage: python gwp_tool.py <model.ifc>")
    comm.COMM_RESULT(analyse(ifcopenshell.open(sys.argv[1])))
