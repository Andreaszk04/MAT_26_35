"""
CHEK - Check: "Does the evidence satisfy a criterion?"
"""


def CHEK_LIMIT(gwp_per_m2_year, limit):
    """Does the GWP [kg CO2e/m2/year] stay under the BR18 limit?"""
    if gwp_per_m2_year is None:
        return {"check": "GWP <= BR18 limit", "status": "N/A",
                "detail": "GWP per m2 per year could not be calculated (floor area missing?)"}
    share = gwp_per_m2_year / limit["value"]
    return {
        "check": f"Walls' share of the building limit ({limit['value']} kg CO2e/m2/year)",
        "status": "PASS" if gwp_per_m2_year <= limit["value"] else "FAIL",
        "detail": f"{gwp_per_m2_year:.2f} kg CO2e/m2/year = {share:.0%} of the limit",
        "share_of_limit": share,
    }


def CHEK_COVERAGE(rows):
    """How much of the material volume got a GWP value? Unmatched materials make the
    total too low, so the result is only trustworthy when coverage is close to 100 %."""
    total = sum(r["volume_m3"] for r in rows if r["key"] not in ("air", "landscape"))
    covered = sum(r["volume_m3"] for r in rows if r["key"] not in ("air", "landscape") and r["gwp_total"] is not None)
    if not total:
        return {"check": "Material volume with a GWP value", "status": "N/A", "detail": "no volume"}
    share = covered / total
    missing = sorted({r["material"] for r in rows if r["key"] not in ("air", "landscape") and r["gwp_total"] is None})
    return {
        "check": "Material volume with a GWP value",
        "status": "PASS" if not missing else "WARNING",
        "detail": f"{share:.1%} of {total:.1f} m3"
                  + (f" - missing: {', '.join(missing)}" if missing else ""),
    }


def CHEK_FLOOR_AREA(floor_area, source):
    """Is the reference area the right kind? BR18 uses the gross floor area (etageareal)."""
    if floor_area is None:
        return {"check": "Floor area available", "status": "FAIL", "detail": "no floor area in the model"}
    status = "PASS" if source.startswith("IfcSpace GrossFloorArea") else "WARNING"
    return {"check": "Floor area = gross floor area (BR18 'etageareal')", "status": status,
            "detail": f"{floor_area:.1f} m2 from {source}"}
