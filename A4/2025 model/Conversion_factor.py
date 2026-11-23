from Tabel_7_materials_assigned import results, material_units

converted_volumes = {}

for r in results:
    material_name = r["Material (IFC)"]
    epd_name = r["Navn DK"]  # from Tabel_7_materials_assigned
    volume_m3 = r["Volume [m³]"]
    excel_unit = r["Enhed"]

    # Ensure Masse faktor and Masse enhed are clean
    masse_faktor = r.get("Masse faktor")
    try:
        masse_faktor = float(masse_faktor) if masse_faktor is not None else None
    except (TypeError, ValueError):
        masse_faktor = None

    masse_enhed = r.get("Masse enhed")
    if masse_enhed:
        masse_enhed = str(masse_enhed).strip().replace("³", "3")  # normalize m³ to m3

    layer_thickness = r.get("Layer thickness")

    # Conversion 
    if excel_unit == "m³":
        converted_volume = volume_m3

    elif excel_unit in ["m²", "m² with R=1 m²K/W"]:
        if not layer_thickness or layer_thickness == 0:
            print(f"Cannot convert '{material_name}' from m³ to m²: missing layer thickness.")
            converted_volume = None
        else:
            converted_volume = volume_m3 / layer_thickness
            #print(f"Converted '{material_name}' from m³ to m² using layer thickness {layer_thickness} m")

    elif excel_unit == "kg":
        if masse_faktor and masse_enhed in ["kg/m3"]:
            converted_volume = volume_m3 * masse_faktor
            #print(f"Converted '{material_name}' from m³ to kg using Masse faktor {masse_faktor} {masse_enhed} from EPD '{epd_name}'")
        elif masse_enhed in ["g/cm3", "g/cm³"]:
            converted_volume = (volume_m3 * 1000000 * masse_faktor) / 1000
            #print(f"Converted '{material_name}' from m³ to kg using Masse faktor {masse_faktor} {masse_enhed} from EPD '{epd_name}'")
        else:
            print(f"Cannot convert '{material_name}' to kg: missing or incompatible Masse Enhed.")
            converted_volume = None

    elif excel_unit == "ton":
        if masse_faktor and masse_enhed in ["kg/m3"]:
            converted_volume = volume_m3 * masse_faktor / 1000
            #print(f"Converted '{material_name}' from m³ to ton using Masse faktor {masse_faktor} {masse_enhed} from EPD '{epd_name}'")
        else:
            print(f"Cannot convert '{material_name}' to ton: missing or incompatible Masse Enhed.")
            converted_volume = None

    else:
        print(f"Unit '{excel_unit}' for {material_name} not handled.")
        converted_volume = None

    converted_volumes[material_name] = {
        "volume": converted_volume,
        "epd_name": epd_name
    }

# Results
#print("----------------------------------------------")
#print("\nConverted volumes per material:")
#for material, data in converted_volumes.items():
    #vol = data["volume"]
    #epd_name = data["epd_name"]
    #unit = material_units.get(material, '')

    #if vol is None:
        #print(f"- IFC material: {material} | EPD: {epd_name} | Conversion failed ({unit})")
    #else:
        #print(f"- IFC material: {material} | EPD: {epd_name} | Quantity: {round(vol, 2)} {unit}")
#print("----------------------------------------------")

# Store converted volumes similar to material_units
converted_results = {}  # dict mapping IFC material name → converted volume
converted_units = {}    # dict mapping IFC material name → unit (same as material_units)

for r in results:
    material_name = r["Material (IFC)"]
    converted_data = converted_volumes.get(material_name, {})
    converted_results[material_name] = converted_data.get("volume")
    converted_units[material_name] = r["Enhed"]
