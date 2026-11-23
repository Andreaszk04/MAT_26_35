"""
CONN - Connect: "How does this information relate?"

Connects each IFC material name to a BR18 Table 7 entry. The material name is
read with if-statements: first the main category (e.g. is_insulation), then a
closer look at the name (e.g. is_stone, is_glass, is_eps). The building part
(Exterior wall / Roof / Floor) is used where the right Table 7 entry differs
between parts (e.g. roof insulation vs. wall insulation).

CONN_MATERIAL returns a key; input/material_data.json maps that key to the
Table 7 'Sorterings ID', the lifetime and (for insulation) lambda.
"""
import re


# Short abbreviations that must be whole words ('stairs' is not 'air', 'steps' is not 'eps')
WHOLE_WORDS = {"air", "eps", "xps", "pir", "pur", "osb", "clt", "pvc", "dpm", "felt", "leca"}


def _has(name, *words):
    """True if any of the words appears in the (lower-case) material name."""
    for w in words:
        if w in WHOLE_WORDS:
            if re.search(rf"\b{re.escape(w)}\b", name):
                return True
        elif w in name:
            return True
    return False


def CONN_MATERIAL(material_name, part):
    """IFC material name + building part -> material key (or None if unknown)."""
    name = material_name.lower()

    # --- air / cavities: no material, no GWP --------------------------------
    is_air = _has(name, "air", "cavity", "luft", "hulrum")
    if is_air and not _has(name, "barrier", "spærre"):
        return "air"

    # --- terrain / landscaping: not part of the building, no GWP --------------
    if _has(name, "earth", "soil", "grass", "jord", "græs", "muld"):
        return "landscape"

    # --- insulation -----------------------------------------------------------
    is_top_board = _has(name, "topplade", "toprock", "top board")
    is_insulation = is_top_board or _has(name, "insulation", "isolering", "wool", "uld", "eps",
                                         "xps", "pir", "polystyren", "batts")
    if is_insulation:
        is_stone = _has(name, "stone", "sten", "rock")
        is_glass = _has(name, "glass", "glas")
        is_eps = _has(name, "eps", "expanded polystyren")
        is_xps = _has(name, "xps", "extruded")
        is_pir = _has(name, "pir", "polyiso", "pur")
        is_wood_fibre = _has(name, "wood fib", "woodfib", "træfiber")
        is_hemp = _has(name, "hemp", "hamp")
        is_cellulose = _has(name, "cellulose", "papir", "paper")
        is_rigid = _has(name, "rigid", "board", "hard", "hård")
        is_batt = _has(name, "batt", "flexible", "fleksibel")
        is_pressure = _has(name, "pressure", "trykfast", "terrain", "ground", "terræn")
        is_grey = _has(name, "grey", "gray", "grå", "neopor")

        if is_eps:
            return "eps_grey" if is_grey else "eps_white"
        if is_xps:
            return "xps"
        if is_pir:
            return "pir"
        if is_wood_fibre:
            return "wood_fibre"
        if is_hemp:
            return "hemp"
        if is_cellulose:
            return "cellulose"
        # mineral wool (stone wool, glass wool, or unspecified insulation)
        if is_top_board:
            return "mineral_wool_roof_top_board"
        if is_batt:                       # batts between joists/studs - any part
            return "mineral_wool_flexible"
        if part == "Roof":
            return "mineral_wool_roof"
        if part == "Floor" and is_pressure:
            return "mineral_wool_floor"
        if is_rigid:
            return "mineral_wool_rigid"
        if is_stone or is_glass:
            return "mineral_wool_flexible"
        return "mineral_wool_flexible"  # unspecified insulation -> assumed mineral wool

    # --- membranes and textiles (checked before 'roofing' and 'tile':
    #     'damp-pROOFING' contains 'roofing' and 'geoTEXTILE' contains 'tile') ----
    if _has(name, "vapour", "vapor", "dampspærre", "polyethylen", "pe foil", "pe-folie"):
        return "vapour_barrier"
    if _has(name, "damp-proof", "damp proof", "dampproof", "dpm", "fugtspærre"):
        return "damp_proofing"
    if _has(name, "geotextile", "root barrier", "rodspærre", "fiberdug", "filter"):
        return "geotextile"
    if _has(name, "epdm"):
        return "epdm_membrane"
    if _has(name, "roofing", "bitumen", "tagpap", "asphalt", "felt"):
        return "roofing_felt"
    if _has(name, "membrane"):
        return "roofing_felt" if part == "Roof" else "vapour_barrier"

    # --- boards ---------------------------------------------------------------
    if _has(name, "silent board", "knauf", "acoustic board", "akustik"):
        return "gypsum_board_acoustic"
    if _has(name, "gypsum", "gips", "plasterboard", "drywall"):
        return "gypsum_board"
    if _has(name, "glass", "glas") and not _has(name, "wool", "uld", "fibre", "fiber"):
        return "glass"
    if _has(name, "gravel", "grus", "drainage", "pebble"):
        return "gravel"
    if _has(name, "osb"):
        return "osb"
    if _has(name, "plywood", "krydsfiner"):
        return "plywood"
    if _has(name, "fibre cement", "fiber cement", "fibercement"):
        return "fibre_cement_board"

    # --- masonry, concrete, render ----------------------------------------------
    if _has(name, "aerated", "porebeton", "aircrete", "gasbeton"):
        return "aerated_concrete"
    if _has(name, "lightweight", "letklinker", "leca", "letbeton"):
        return "lightweight_concrete_block"
    if _has(name, "screed", "flydemørtel", "avretning", "levelling"):
        return "screed"
    if _has(name, "concrete", "beton", "cast-in-place", "precast"):
        return "concrete"
    if _has(name, "roof tile", "tagsten", "clay tile"):
        return "roof_tile_clay"
    if _has(name, "brick", "tegl", "mursten", "masonry"):
        return "brick_yellow" if _has(name, "yellow", "gul") else "brick"
    if _has(name, "plaster", "render", "puds", "stucco", "mortar", "mørtel"):
        return "render"

    # --- light metal profiles (before timber: 'Metal Stud' is not a timber stud) --
    is_metal = _has(name, "metal", "steel", "stål")
    if is_metal and _has(name, "furring", "stud", "profile", "profil", "lægte"):
        return "steel_light_profiles"

    # --- timber ---------------------------------------------------------------
    if _has(name, "clt", "cross laminated", "krydslamineret"):
        return "clt"
    if _has(name, "parquet", "parket", "hardwood floor"):
        return "parquet"
    if _has(name, "wood", "timber", "træ", "softwood", "lumber", "joist", "stud",
            "rafter", "spær", "cladding", "beklædning"):
        return "timber"

    # --- floor finishes -------------------------------------------------------
    if _has(name, "linoleum"):
        return "linoleum"
    if _has(name, "vinyl", "pvc"):
        return "pvc_floor"
    if _has(name, "tile", "flise", "klinker", "ceramic", "keramik"):
        return "ceramic_tiles"

    # --- metals ---------------------------------------------------------------
    if _has(name, "alumin"):
        return "aluminium"
    if _has(name, "zinc", "zink"):
        return "zinc"
    if _has(name, "steel", "stål", "metal"):
        return "steel_sheet" if _has(name, "finish", "paint", "sheet", "plade", "cladding", "deck") \
            else "steel"

    return None


