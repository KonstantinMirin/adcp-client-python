# Route A / Route B spike

Three hand-written schemas (`cases.py`), lowered once into dmcg 0.86.0's model layer
(`route_a.py`) and once straight to text (`route_b.py`), graded by `codegen.harness`
(`grade.py`). `out_a.py` and `out_b.py` are the emitted modules. `census.py` is the
root-shape census over the portable bundle that sizes the plan's steps.

```bash
env -u VIRTUAL_ENV uv sync --all-extras
env -u VIRTUAL_ENV uv run --no-sync python -I docs/analysis/spike/route_a.py   # writes out_a.py
env -u VIRTUAL_ENV uv run --no-sync python -I docs/analysis/spike/route_b.py   # writes out_b.py
PYTHONPATH=. env -u VIRTUAL_ENV uv run --no-sync python docs/analysis/spike/grade.py a
PYTHONPATH=. env -u VIRTUAL_ENV uv run --no-sync python docs/analysis/spike/grade.py b
env -u VIRTUAL_ENV uv run --no-sync python docs/analysis/spike/census.py
```

The decision the measurement supports is in `docs/analysis/rebuild-plan.md` §1.
