"""
COMM – Communicate: "How do we make the findings useful?"

Console tables, an Excel workbook and a bar chart - including gaps and assumptions.
"""
from pathlib import Path

import pandas as pd

try:
    from tabulate import tabulate
except ImportError:  # tabulate is optional
    tabulate = None


ROUNDING = {  # decimals per column (console only - Excel keeps full precision)
    "Net area [m2]": 0, "U IFC [W/m2K]": 3, "U calculated [W/m2K]": 3, "GWP [kg CO2e/m2]": 1,
    "lambda [W/mK]": 3, "Insulation thickness [mm]": 0, "U insulation [W/m2K]": 3,
    "U wall [W/m2K]": 3, "GWP insulation [kg CO2e/m2]": 2, "GWP insulation [kg CO2e]": 0,
    "GWP wall [kg CO2e]": 0, "Change in wall GWP [%]": 1,
}


def _table(df):
    df = df.copy()
    for col, dec in ROUNDING.items():
        if col in df.columns:
            df[col] = df[col].map(lambda v, d=dec: "-" if v is None or v != v else f"{v:,.{d}f}")
    if tabulate:
        return tabulate(df, headers="keys", tablefmt="simple", showindex=False,
                        disable_numparse=True, stralign="right")
    return df.to_string(index=False)


def layers_dataframe(result):
    rows = []
    for w in result["walls"]:
        for l in w["layers"]:
            rows.append({
                "Wall type": w["wall_type"],
                "Layer": l["layer_no"],
                "IFC material": l["material"],
                "Thickness [mm]": l["thickness_m"] * 1000,
                "lambda [W/mK]": l["lambda"],
                "lambda source": l["lambda_source"],
                "R [m2K/W]": l["R"],
                "Insulation": "yes" if l["is_insulation"] else "",
                "Table 7 id": l["sorterings_id"],
                "Table 7 name": l["epd_name"],
                "Table 7 unit": l["epd_unit"],
                "Volume [m3]": l["volume_m3"],
                "Quantity [FU]": l["quantity_FU"],
                "GWP A1-A3+C3+C4 [kg CO2e]": l["GWP_total"],
                "GWP D [kg CO2e]": l["GWP_D"],
            })
    return pd.DataFrame(rows)


def walls_dataframe(result):
    return pd.DataFrame([{
        "Wall type": w["wall_type"],
        "Count": w["count"],
        "Net area [m2]": w["area_m2"],
        "Area source": w["area_source"],
        "Thickness [mm]": w["thickness_mm"],
        "U IFC [W/m2K]": w["U_ifc"],
        "U calculated [W/m2K]": w["U_calc"],
        "GWP [kg CO2e]": w["GWP_total"],
        "GWP [kg CO2e/m2]": w["GWP_per_m2"],
        "Insulated": "yes" if w["has_insulation"] else "",
    } for w in result["walls"]])


def checks_dataframe(result):
    return pd.DataFrame([{"Wall type": w["wall_type"], **c} for w in result["walls"] for c in w["checks"]])


