"""
CHEK – Check
------------
Checks the GWP result from CALC (kg CO2e/m2/year) against the BR18 limit values
(copied from Input/BR18_GWP_Minimum_Values.xlsx) and returns a text result for both building types.

Usage:
    from chek import chek
    print(chek(calc_result))
"""

# BR18 limit values [kg CO2e/m2/year] – copied from BR18_GWP_Minimum_Values.xlsx
BR18_LIMITS = {
    1: [  # Storybuildings, offices, trade, warehouse
        ("BR18, §298, stk. 1, pkt. 4", 7.5),
        ("BR18, §297, stk. 13, pkt. 4", 6.1),
    ],
    2: [  # Other buildings
        ("BR18, §298, stk. 1, pkt. 4", 8.0),
        ("BR18, §297, stk. 13, pkt. 5", 6.4),
    ],
}

BUILDING_TYPES = {
    1: "Storybuildings, offices, trade, warehouse",
    2: "Other buildings",
}


def chek(calc_result):
    """
    calc_result : dict from CALC (uses 'gwp_m2_year')
    Returns the check for both building types as text.
    """
    gwp = calc_result["gwp_m2_year"]
    lines = [f"GWP of exterior walls: {gwp:.2f} kg CO2e/m2/year"]

    for btype, limits in BR18_LIMITS.items():
        lines.append(f"\n{BUILDING_TYPES[btype]}:")
        for paragraph, limit in limits:
            if gwp <= limit:
                lines.append(f"  ✔ Complies with {paragraph}: {gwp:.2f} ≤ limit of "
                             f"{limit:.1f} kg CO2e/m2/year ({gwp / limit:.0%} of limit).")
            else:
                lines.append(f"  ✘ Does NOT comply with {paragraph}: {gwp:.2f} > limit of "
                             f"{limit:.1f} kg CO2e/m2/year (exceeded by {gwp - limit:.2f}).")

    lines.append("\nNote: only exterior walls are included – the limits apply to the whole building.")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    from capt import capt
    from conn import conn
    from calc import calc, print_calc
    rows, totals = capt(sys.argv[1])
    conn_result, filtered, sorted_off = conn(totals)
    res = calc(conn_result)
    print_calc(res)
    print("\n" + chek(res))
