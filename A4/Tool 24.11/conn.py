"""
CONN – Connect
--------------
PART 1  FILTER   Sort/rename the materials from CAPT into the general material
                 classes of Input/GWP_General_materials.xlsx.
                 The filters run one after another; each filter only receives
                 the materials the previous filter did NOT take:

                   CAPT materials
                     -> 1a Composite  (insulation AND (timber OR structure))
                          * new material "Wood, Construction"  = 7.5 % of volume
                          * new material "insulation part"     = 92.5 % of volume
                            -> sent on to 1b
                     -> 1b Insulation (name contains "insulation" -> which kind?)
                     -> 1c Other materials (wood, concrete, gypsum, steel, ...)
                     -> no match: sorted off (not used further)

PART 2  CONNECT  Attach the GWP value (column E, GWP/m3/50 years) to each class
                 -> output used by CALC.

Usage:
    from capt import capt
    from conn import conn
    rows, totals = capt("model.ifc")
    conn_result, filtered, sorted_off = conn(totals)
"""
import re
from pathlib import Path
import openpyxl

GWP_FILE = Path(__file__).resolve().parent / "Input" / "GWP_General_materials.xlsx"

WOOD_SHARE = 0.075               # wood share of composite timber/insulation layers
INSULATION_SHARE = 1 - WOOD_SHARE


# ---------- helpers --------------------------------------------------------

def _clean(name):
    """Lower case, and '-', '_', '/' -> space  (e.g. 'batt-insulation' -> 'batt insulation')."""
    return re.sub(r"[-_/]", " ", str(name).lower())


def has(name, *words):
    """True if the (cleaned) name contains ANY of the words."""
    n = _clean(name)
    return any(w.lower() in n for w in words)


def item(material, original, volume):
    """One material in the filter chain."""
    return dict(material=material, original=original, volume=volume)


# =========================================================================
# PART 1 – FILTER
# =========================================================================

# ---- 1a Composite --------------------------------------------------------

def filter_composite(items):
    """Insulation AND (timber OR structure) -> split into wood + insulation part.
    Returns (matched, remaining). The insulation part is put in 'remaining'
    so it runs through the insulation filter next."""
    matched, remaining = [], []
    for it in items:
        name = it["material"]
        if has(name, "insulation") and has(name, "timber", "structure"):
            matched.append(item("Wood, Construction", it["original"], it["volume"] * WOOD_SHARE))
            remaining.append(item(name, it["original"], it["volume"] * INSULATION_SHARE))
        else:
            remaining.append(it)
    return matched, remaining


# ---- 1b Insulation -------------------------------------------------------

def insulation_kind(name):
    """Which kind of insulation? Returns class name or None."""
    if has(name, "eps", "rigid"):
        return "Insulation, Rigid (EPS)"
    if has(name, "hemp"):
        return "Insulation, Hemp"
    if has(name, "cork"):
        return "Insulation, Cork"
    if has(name, "grass"):
        return "Insulation, Grass"
    if has(name, "cellulose"):
        return "Insulation, Paper"
    if has(name, "wood fiber"):
        return "Insulation, Woodfiber"
    if has(name, "fiberglass"):
        return "Insulation, Fiberglass"
    if has(name, "rockwool", "batt", "rock wool"):
        return "Insulation, Mineral wool"
    return None


def filter_insulation(items):
    """Name contains 'insulation' -> find the kind.
    Returns (matched, remaining, sorted_off).
    Insulation of unknown kind is sorted off (it is insulation, so the
    'other materials' filter cannot classify it correctly)."""
    matched, remaining, sorted_off = [], [], []
    for it in items:
        name = it["material"]
        if has(name, "insulation"):
            kind = insulation_kind(name)
            if kind:
                matched.append(item(kind, it["original"], it["volume"]))
            else:
                sorted_off.append(it)
        else:
            remaining.append(it)
    return matched, remaining, sorted_off


# ---- 1c Other materials --------------------------------------------------