def CONN_TABLE7(key, material_data, table7):
    """Material key -> dict with Table 7 values, lifetime and lambda.
    Returns None if the key or its Sorterings ID is unknown."""
    if key is None or key not in material_data:
        return None
    data = material_data[key]
    table7_id = data.get("table7_id")
    if not table7_id:  # e.g. air: known material without GWP
        return {"key": key, "sorterings_id": None, "epd_name": "(no GWP)", **data}
    if table7_id not in table7.index:
        return None
    row = table7.loc[table7_id]

    def num(col):
        try:
            value = float(row[col])
        except (TypeError, ValueError):
            return 0.0
        return 0.0 if value != value else value  # NaN -> 0

    def clean(text):
        return str(text).strip().replace("³", "3").replace("²", "2")

    return {
        "key": key,
        "sorterings_id": table7_id,
        "epd_name": str(row["Navn DK"]).strip(),
        "unit": clean(row["Deklareret enhed (FU)"]),
        "mass_factor": num("Masse faktor"),
        "mass_unit": clean(row["Masse enhed"]),
        "gwp_A1A3": num("Global Opvarmning, modul A1-A3"),
        "gwp_C3": num("Global Opvarmning, modul C3"),
        "gwp_C4": num("Global Opvarmning, modul C4"),
        "gwp_D": num("Global Opvarmning, modul D"),
        "lifetime": data.get("lifetime"),
        "lifetime_source": data.get("lifetime_source", ""),
        "lambda": data.get("lambda"),
        "board_thickness_m": data.get("board_thickness_m"),
        "max_thickness_m": data.get("max_thickness_m"),
    }
