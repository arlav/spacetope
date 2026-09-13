# topologicpy behaviour experiments (2026-09-13)

Throwaway scripts run against topologicpy 0.9.57 / topologic_core 8.0.0 on Python 3.11.9 (macOS arm64) to establish the facts in `../TOPOLOGICPY_NOTES.md`. Not tests; port the cases into `tests/test_topologic_smoke.py` in M0.

- `exp.py` — two-box cases: exact touch, gaps, overlap, partial abut, stacked, disjoint; dictionaries through `ByCells`; pickling.
- `exp2b.py` — Graph.ByTopology flag semantics on rooms + corridor + doors/windows; apertures.
- `exp3.py` — dictionary survival through Merge/SelfMerge/selectors; multiprocessing gotchas.
- `exp4.py` — serialisation: JSON/BREP/Geometry/MeshData/OBJ/Plotly round-trips.
- `exp5.py` — timing at 25/98/196 cells; threads.
- `sigs.py` — `inspect.signature` dump of the methods we rely on.

Run with `python docs/experiments/exp.py` inside the project venv (each has a `__main__` guard where processes are spawned).
