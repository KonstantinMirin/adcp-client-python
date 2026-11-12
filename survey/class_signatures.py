"""Dump every pydantic class signature in whichever tree this interpreter resolves adcp from."""

import importlib
import json
import pkgutil
import sys

import pydantic

out = {}
roots = ["adcp.types"]
for root in roots:
    try:
        mod = importlib.import_module(root)
    except Exception:
        continue
    for mi in pkgutil.walk_packages(mod.__path__, root + "."):
        try:
            m = importlib.import_module(mi.name)
        except Exception:
            continue
        for n, o in vars(m).items():
            if not (isinstance(o, type) and issubclass(o, pydantic.BaseModel)):
                continue
            if o is pydantic.BaseModel:
                continue
            try:
                f = o.model_fields
            except Exception:
                continue
            fields = sorted(f)
            req = sorted(k for k, v in f.items() if v.is_required())
            ref = getattr(o, "__adcp_schema__", None)
            key = (o.__module__, o.__qualname__)
            out.setdefault(
                f"{key[0]}.{key[1]}",
                {
                    "name": o.__name__,
                    "fields": fields,
                    "required": req,
                    "pointer": f"{ref.document}{ref.pointer}" if ref is not None else None,
                },
            )
json.dump(out, open(sys.argv[1], "w"))
print(len(out), "classes ->", sys.argv[1])
