"""
CALC – Calculate
----------------
1. Ask the user for the floor area of the building [m2]
2. GWP per material class:   GWP_i = V_i * gwp_factor_i        [kg CO2e]
3. Total and per m2 per year: GWP_total / (A * 50 years)       [kg CO2e/m2/year]

Usage:
    from capt import capt
    from conn import conn
    from calc import calc
    rows, totals = capt("model.ifc")
    conn_result, filtered, sorted_off = conn(totals)
    calc_result = calc(conn_result)
"""

PERIOD = 50   # years (the GWP values in column E are for a 50-year period)


def ask_area():
    """1. Ask the user for the building's floor area in m2 (must be a positive number)."""
    while True:
        txt = input("State the floor area of the building [m2]: ").strip().replace(",", ".")
        try:
            A = float(txt)
            if A > 0:
                return A
        except ValueError:
            pass
        print("  Please enter a positive number, e.g. 1250 or 1250.5")


def calc_gwp_materials(conn_result):
    """2. GWP per class. Returns {class: {"volume", "gwp_factor", "gwp"}}."""
    return {cls: {**r, "gwp": r["volume"] * r["gwp_factor"]}
            for cls, r in conn_result.items()}


def calc(conn_result, area=None, period=PERIOD):
    """
    conn_result : {class: {"volume": m3, "gwp_factor": kg CO2e/m3/50 yr}}  (from CONN)
    area        : floor area [m2]; asked for if None

    Returns dict:
      materials    : {class: {"volume", "gwp_factor", "gwp"}}
      gwp_total    : kg CO2e (50 years)
      area         : m2
      gwp_m2_year  : kg CO2e/m2/year
    """
    if area is None:
        area = ask_area()

    materials = calc_gwp_materials(conn_result)
    gwp_total = sum(r["gwp"] for r in materials.values())   # 3. sum
    gwp_m2_year = gwp_total / (area * period)                # 3. / (A * 50)

    return dict(materials=materials, gwp_total=gwp_total,
                area=area, gwp_m2_year=gwp_m2_year)


def print_calc(res):
    print(f"\n{'Class':<45}{'V [m3]':>10}{'GWP/m3':>12}{'GWP [kg CO2e]':>16}")
    print("-" * 83)
    for cls, r in sorted(res["materials"].items(), key=lambda x: -x[1]["gwp"]):
        print(f"{cls:<45}{r['volume']:>10.3f}{r['gwp_factor']:>12.2f}{r['gwp']:>16.1f}")
    print("-" * 83)
    print(f"{'Total GWP (50 years)':<67}{res['gwp_total']:>16.1f} kg CO2e")
    print(f"{'Floor area':<67}{res['area']:>16.1f} m2")
    print(f"{'GWP per m2 per year':<67}{res['gwp_m2_year']:>16.3f} kg CO2e/m2/year")


if __name__ == "__main__":
    import sys
    from capt import capt
    from conn import conn
    rows, totals = capt(sys.argv[1])
    conn_result, filtered, sorted_off = conn(totals)
    print_calc(calc(conn_result))
