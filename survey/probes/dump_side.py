"""One side's public declarations, with the identity reading 10 keys an alias on.

Follows `survey/dropin_blocking.py`'s rules: a model's identity is its WIRE field set, an
enum's is its value list, and a constrained scalar's is its constraint set.  Nothing is
decided here -- this writes the two populations the node key is applied over.
"""
import enum, importlib, json, pkgutil, sys, typing
from pathlib import Path

ROOT = sys.argv[1]            # adcp.types.domains  |  adcp.types._schemas
OUT = Path(sys.argv[2])


def constraint_set(obj):
    out = {}
    for md in typing.get_args(obj)[1:] if typing.get_origin(obj) is typing.Annotated else ():
        for inner in getattr(md, "metadata", ()) or ():
            for key in ("pattern", "max_length", "min_length", "ge", "le", "gt", "lt",
                        "max_digits", "decimal_places", "multiple_of"):
                value = getattr(inner, key, None)
                if value is not None:
                    out[key] = str(value)
        for key in ("pattern", "max_length", "min_length", "ge", "le", "gt", "lt"):
            value = getattr(md, key, None)
            if value is not None:
                out[key] = str(value)
    return out


def identity(obj):
    if isinstance(obj, type) and issubclass(obj, enum.Enum):
        return ["enum", sorted(str(m.value) for m in obj)]
    fields = getattr(obj, "model_fields", None)
    if isinstance(fields, dict):
        return ["model", sorted((fi.alias or n) for n, fi in fields.items())]
    if typing.get_origin(obj) is typing.Annotated:
        cons = constraint_set(obj)
        return ["scalar", sorted(f"{k}={v}" for k, v in cons.items())] if cons else ["scalar", []]
    return None


root = importlib.import_module(ROOT)
rows, bad = {}, []
for found in pkgutil.walk_packages(root.__path__, root.__name__ + "."):
    try:
        module = importlib.import_module(found.name)
    except Exception as exc:
        bad.append([found.name, f"{type(exc).__name__}: {exc}"])
        continue
    for name, obj in list(vars(module).items()):
        if name.startswith("_"):
            continue
        ident = identity(obj)
        if ident is None:
            continue
        if isinstance(obj, type) and getattr(obj, "__module__", None) != found.name:
            continue        # a re-export; its own module declares it
        record = getattr(obj, "__adcp_schema__", None)
        rows[found.name + ":" + name] = {
            "kind": ident[0],
            "ident": ident[1],
            "schema": [record.document, record.pointer] if record is not None else None,
        }
OUT.write_text(json.dumps({"root": ROOT, "rows": rows, "errors": bad}))
print(f"{ROOT}: {len(rows)} declarations, {len(bad)} modules did not import")
