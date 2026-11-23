from Tabel_7_materials_assigned import results
from Conversion_factor import converted_results  # the converted volumes dictionary

# Dictionary to store the calculated GWP per material
gwp_per_material = {}
initial_gwp = {}  # Store GWP results for later use

for r in results:
    material_name_ifc = r["Material (IFC)"]
    epd_name = r["Navn DK"]  # from Tabel_7_materials_assigned
    total_gwp_per_unit = r["Total GWP (A1-A3 + C3 + C4)"]  # kg CO2-eq per FU
    converted_unit = converted_results.get(material_name_ifc)

    if converted_unit is None:
        print(f"Cannot calculate GWP for {material_name_ifc}: converted volume/unit missing")
        gwp = None
    else:
        gwp = total_gwp_per_unit * converted_unit

    gwp_per_material[material_name_ifc] = gwp
    initial_gwp[material_name_ifc] = {
        "GWP_total": gwp,
        "Unit": r["Enhed"],
        "EPD name": epd_name
    }

# Print summary
print("\nGWP per material (kg CO2-eq / FU):")
for r in results:
    material_ifc = r["Material (IFC)"]
    epd_name = r["Navn DK"]
    unit = r["Enhed"]
    gwp = gwp_per_material.get(material_ifc)

    if gwp is None:
        print(f"- IFC material: {material_ifc} | EPD: {epd_name} | Calculation failed!")
    else:
        print(f"- IFC material: {material_ifc} | EPD: {epd_name} | GWP: {round(gwp, 2)} kg CO2-eq / {unit}")