def other_kind(name):
    """All other materials. Order matters: specific before general."""
    if has(name, "chipboard", "plywood", "clt"):
        return "Wood, Plywood"
    if has(name, "wood", "lumber", "siding", "wooden", "cladding", "timber"):
        return "Wood, Construction"
    if (has(name, "concrete") and has(name, "aerated")) or has(name, "porebeton"):
        return "Concrete, Autoclaved Aerated Concrete (AAC)"
    if has(name, "gypsum", "knauf", "gips", "yeso", "gyproc", "clima board"):
        return "Gypsum board"
    if has(name, "steel", "stål"):
        return "Steel"
    if has(name, "tile", "porcelain"):
        return "Facade tiles"
    if has(name, "brick") and has(name, "red"):
        return "Brick, Red"
    if has(name, "brick"):
        return "Brick, Not red"
    if has(name, "heavy weight") or (has(name, "concrete") and has(name, "reinforced")):
        return "Concrete, Armed"
    if has(name, "concrete"):
        return "Concrete, Not armed"
    if has(name, "cement") and has(name, "fiber"):
        return "Fiber cement, Board"
    if has(name, "cement"):
        return "Cement"
    if has(name, "calcium silicate", "plaster", "grout"):
        return "Calcium silicate"
    return None


def filter_other(items):
    """Returns (matched, sorted_off)."""
    matched, sorted_off = [], []
    for it in items:
        kind = other_kind(it["material"])
        if kind:
            matched.append(item(kind, it["original"], it["volume"]))
        else:
            sorted_off.append(it)
    return matched, sorted_off


# ---- Filter chain --------------------------------------------------------

def conn_filter(totals):
    """
    totals : {material name: volume [m3]}  (from CAPT)
    Returns
      filtered   : list of {material (class), original, volume}
      sorted_off : list of {material, original, volume}
    """
    items = [item(name, name, V) for name, V in totals.items()]

    comp, rest = filter_composite(items)
    ins, rest, off_ins = filter_insulation(rest)
    oth, off_oth = filter_other(rest)

    return comp + ins + oth, off_ins + off_oth


# =========================================================================
# PART 2 – CONNECT WITH GWP
# =========================================================================

def load_gwp(path=GWP_FILE):
    """{class: GWP/m3/50 years}  (column B = class, column E = GWP 50 years)."""
    ws = openpyxl.load_workbook(path, data_only=True).active
    gwp = {}
    for row in ws.iter_rows(min_row=1, max_col=5, values_only=True):
        name, value = row[1], row[4]
        if name and isinstance(value, (int, float)):   # skips header/empty rows
            gwp[str(name).strip()] = float(value)
    return gwp


def conn_gwp(filtered, gwp_path=GWP_FILE):
    """
    Sums volume per class and attaches the GWP value.
    Returns {class: {"volume": m3, "gwp_factor": GWP/m3/50 yr}}  -> input for CALC
    """
    gwp = load_gwp(gwp_path)
    result = {}
    for it in filtered:
        cls = it["material"]
        if cls not in gwp:
            raise KeyError(f"Class '{cls}' not found in {Path(gwp_path).name}")
        r = result.setdefault(cls, {"volume": 0.0, "gwp_factor": gwp[cls]})
        r["volume"] += it["volume"]
    return result


# =========================================================================
# CONN
# =========================================================================

def conn(totals, gwp_path=GWP_FILE):
    """
    Returns
      conn_result : {class: {"volume", "gwp_factor"}}   -> used by CALC
      filtered    : details, which original material went to which class
      sorted_off  : materials not used further
    """
    filtered, sorted_off = conn_filter(totals)
    conn_result = conn_gwp(filtered, gwp_path)
    return conn_result, filtered, sorted_off


def print_conn(conn_result, filtered, sorted_off):
    print(f"\n{'Original material':<45}{'Class':<45}{'V [m3]':>10}")
    print("-" * 100)
    for it in filtered:
        print(f"{it['original'][:44]:<45}{it['material']:<45}{it['volume']:>10.3f}")

    print(f"\n{'Class':<45}{'V [m3]':>10}{'GWP/m3/50yr':>14}")
    print("-" * 69)
    for cls, r in sorted(conn_result.items(), key=lambda x: -x[1]["volume"]):
        print(f"{cls:<45}{r['volume']:>10.3f}{r['gwp_factor']:>14.2f}")

    if sorted_off:
        print("\nSorted off (no match):")
        for it in sorted_off:
            print(f"  {it['original'][:43]:<43}{it['volume']:>10.3f}")


if __name__ == "__main__":
    import sys
    from capt import capt
    rows, totals = capt(sys.argv[1])
    print_conn(*conn(totals))
