import ifcopenshell
from Model import ifc_file



# Find all exterior walls
exterior_walls = []

for wall in ifc_file.by_type("IfcWall") + ifc_file.by_type("IfcWallStandardCase"):
    is_external = False

    # Try direct attribute first
    if hasattr(wall, "IsExternal") and wall.IsExternal:
        is_external = True
    else:
        # Check for property sets
        for rel in getattr(wall, "IsDefinedBy", []):
            if rel.is_a("IfcRelDefinesByProperties"):
                prop_def = rel.RelatingPropertyDefinition
                if prop_def.is_a("IfcPropertySet"):
                    for prop in prop_def.HasProperties:
                        if prop.Name.lower() == "isexternal":
                            value = getattr(prop, "NominalValue", None)
                            if value and getattr(value, "wrappedValue", False):
                                is_external = True
                                break
                if is_external:
                    break

    if is_external:
        exterior_walls.append(wall)

# Categorize exterior walls by number of material layers
walls_with_one_layer = []
walls_with_multiple_layers = []

for wall in exterior_walls:
    for rel in ifc_file.get_inverse(wall):
        if rel.is_a("IfcRelAssociatesMaterial"):
            mat = rel.RelatingMaterial

            # Support both LayerSetUsage and LayerSet
            if mat.is_a("IfcMaterialLayerSetUsage"):
                layer_set = mat.ForLayerSet
            elif mat.is_a("IfcMaterialLayerSet"):
                layer_set = mat
            else:
                continue

            num_layers = len(layer_set.MaterialLayers)
            if num_layers > 1:
                walls_with_multiple_layers.append(wall)
            elif num_layers == 1:
                walls_with_one_layer.append(wall)
            break

# Get name or ID
def get_wall_identifier(wall):
    if wall.ObjectType:
        return wall.ObjectType
    elif wall.Name:
        return wall.Name
    else:
        return f"Unnamed wall #{wall.id()}"

# Collect unique wall types
unique_multi = sorted(set(get_wall_identifier(w) for w in walls_with_multiple_layers))
unique_single = sorted(set(get_wall_identifier(w) for w in walls_with_one_layer))

# Combine both categories (one layers + multiple layers) into one list for user selection
all_wall_types = unique_multi + unique_single

print("Exterior wall types:")
print("\n-- Walls with MORE than one material layer --")
for i, wtype in enumerate(unique_multi, start=1):
    print(f"{i}. {wtype}")

start_index_single = len(unique_multi) + 1
print("\n-- Walls with ONE material layer --")
for i, wtype in enumerate(unique_single, start=start_index_single):
    print(f"{i}. {wtype}")

print(f"\nTotal exterior wall types: {len(all_wall_types)}")

# User selects wall type to later calculate GWP
while True:
    try:
        choice = int(input("\nChoose which exterior wall you want to calculate GWP for and enter the wall number here: "))
        if 1 <= choice <= len(all_wall_types):
            selected_wall_type = all_wall_types[choice - 1]
            break
        else:
            print("Please enter a valid number from the list.")
    except ValueError:
        print("Invalid input. Please enter a number.")

print(f"\n You selected: {selected_wall_type} \n")

# `selected_wall_type` can be loaded into another code-file


