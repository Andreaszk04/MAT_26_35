"""
CHEK – Check: "Does the evidence satisfy a criterion?"
"""


def CHEK_UVALUE(u_calc, u_ifc, requirement, tolerance=0.10):
    """Checks for one wall type:
       1. does the calculated U-value meet the requirement?
       2. does the U-value stored in the IFC agree with the calculated one?"""
    checks = []
    if u_calc is not None:
        checks.append({
            "check": f"U (calculated) <= {requirement} W/m2K",
            "status": "PASS" if u_calc <= requirement else "FAIL",
            "detail": f"U_calc = {u_calc:.3f} W/m2K",
        })
    else:
        checks.append({"check": "U (calculated)", "status": "N/A",
                       "detail": "missing lambda for at least one layer"})

    if u_ifc is None:
        checks.append({"check": "U in IFC", "status": "N/A",
                       "detail": "Pset_WallCommon.ThermalTransmittance missing"})
    elif u_calc is not None:
        deviation = (u_ifc - u_calc) / u_calc
        checks.append({
            "check": f"U (IFC) within +/-{tolerance:.0%} of U (calculated)",
            "status": "PASS" if abs(deviation) <= tolerance else "WARNING",
            "detail": f"U_ifc = {u_ifc:.3f}, U_calc = {u_calc:.3f} ({deviation:+.0%})",
        })
    return checks


def CHEK_AREA(areas):
    """Flag walls without a usable area."""
    missing = [a for a in areas if a is None]
    if missing:
        return {"check": "Wall area available", "status": "WARNING",
                "detail": f"{len(missing)} wall(s) without area were skipped"}
    return {"check": "Wall area available", "status": "PASS", "detail": "all walls"}
