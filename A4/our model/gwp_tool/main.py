"""
A4 - Exterior wall GWP tool

Calculates the GWP of the exterior walls of an IFC model with BR18 Table 7 data,
per wall type and per m2 floor area per year over 50 years, and shows the walls'
share of the BR18 limit. Full details are written to output/gwp_results.csv.

Run:  python main.py
"""
from pathlib import Path

import ifcopenshell

import comm
from gwp_tool import analyse

# --- Point this to the model on your own machine (the IFC is NOT part of the repo) ---
model_path = Path(__file__).resolve().parent / "input" / "26-08-D-Arch.ifc"  # change if your model is elsewhere

OUTPUT = Path(__file__).resolve().parent / "output"


def main():
    if not model_path.is_file():
        raise FileNotFoundError(f"No file found at {model_path}!")
    print(f"Opening {model_path.name} ...")
    model = ifcopenshell.open(model_path)

    result = analyse(model)

    comm.COMM_RESULT(result)
    csv_path = comm.COMM_CSV(result, OUTPUT / "gwp_results.csv")
    print(f"\nAll details per wall type and material: {csv_path}")


if __name__ == "__main__":
    main()
