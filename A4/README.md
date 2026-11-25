# A4 – Exterior wall GWP tool

> Fill in the parts marked **TODO** – they need the group's own A2 use case and project report.

## About the tool

### Problem / claim
**TODO:** State the claim from the Advanced Building Design report that the tool checks
(quote it and give the page).

### Where the problem was found
**TODO:** Report name, section and page, and the A2 use case it comes from.

### Description of the tool
The tool calculates the global warming potential (GWP) of all **exterior walls** in an IFC
model over a 50-year period and compares it with the BR18 limit values.

| Step | File | What it does |
| --- | --- | --- |
| CAPT | `capt.py` | Finds walls with `Pset_WallCommon.IsExternal = True`, reads each material layer and calculates its volume `V = thickness × length × height` |
| CONN | `conn.py` | Sorts the IFC material names into general material classes (composite → insulation → other materials) and attaches the GWP factor from `Input/GWP_General_materials.xlsx` |
| CALC | `calc.py` | GWP per class = volume × GWP factor; total GWP divided by floor area and 50 years |
| CHEK | `chek.py` | Compares kg CO2e/m²/year with the BR18 limit values |
| COMM | `comm.py` | Report: GWP, BR18 check, GWP per material, materials not included |

`exterior_wall_gwp/src/main.py` contains the callable function `analyse(model)`, which runs
the steps in this order. Another tool can reuse it:

```python
from exterior_wall_gwp.src.main import analyse
result = analyse(model)               # asks for the floor area
result = analyse(model, area=1250.0)  # or give it directly
```

### Folder structure

```text
A4/
  README.md                   this report
  CHANGELOG.md                dated changes
  requirements.txt            Python packages
  settings.py                 MODEL_PATH – path to your local IFC
  runall.py                   runs the analysis and saves the result
  exterior_wall_gwp.ids       IDS: what the model must contain
  exterior_wall_gwp/
    src/
      main.py                 analyse(model)
      capt.py conn.py calc.py chek.py comm.py
      Input/GWP_General_materials.xlsx
    results/run-.../result.json
  tests/
    test_exterior_wall_gwp.py
```

### Instructions to run the tool
1. Install the packages (once):
   ```bash
   python -m venv .venv
   .venv/bin/python -m pip install -r requirements.txt        # macOS / Linux
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt   # Windows
   ```
2. Set the path to your IFC model in `settings.py`, e.g. `MODEL_PATH = r"C:\Models\building.ifc"`.
   The IFC model is **not** part of the repository.
3. Run from the `A4` folder:
   ```bash
   python runall.py
   ```
4. Enter the floor area of the building when asked.
5. The report is printed in the terminal, and all results are saved in
   `exterior_wall_gwp/results/run-<time>/result.json`.

Run the tests: `python -m unittest discover -s tests`

## Advanced Building Design

### Design stage (A, B, C or D)
**TODO:** Which stage and why.

### Which subjects might use it?
**TODO:** e.g. sustainability, architecture, structure.

### What information is required in the model?
Checked by `exterior_wall_gwp.ids`:
- every `IfcWall` has `Pset_WallCommon.IsExternal` (walls without it are left out),
- exterior walls have an `IfcMaterialLayerSet` with named materials and layer thicknesses
  (or a single `IfcMaterial`),
- exterior walls have `Qto_WallBaseQuantities.Length` and `Height`
  (if missing, the tool uses the wall geometry instead).

The floor area of the building is entered by the user when the tool runs.
