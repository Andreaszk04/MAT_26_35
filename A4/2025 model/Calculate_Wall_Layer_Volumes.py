from collections import defaultdict
from Defining_Exterior_Walls import ifc_file, selected_wall_type

unit_assignment = ifc_file.by_type("IfcUnitAssignment")

if not unit_assignment:
    length_unit_str = "UNKNOWN"
    conversion_factor = 1.0
else:
    length_units = [
        u for u in unit_assignment[0].Units
        if u.is_a("IfcSIUnit") and u.UnitType == "LENGTHUNIT"
    ]
    if not length_units:
        length_unit_str = "UNKNOWN"
        conversion_factor = 1.0
    else:
        length_unit = length_units[0]
        prefix = length_unit.Prefix
        name = length_unit.Name
        if prefix == "MILLI":
            length_unit_str = "MILLIMETERS"
            conversion_factor = 0.001
        elif prefix == "CENTI":
            length_unit_str = "CENTIMETERS"
            conversion_factor = 0.01
        elif name == "METRE" and prefix is None:
            length_unit_str = "METERS"
            conversion_factor = 1.0
        else:
            length_unit_str = f"{prefix or ''}{name}"
            conversion_factor = 1.0
        print("----------------------------------------------")
        print(f"Defined in the IFC model is the following unit for material layer thickess: {length_unit_str}")
        print("----------------------------------------------")

def get_wall_identifier(wall):
    if wall.ObjectType:
        return wall.ObjectType
    elif wall.Name:
        return wall.Name
    else:
        return f"Unnamed wall #{wall.id()}"

selected_walls = [
    wall
    for wall in (ifc_file.by_type("IfcWall") + ifc_file.by_type("IfcWallStandardCase"))
    if get_wall_identifier(wall) == selected_wall_type
]

def get_wall_area(wall):
    for rel in getattr(wall, "IsDefinedBy", []):
        if rel.is_a("IfcRelDefinesByProperties"):
            prop_def = rel.RelatingPropertyDefinition
            if prop_def.is_a("IfcPropertySet"):
                for prop in prop_def.HasProperties:
                    if prop.Name.lower() in ["area", "grosssidearea", "netsidearea"]:
                        nominal_value = getattr(prop, "NominalValue", None)
                        if nominal_value:
                            return float(nominal_value.wrappedValue)
    print(f"No area info for wall {get_wall_identifier(wall)}. Add area in BIM model.")
    return None

def get_layer_thickness(layer):
    if hasattr(layer, "LayerThickness") and layer.LayerThickness:
        return layer.LayerThickness
    material = getattr(layer, "Material", None)
    if not material:
        return None
    if hasattr(material, "ForLayerSet"):
        layer_set = material.ForLayerSet
        if hasattr(layer_set, "MaterialLayers"):
            for l in layer_set.MaterialLayers:
                if hasattr(l, "LayerThickness") and l.LayerThickness:
                    return l.LayerThickness
    return None

def calculate_layer_volumes(wall):
    volumes = []
    area = get_wall_area(wall)
    if area is None:
        return volumes
    for rel in ifc_file.get_inverse(wall):
        if rel.is_a("IfcRelAssociatesMaterial"):
            mat = rel.RelatingMaterial
            if mat.is_a("IfcMaterialLayerSetUsage"):
                layer_set = mat.ForLayerSet
            elif mat.is_a("IfcMaterialLayerSet"):
                layer_set = mat
            else:
                continue
            for layer in layer_set.MaterialLayers:
                thickness = get_layer_thickness(layer)
                material_name = getattr(layer.Material, "Name", "Unnamed Material")
                if thickness is None:
                    print(f"No thickness info for layer '{material_name}' in wall {get_wall_identifier(wall)}")
                    continue
                if conversion_factor != 1.0:
                    thickness *= conversion_factor
                volume = thickness * area
                volumes.append((material_name, volume, thickness))
            break
    return volumes

# Store both volume and thickness
layer_volumes_summary = defaultdict(lambda: {"volume": 0, "thickness": None})
for wall in selected_walls:
    wall_volumes = calculate_layer_volumes(wall)
    for material_name, volume, thickness in wall_volumes:
        layer_volumes_summary[material_name]["volume"] += volume
        layer_volumes_summary[material_name]["thickness"] = thickness

print("\nTotal volumes per material:")
for material, data in layer_volumes_summary.items():
    print(f"- Material name: {material} | Volume: {data['volume']:.3f} m³ | Layer thickness: {data['thickness']} m")

print("\n----------------------------------------------")
