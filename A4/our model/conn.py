"""
CONN – Connect: "How does this information relate?"

Connects each IFC material layer to
  * a thermal property (lambda or a fixed R for air layers), and
  * a BR18 Table 7 entry (Sorterings ID),
using the ordered rules in input/config.json.
"""
import re


def CONN_MATERIAL(layer, config):
    """Return the first rule in config['materials'] whose regex matches the layer's
    material name (case-insensitive). Returns {} when nothing matches."""
    name = layer["material"]
    for rule in config["materials"]:
        if re.search(rule["match"], name, flags=re.IGNORECASE):
            return rule
    return {}


def CONN_LAMBDA(layer, rule):
    """Thermal conductivity for a layer -> (lambda, source).
    A value stored in the IFC wins over the value in config."""
    if layer.get("lambda_ifc"):
        return layer["lambda_ifc"], "IFC material property"
    if rule.get("lambda"):
        return float(rule["lambda"]), "config (assumed design value)"
    return None, "missing"


def CONN_TABLE7(sorterings_id, table7):
    """Look up one Table 7 row -> dict with the values needed for the GWP calculation."""
    if not sorterings_id or sorterings_id not in table7.index:
        return None
    row = table7.loc[sorterings_id]
    if hasattr(row, "ndim") and row.ndim > 1:  # duplicated id -> take the first
        row = row.iloc[0]

    def num(col):
        value = row.get(col)
        try:
            value = float(value)
        except (TypeError, ValueError):
            return 0.0
        return 0.0 if value != value else value  # NaN -> 0

    return {
        "sorterings_id": sorterings_id,
        "epd_name": str(row["Navn DK"]),
        "unit": str(row["Deklareret enhed (FU)"]).strip(),
        "mass_factor": num("Masse faktor"),
        "mass_unit": str(row["Masse enhed"]).strip().replace("³", "3").replace("²", "2"),
        "gwp_A1A3": num("Global Opvarmning, modul A1-A3"),
        "gwp_C3": num("Global Opvarmning, modul C3"),
        "gwp_C4": num("Global Opvarmning, modul C4"),
        "gwp_D": num("Global Opvarmning, modul D"),
    }
