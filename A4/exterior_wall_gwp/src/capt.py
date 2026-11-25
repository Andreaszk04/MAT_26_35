"""
CAPT – Extract data
-------------------
Extracts the material layers of all EXTERIOR walls in an IFC file,
calculates the volume of each layer  (V = thickness * length * height)
and sums the volume per material.

Usage:
    python capt.py model.ifc
or in a notebook:
    from capt import capt
    rows, totals = capt("model.ifc")
"""
import sys
import ifcopenshell
import ifcopenshell.util.element as uel
import ifcopenshell.util.unit as uunit


# ---------- helpers --------------------------------------------------------

def is_external(wall):
    """True if Pset_WallCommon.IsExternal is True (also checks the wall type)."""
    psets = uel.get_psets(wall)  # includes inherited type psets
    return bool(psets.get("Pset_WallCommon", {}).get("IsExternal", False))


def get_wall_material(wall):
    """Return the wall's material (instance or type): IfcMaterialLayerSet, IfcMaterial, ... or None."""
    return uel.get_material(wall, should_skip_usage=True)  # usage -> layer set


def get_wall_volume(wall, scale):
    """
    Volume of the wall in m3.
    1) Qto_WallBaseQuantities: NetVolume, else GrossVolume
    2) Fallback: volume of the geometry
    """
    qto = uel.get_psets(wall, qtos_only=True).get("Qto_WallBaseQuantities", {})
    V = qto.get("NetVolume") or qto.get("GrossVolume")
    if V:
        return V * scale**3, "Qto"

    import ifcopenshell.geom
    import ifcopenshell.util.shape as ushape
    settings = ifcopenshell.geom.settings()
    shape = ifcopenshell.geom.create_shape(settings, wall)
    return ushape.get_volume(shape.geometry), "Geometry"


def get_length_height(wall, scale):
    """
    Length and height of the wall in metres.
    1) Qto_WallBaseQuantities (Length / Height)
    2) Fallback: bounding box of the geometry in the wall's local axes
       (local X = along wall, local Z = height).
    """
    qto = uel.get_psets(wall, qtos_only=True).get("Qto_WallBaseQuantities", {})
    L, H = qto.get("Length"), qto.get("Height")
    if L and H:
        return L * scale, H * scale, "Qto"

    import ifcopenshell.geom
    import ifcopenshell.util.shape as ushape
    settings = ifcopenshell.geom.settings()       # local coords, SI units (m)
    shape = ifcopenshell.geom.create_shape(settings, wall)
    return ushape.get_x(shape.geometry), ushape.get_z(shape.geometry), "Geometry"


# ---------- CAPT -----------------------------------------------------------

def capt(ifc_path):
    """
    Returns
      rows   : one dict per wall layer  (wall, material, t, L, H, volume)
      totals : {material_name: total volume [m3]}
    """
    model = ifcopenshell.open(ifc_path)
    scale = uunit.calculate_unit_scale(model)     # project length unit -> m

    rows, totals = [], {}

    for wall in model.by_type("IfcWall"):         # includes IfcWallStandardCase
        if not is_external(wall):
            continue

        mat = get_wall_material(wall)

        # Case 1: single material -> volume of the whole wall
        if mat is not None and mat.is_a("IfcMaterial"):
            V, source = get_wall_volume(wall, scale)
            rows.append(dict(wall=wall.Name, guid=wall.GlobalId, material=mat.Name,
                             t=None, L=None, H=None, volume=V, dim_source=source))
            totals[mat.Name] = totals.get(mat.Name, 0.0) + V
            continue

        # Anything else that is not a layer set -> skip
        if mat is None or not mat.is_a("IfcMaterialLayerSet"):
            kind = mat.is_a() if mat else "no material"
            print(f"! {wall.Name} ({wall.GlobalId}): {kind} – skipped")
            continue

        # Case 2: layer set -> V = t * L * H per layer
        L, H, source = get_length_height(wall, scale)

        for layer in mat.MaterialLayers:
            name = layer.Material.Name if layer.Material else "Unknown"
            t = layer.LayerThickness * scale      # m
            V = t * L * H                         # m3
            rows.append(dict(wall=wall.Name, guid=wall.GlobalId, material=name,
                             t=t, L=L, H=H, volume=V, dim_source=source))
            totals[name] = totals.get(name, 0.0) + V

    return rows, totals


def print_results(rows, totals):
    print(f"\n{'Wall':<20}{'Material':<25}{'t [m]':>8}{'L [m]':>8}{'H [m]':>8}{'V [m3]':>10}")
    print("-" * 79)
    f = lambda x, d: f"{x:>8.{d}f}" if x is not None else f"{'–':>8}"
    for r in rows:
        print(f"{str(r['wall']):<20}{r['material']:<25}{f(r['t'], 3)}"
              f"{f(r['L'], 2)}{f(r['H'], 2)}{r['volume']:>10.3f}")
    print(f"\n{'Material':<25}{'Total V [m3]':>14}")
    print("-" * 39)
    for m, v in sorted(totals.items(), key=lambda x: -x[1]):
        print(f"{m:<25}{v:>14.3f}")


if __name__ == "__main__":
    rows, totals = capt(sys.argv[1])
    print_results(rows, totals)
