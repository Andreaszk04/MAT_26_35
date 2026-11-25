# Changelog

## 2026-11-25

- Packaged the group's exterior wall GWP tool (CAPT, CONN, CALC, CHEK, COMM) in the
  course IFC starter structure: `exterior_wall_gwp/src/`, registered in `runall.py`.
- Added `exterior_wall_gwp/src/main.py` with the callable `analyse(model)`. It runs the
  existing modules in order and returns a JSON-compatible result; the modules themselves
  are unchanged.
- Results are written to `exterior_wall_gwp/results/run-.../result.json`.
- Added `exterior_wall_gwp.ids` (model requirements) and tests in `tests/`.
- Based on the course IFC starter (node-comply-template, 2026-11-16).
