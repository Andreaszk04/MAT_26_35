import os
import pandas as pd
from Calculate_Wall_Layer_Volumes import layer_volumes_summary

excel_filename = "Tabel-7-2025.xlsx"
excel_path = os.path.join(os.path.dirname(__file__), excel_filename)

df = pd.read_excel(excel_path, sheet_name=0)
df.columns = [str(c).strip() for c in df.columns]

required_cols = [
    "Sorterings ID", "Navn DK",
    "Global Opvarmning, modul A1-A3",
    "Global Opvarmning, modul C3",
    "Global Opvarmning, modul C4",
    "Deklareret enhed (FU)", "Masse faktor", "Masse enhed"
]

for col in required_cols:
    if col not in df.columns:
        raise ValueError(f"Column '{col}' not found in Excel file")

results = []
material_units = {}
calculated_unit = "m³"
allowed_units = {"kg", "m²", "m² with R=1 m²K/W", "m³", "ton"}

print("\nAssign a Sorterings ID from Table 7 to each material found in the wall:")

for material_name, data in layer_volumes_summary.items():
    volume = data["volume"]
    thickness = data["thickness"]
    while True:
        user_input = input(f"Enter Sorterings ID for material '{material_name}': ").strip()
        match = df[df["Sorterings ID"].astype(str) == user_input]
        if match.empty:
            print(f"No match found for Sorterings ID '{user_input}'")
            continue

        unit = str(match["Deklareret enhed (FU)"].values[0]).strip()
        if unit not in allowed_units:
            print(f"This is not a wall material (declared unit: '{unit}')")
            continue

        total_gwp = (
            match["Global Opvarmning, modul A1-A3"].fillna(0).values[0] +
            match["Global Opvarmning, modul C3"].fillna(0).values[0] +
            match["Global Opvarmning, modul C4"].fillna(0).values[0]
        )
        navn_dk = match["Navn DK"].values[0]
        masse_faktor = match["Masse faktor"].values[0]
        masse_enhed = match["Masse enhed"].values[0]

        results.append({
            "Material (IFC)": material_name,
            "Volume [m³]": volume,
            "Sorterings ID": user_input,
            "Navn DK": navn_dk,
            "Total GWP (A1-A3 + C3 + C4)": total_gwp,
            "Enhed": unit,
            "Masse faktor": masse_faktor,
            "Masse enhed": masse_enhed,
            "Layer thickness": thickness
        })
        material_units[material_name] = unit
        break

print("\n----------------------------------------------")

print("\nSummary of Assigned Materials:")
for r in results:
    print(f"- IFC material: {r['Material (IFC)']} is mapped with EPD: {r['Navn DK']} | "
          f"Volume: {r['Volume [m³]']:.3f} m³ | "
          f"EPD unit: {r['Enhed']} | "
          f"Layer thickness: {r['Layer thickness']} m | "
          f"GWP: {r['Total GWP (A1-A3 + C3 + C4)']:.2f} kg CO2-eq / {r['Enhed']}")

print("\n----------------------------------------------")