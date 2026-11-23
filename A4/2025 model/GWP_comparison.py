import importlib
import pandas as pd
from tabulate import tabulate
from GWP_calculation import initial_gwp


def calculate_gwp_scenario():
    """Run a new GWP calculation for a wall configuration."""
    # Reload the material assignment so the user can choose new materials
    Tabel_7_materials_assigned = importlib.import_module("Tabel_7_materials_assigned")
    importlib.reload(Tabel_7_materials_assigned)

    from Conversion_factor import converted_results
    results = Tabel_7_materials_assigned.results

    gwp_per_material = {}
    total_gwp = 0

    for r in results:
        material_name_ifc = r["Material (IFC)"]
        epd_name = r["Navn DK"]
        total_gwp_per_unit = r["Total GWP (A1-A3 + C3 + C4)"]
        converted_unit = converted_results.get(material_name_ifc)

        if converted_unit is None:
            gwp = None
        else:
            gwp = total_gwp_per_unit * converted_unit
            total_gwp += gwp

        gwp_per_material[material_name_ifc] = {
            "EPD name": epd_name,
            "GWP_total": gwp,
            "Unit": r["Enhed"],
            "Layer thickness": r["Layer thickness"],
            "GWP per EPD unit": total_gwp_per_unit
        }

    return gwp_per_material, total_gwp


def main():
    print("----------------------------------------------")

    scenarios = []
    detailed_records = []
    scenario_counter = 1

    # --- Original scenario ---
    total_original = sum(v["GWP_total"] for v in initial_gwp.values() if v["GWP_total"] is not None)
    scenarios.append({
        "Scenario": f"Original ({scenario_counter})",
        "Total GWP (kg CO2-eq)": total_original
    })

    for mat, data in initial_gwp.items():
        detailed_records.append({
            "Scenario": "Original (1)",
            "IFC material": mat,
            "EPD name": data["EPD name"],
            "GWP per EPD unit": None,
            "Unit": data["Unit"],
            "Layer thickness [m]": None,
            "GWP_total (kg CO2-eq)": data["GWP_total"]
        })

    # --- Iterative loop for alternatives ---
    while True:
        answer = input("\nDo you want to calculate an alternative scenario? (y/n): ").strip().lower()
        if answer != "y":
            break

        scenario_counter += 1
        gwp_dict, total_gwp = calculate_gwp_scenario()
        scenario_name = f"Alternative {scenario_counter - 1}"
        scenarios.append({
            "Scenario": scenario_name,
            "Total GWP (kg CO2-eq)": total_gwp
        })

        for mat, data in gwp_dict.items():
            detailed_records.append({
                "Scenario": scenario_name,
                "IFC material": mat,
                "EPD name": data["EPD name"],
                "GWP per EPD unit": data["GWP per EPD unit"],
                "Unit": data["Unit"],
                "Layer thickness [m]": data["Layer thickness"],
                "GWP_total (kg CO2-eq)": data["GWP_total"]
            })

    # --- Summary table ---
    df_summary = pd.DataFrame(scenarios)
    df_summary["Difference from Original (%)"] = (
        (df_summary["Total GWP (kg CO2-eq)"] - df_summary.loc[0, "Total GWP (kg CO2-eq)"])
        / df_summary.loc[0, "Total GWP (kg CO2-eq)"] * 100
    ).round(2)

    df_summary["Total GWP (kg CO2-eq)"] = df_summary["Total GWP (kg CO2-eq)"].map("{:,.2f}".format)
    df_summary["Difference from Original (%)"] = df_summary["Difference from Original (%)"].map("{:+.2f}".format)

    # --- Print only summary table ---
    print("\n----------------------------------------------")
    print(tabulate(df_summary, headers="keys", tablefmt="grid", showindex=False, numalign="right", stralign="center"))

    # --- Detailed combined sheet for Excel ---
    df_detailed = pd.DataFrame(detailed_records)

    # Extract numeric index for correct sorting (e.g., Original first, then 1, 2, 3)
    def scenario_order(name):
        if "Original" in name:
            return 0
        else:
            try:
                return int(name.split()[-1])
            except ValueError:
                return 999

    df_detailed["Scenario_order"] = df_detailed["Scenario"].apply(scenario_order)
    df_detailed = df_detailed.sort_values(by=["Scenario_order", "IFC material"]).drop(columns="Scenario_order").reset_index(drop=True)

    # --- Save to Excel ---
    save = input("\nDo you want to save the results to Excel? (y/n): ").strip().lower()
    if save == "y":
        with pd.ExcelWriter("GWP_comparison_results.xlsx") as writer:
            df_summary.to_excel(writer, sheet_name="Summary", index=False)
            df_detailed.to_excel(writer, sheet_name="Detailed Results", index=False)
        print("Results saved to 'GWP_comparison_results.xlsx'.")

    print("\nComparison completed successfully.")


if __name__ == "__main__":
    main()

