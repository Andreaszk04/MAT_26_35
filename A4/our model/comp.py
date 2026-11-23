"""
COMP – Compare: "What changes between alternatives?"

Primary function of the tool: COMP_INSULATION.
For one wall type, the original insulation layer(s) are replaced by an alternative
insulation with the SAME thermal resistance R (so the wall keeps the same U-value).
The required thickness and the GWP of the alternative are calculated and compared.
"""
from calc import (CALC_EQUIVALENT_THICKNESS, CALC_GWP, CALC_INSULATION_UVALUE,
                  CALC_QUANTITY, CALC_UVALUE)
from conn import CONN_TABLE7


def COMP_INSULATION(wall, alternatives, table7, Rsi=0.13, Rse=0.04):
    """wall: one wall-type result from analyse(); alternatives: list from config.
    Returns a list of scenario rows (first row = original wall)."""
    layers = wall["layers"]
    insulation = [l for l in layers if l["is_insulation"]]
    if not insulation:
        return []

    area = wall["area_m2"]
    R_ins = sum(l["R"] for l in insulation) if all(l["R"] is not None for l in insulation) else None
    d_ins = sum(l["thickness_m"] for l in insulation)
    gwp_ins = sum((l["GWP_total"] or 0.0) for l in insulation)
    gwp_wall = wall["GWP_total"]
    R_other = [l["R"] for l in layers if not l["is_insulation"]]

    rows = [{
        "Wall type": wall["wall_type"],
        "Scenario": "Original",
        "Insulation": " + ".join(l["material"] for l in insulation),
        "Table 7 entry": " + ".join(f"{l['sorterings_id']} {l['epd_name']}" for l in insulation),
        "lambda [W/mK]": (d_ins / R_ins) if R_ins else None,  # effective lambda
        "Insulation thickness [mm]": d_ins * 1000,
        "R insulation [m2K/W]": R_ins,
        "U insulation [W/m2K]": CALC_INSULATION_UVALUE(R_ins),
        "U wall [W/m2K]": wall["U_calc"],
        "Wall area [m2]": area,
        "GWP insulation [kg CO2e]": gwp_ins,
        "GWP insulation [kg CO2e/m2]": gwp_ins / area if area else None,
        "GWP wall [kg CO2e]": gwp_wall,
        "Change in wall GWP [%]": 0.0,
        "Change in wall thickness [mm]": 0.0,
        "Note": "",
    }]

    if R_ins is None:
        rows[0]["Note"] = "R of the original insulation unknown - alternatives cannot be sized"
        return rows

    for alt in alternatives:
        epd = CONN_TABLE7(alt.get("table7_id"), table7)
        lam = float(alt["lambda"])
        d_alt = CALC_EQUIVALENT_THICKNESS(R_ins, lam)
        note = alt.get("note", "")
        gwp_alt = None
        if epd is None:
            note = f"Table 7 id '{alt.get('table7_id')}' not found. " + note
        else:
            qty, qnote = CALC_QUANTITY(epd, area, d_alt, R_ins)
            g = CALC_GWP(epd, qty)
            gwp_alt = g["GWP_total"] if g else None
            note = (qnote + " " + note).strip()

        gwp_wall_alt = (gwp_wall - gwp_ins + gwp_alt) if (gwp_alt is not None and gwp_wall is not None) else None
        u_wall_alt = CALC_UVALUE(R_other + [d_alt / lam], Rsi, Rse)

        rows.append({
            "Wall type": wall["wall_type"],
            "Scenario": alt["name"],
            "Insulation": alt["name"],
            "Table 7 entry": f"{epd['sorterings_id']} {epd['epd_name']}" if epd else "-",
            "lambda [W/mK]": lam,
            "Insulation thickness [mm]": d_alt * 1000,
            "R insulation [m2K/W]": R_ins,
            "U insulation [W/m2K]": CALC_INSULATION_UVALUE(R_ins),
            "U wall [W/m2K]": u_wall_alt,
            "Wall area [m2]": area,
            "GWP insulation [kg CO2e]": gwp_alt,
            "GWP insulation [kg CO2e/m2]": gwp_alt / area if (gwp_alt is not None and area) else None,
            "GWP wall [kg CO2e]": gwp_wall_alt,
            "Change in wall GWP [%]": ((gwp_wall_alt - gwp_wall) / gwp_wall * 100)
                                       if (gwp_wall_alt is not None and gwp_wall) else None,
            "Change in wall thickness [mm]": (d_alt - d_ins) * 1000,
            "Note": note,
        })
    return rows
