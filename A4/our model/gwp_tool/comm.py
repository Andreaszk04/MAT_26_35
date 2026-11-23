"""
COMM - Communicate: "How do we make the findings useful?"

Console output is a short summary: one line per wall type, the materials that
matter most, the checks, a count of data gaps, and one concluding sentence.
Every detail (each material of each wall type) goes to the CSV file instead.
"""
import csv
from pathlib import Path


def _fmt(value, digits=0):
    return "-" if value is None else f"{value:,.{digits}f}"


def COMM_RESULT(result, top_n=5):
    """Print the summary to the console."""
    total = result["total"]
    types = result["types"]
    print("=" * 78)
    print(f"GWP of the exterior walls - {result['reference_period_years']}-year reference period")
    print(f"Floor area {_fmt(result['floor_area_m2'])} m2  |  "
          f"wall area {_fmt(sum(t['area_m2'] for t in types))} m2  |  "
          f"{len(types)} exterior wall types")
    print("=" * 78)

    # --- one line per wall type -------------------------------------------
    print(f"\n{'Wall type':<44}{'Area m2':>9}{'t CO2e':>8}{'kg/m2 wall':>12}{'Share':>7}")
    for t in types:
        share = t["gwp_kg"] / total["gwp_kg"] if total["gwp_kg"] else 0
        flag = "" if t["complete"] else " *"
        name = t["type"].replace("Basic Wall:", "")[:42] + flag
        print(f"{name:<44}{_fmt(t['area_m2']):>9}{_fmt(t['gwp_kg'] / 1000, 1):>8}"
              f"{_fmt(t['gwp_per_m2_wall'], 1):>12}{share:>7.0%}")
    print(f"{'TOTAL':<44}{_fmt(sum(t['area_m2'] for t in types)):>9}"
          f"{_fmt(total['gwp_kg'] / 1000, 1):>8}")
    if any(not t["complete"] for t in types):
        print("  * contains materials without a GWP value - the real value is higher")

    # --- materials that drive the result ----------------------------------
    by_material = {}
    for r in result["rows"]:
        if r["gwp_total"]:
            by_material[r["material"]] = by_material.get(r["material"], 0.0) + r["gwp_total"]
    print(f"\nLargest contributors (of {_fmt(total['gwp_kg'] / 1000, 1)} t CO2e):")
    for material, gwp in sorted(by_material.items(), key=lambda x: -x[1])[:top_n]:
        print(f"  {material[:46]:<48}{_fmt(gwp / 1000, 1):>7} t  {gwp / total['gwp_kg']:>4.0%}")

    # --- checks and gaps --------------------------------------------------
    print("\nChecks:")
    for c in result["checks"]:
        print(f"  [{c['status']:<7}] {c['check']}: {c['detail']}")
    if result["gaps"]:
        print(f"\n{len(result['gaps'])} data gaps / assumptions to review "
              f"(full list in the CSV folder: gaps.txt)")

    print("\n" + "=" * 78)
    print(COMM_SENTENCE(result))
    print("=" * 78)


def COMM_SENTENCE(result):
    """One plain-language conclusion."""
    total = result["total"]["gwp_per_m2_year"]
    limit = result["limit"]
    if total is None:
        return "The GWP could not be expressed per m2 floor area because the floor area is missing."
    share = total / limit["value"]
    verdict = ("is below" if total <= limit["value"] else "is ABOVE")
    return (f"The total GWP of the exterior walls is {total:.2f} kg CO2e/m2/year "
            f"({result['total']['gwp_kg'] / 1000:,.0f} t CO2e over "
            f"{result['reference_period_years']} years). This {verdict} the BR18 limit of "
            f"{limit['value']} kg CO2e/m2/year and uses {share:.0%} of it - but the limit is for "
            f"the whole building, so this shows the walls' share, not compliance.")


def COMM_CSV(result, path):
    """Write all details: one row per wall type / material, plus gaps.txt next to it."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["part", "type", "material", "key", "sorterings_id", "epd_name", "unit",
              "volume_m3", "area_m2", "quantity", "lifetime", "replacements",
              "gwp_A1A3", "gwp_C3C4", "gwp_B4", "gwp_total", "gwp_D", "note"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(result["rows"])
    (path.parent / "gaps.txt").write_text("\n".join(result["gaps"]) + "\n", encoding="utf-8")
    return path
