"""
A4 – Exterior wall insulation tool (group 35)

1. extracts the material layers and U-value of the exterior walls (IFC),
2. calculates U-value and GWP of each wall type (BR18 Table 7),
3. replaces the insulation with alternatives (e.g. hemp) of equal thermal resistance
   and compares thickness and GWP.

Run:  python main.py
"""
from pathlib import Path

import ifcopenshell

import comm
from wall_insulation_tool import analyse

# --- Point this to the model on your own machine (the IFC is NOT part of the repo) ---
model_path = Path("/Users/fmtg/Downloads/26-08-D-Arch - Copy.ifc")
if not model_path.is_file():
    raise FileNotFoundError(f"No file found at {model_path}!")

# Optional: only analyse these wall types (None = all exterior wall types)
WALL_TYPES = None   # e.g. ["Basic Wall:M-Exterior-Double Brick (390mm)"]

OUTPUT = Path(__file__).resolve().parent / "output"


def main():
    print(f"Opening {model_path.name} ...")
    model = ifcopenshell.open(model_path)

    result = analyse(model, wall_types=WALL_TYPES)

    comm.COMM_CONSOLE(result)
    xlsx = comm.COMM_EXCEL(result, OUTPUT / "wall_insulation_results.xlsx")
    png = comm.COMM_CHART(result, OUTPUT / "insulation_gwp_comparison.png")
    print(f"\nResults written to:\n  {xlsx}\n  {png}")


if __name__ == "__main__":
    main()
