"""
Exterior wall GWP - entry point for the A4 runner.

analyse(model) is the one callable function (Working Together / IFC starter):

    from exterior_wall_gwp.src.main import analyse
    result = analyse(my_model)

It only connects the group's modules in order - it does not change them:

    CAPT (capt.py) -> CONN (conn.py) -> CALC (calc.py) -> CHEK (chek.py) -> COMM (comm.py)

CALC asks for the floor area in the terminal unless `area` is given.
The returned dictionary is JSON-compatible, so runall.py can save it as result.json.
"""
import sys
from contextlib import contextmanager
from pathlib import Path

import ifcopenshell

# The modules import each other by file name (e.g. comm.py: `from chek import chek`),
# so this folder has to be on the import path.
SRC = Path(__file__).resolve().parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import capt as CAPT  # noqa: E402
import conn as CONN  # noqa: E402
import calc as CALC  # noqa: E402
import chek as CHEK  # noqa: E402
import comm as COMM  # noqa: E402


@contextmanager
def _use_loaded_model(model):
    """capt.capt() takes a file path and opens it itself. The runner has already
    opened the model, so while CAPT runs, 'opening' simply returns that model.
    Nothing is read twice and the model is not changed."""
    original = ifcopenshell.open
    ifcopenshell.open = lambda *args, **kwargs: model
    try:
        yield
    finally:
        ifcopenshell.open = original


def analyse(model, area=None):
    """
    model : an opened IfcOpenShell model
    area  : floor area of the building [m2]; if None, CALC asks for it

    Returns a JSON-compatible dict with the results of every step.
    """
    with _use_loaded_model(model):
        rows, totals = CAPT.capt("model")                       # CAPT
    conn_result, filtered, sorted_off = CONN.conn(totals)       # CONN
    calc_result = CALC.calc(conn_result, area=area)             # CALC
    check_text = CHEK.chek(calc_result)                         # CHEK
    report = COMM.comm(calc_result, sorted_off)                 # COMM

    print("\n" + report)

    return {
        "scope": "Exterior walls (Pset_WallCommon.IsExternal = True)",
        "units": {"volume": "m3", "gwp": "kg CO2e over 50 years",
                  "area": "m2", "gwp_m2_year": "kg CO2e/m2/year"},
        "gwp_total": calc_result["gwp_total"],
        "floor_area": calc_result["area"],
        "gwp_m2_year": calc_result["gwp_m2_year"],
        "materials": calc_result["materials"],
        "check": check_text,
        "not_included": sorted_off,
        "material_mapping": filtered,
        "wall_layers": rows,
        "report": report,
    }
