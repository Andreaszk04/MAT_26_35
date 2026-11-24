"""
COMM – Communicate
------------------
Communicates the results of the tool:
  1. GWP
  2. Compliance with BR18 (from CHEK)
  3. GWP table with the summed materials (new names from CONN)
  4. Original materials that are NOT included (sorted off in CONN)

Run the whole tool:
    python comm.py model.ifc
or in a notebook:
    print(comm(calc_result, sorted_off))
"""
from chek import chek

LINE = "=" * 83


def comm(calc_result, sorted_off):
    """
    calc_result : dict from CALC
    sorted_off  : list from CONN  ({material, original, volume})
    Returns the full report as text.
    """
    out = []

    # 1. GWP --------------------------------------------------------------
    out += [LINE, "1. GWP – EXTERIOR WALLS", LINE,
            f"Total GWP (50 years):  {calc_result['gwp_total']:>12,.1f} kg CO2e",
            f"Floor area:            {calc_result['area']:>12,.1f} m2",
            f"GWP per m2 per year:   {calc_result['gwp_m2_year']:>12.2f} kg CO2e/m2/year", ""]

    # 2. Compliance -------------------------------------------------------
    out += [LINE, "2. COMPLIANCE WITH BR18", LINE, chek(calc_result), ""]

    # 3. GWP table --------------------------------------------------------
    out += [LINE, "3. GWP PER MATERIAL", LINE,
            f"{'Material':<45}{'V [m3]':>10}{'GWP/m3':>12}{'GWP [kg CO2e]':>16}",
            "-" * 83]
    for cls, r in sorted(calc_result["materials"].items(), key=lambda x: -x[1]["gwp"]):
        out.append(f"{cls:<45}{r['volume']:>10.3f}{r['gwp_factor']:>12.2f}{r['gwp']:>16,.1f}")
    out += ["-" * 83,
            f"{'Total':<45}{sum(r['volume'] for r in calc_result['materials'].values()):>10.3f}"
            f"{'':>12}{calc_result['gwp_total']:>16,.1f}", ""]

    # 4. Not included -----------------------------------------------------
    out += [LINE, "4. MATERIALS NOT INCLUDED", LINE]
    if sorted_off:
        out += [f"{'Original material':<70}{'V [m3]':>13}", "-" * 83]
        for it in sorted(sorted_off, key=lambda x: -x["volume"]):
            out.append(f"{it['original'][:69]:<70}{it['volume']:>13.3f}")
        out += ["-" * 83,
                f"{'Total not included':<70}{sum(it['volume'] for it in sorted_off):>13.3f}"]
    else:
        out.append("All materials were included.")

    return "\n".join(out)


if __name__ == "__main__":
    import sys
    from capt import capt
    from conn import conn
    from calc import calc
    rows, totals = capt(sys.argv[1])
    conn_result, filtered, sorted_off = conn(totals)
    res = calc(conn_result)
    print("\n" + comm(res, sorted_off))