def COMM_CONSOLE(result, wall_type=None):
    """Print overview, U-value checks and the insulation comparison."""
    walls = walls_dataframe(result)
    print("\n=== Exterior wall types ===")
    print(_table(walls[["Wall type", "Count", "Net area [m2]", "U IFC [W/m2K]",
                        "U calculated [W/m2K]", "GWP [kg CO2e/m2]", "Insulated"]]))

    comp = pd.DataFrame(result["comparison"])
    if comp.empty:
        print("\nNo insulated exterior walls found - nothing to compare.")
    else:
        types = [wall_type] if wall_type else comp["Wall type"].unique()
        for t in types:
            sub = comp[comp["Wall type"] == t]
            w = next(x for x in result["walls"] if x["wall_type"] == t)
            print(f"\n=== {t}  ({w['area_m2']:.0f} m2, U_ifc = {w['U_ifc']}, "
                  f"U_calc = {w['U_calc']:.3f} W/m2K) ===")
            ins = [l for l in w["layers"] if l["is_insulation"]]
            for l in ins:
                print(f"  original insulation: {l['material']}  d = {l['thickness_m']*1000:.0f} mm, "
                      f"lambda = {l['lambda']}, R = {l['R']:.2f} m2K/W")
            print(_table(sub[["Scenario", "lambda [W/mK]", "Insulation thickness [mm]",
                              "U insulation [W/m2K]", "U wall [W/m2K]",
                              "GWP insulation [kg CO2e/m2]", "GWP insulation [kg CO2e]",
                              "GWP wall [kg CO2e]", "Change in wall GWP [%]"]]))

    fails = checks_dataframe(result)
    fails = fails[fails["status"].isin(["FAIL", "WARNING"])]
    if not fails.empty:
        print("\n=== Checks that need attention ===")
        print(_table(fails))

    if result["gaps"]:
        print("\n=== Data gaps ===")
        for g in result["gaps"]:
            print(" -", g)

    print("\n=== Assumptions ===")
    for k, v in result["assumptions"].items():
        print(f" - {k}: {v}")


def COMM_EXCEL(result, path):
    """Write all results to one workbook."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame(result["comparison"]).to_excel(writer, sheet_name="Insulation comparison", index=False)
        walls_dataframe(result).to_excel(writer, sheet_name="Wall types", index=False)
        layers_dataframe(result).to_excel(writer, sheet_name="Layers", index=False)
        checks_dataframe(result).to_excel(writer, sheet_name="Checks", index=False)
        pd.DataFrame({"Data gaps": result["gaps"]}).to_excel(writer, sheet_name="Gaps", index=False)
        pd.DataFrame(list(result["assumptions"].items()), columns=["Assumption", "Value"]) \
            .to_excel(writer, sheet_name="Assumptions", index=False)
        for ws in writer.sheets.values():  # readable column widths
            for col in ws.columns:
                width = max(len(str(c.value)) if c.value is not None else 0 for c in col[:60])
                ws.column_dimensions[col[0].column_letter].width = min(max(10, width + 2), 60)
    return path


def COMM_CHART(result, path):
    """Insulation GWP per m2 wall for every alternative, summed over all insulated
    exterior wall types (area-weighted). The original insulation is the dark bar."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    comp = pd.DataFrame(result["comparison"])
    if comp.empty:
        return None
    comp = comp.dropna(subset=["GWP insulation [kg CO2e]"])
    total_area = comp[comp["Scenario"] == "Original"]["Wall area [m2]"].sum()
    agg = comp.groupby("Scenario")["GWP insulation [kg CO2e]"].sum() / total_area
    agg = agg.sort_values()

    blue, dark, ink, muted = "#2a78d6", "#0d366b", "#0b0b0b", "#52514e"
    fig, ax = plt.subplots(figsize=(8, 0.45 * len(agg) + 1.4), dpi=150)
    fig.patch.set_facecolor("#fcfcfb")
    ax.set_facecolor("#fcfcfb")
    colors = [dark if s == "Original" else blue for s in agg.index]
    ax.barh(agg.index, agg.values, color=colors, height=0.6)
    ax.axvline(0, color=muted, linewidth=0.8)
    for y, v in enumerate(agg.values):
        ax.text(v + (0.015 if v >= 0 else -0.015) * max(abs(agg.values)), y, f"{v:.1f}",
                va="center", ha="left" if v >= 0 else "right", fontsize=8, color=ink)
    ax.set_xlabel("kg CO2e per m² exterior wall (A1-A3 + C3 + C4), same R as original", color=muted, fontsize=8)
    ax.set_title("Insulation GWP – original vs. alternatives (all insulated exterior walls)",
                 loc="left", fontsize=10, color=ink)
    ax.tick_params(colors=muted, labelsize=8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="x", color="#e6e5e0", linewidth=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
    return path
