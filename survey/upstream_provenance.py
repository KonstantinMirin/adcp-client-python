"""Does any public name of upstream's wheel carry a schema reference?

Run on an interpreter that has UPSTREAM `adcp` installed:

    /tmp/up/bin/python survey/upstream_provenance.py adcp

The public-name rule: reached at a module path with no underscore-prefixed
segment, and either the module declares __all__ and the name is in it, or the
module declares none and the name does not start with "_".

A "schema reference" is looked for in EVERY place one could live, because a
claim of zero is only worth something if the search was not scoped to one kind
of thing:
  * on the object:  any dunder/attr whose name mentions schema/pointer/$id/ref
  * on pydantic models: model_config extras, model_json_schema()["$id"]
  * on the DEFINING MODULE: a module-level attribute naming a schema node
    (this is the fallback OUR tree needs for enums and Annotated aliases, so
    not searching it here would make the comparison unfair to upstream)
"""

from __future__ import annotations

import collections
import importlib
import importlib.metadata as md
import json
import pkgutil
import sys
from pathlib import Path

KEYS = ("schema", "pointer", "jsonschema", "json_schema", "schema_id", "docref")


def candidate_attrs(obj) -> list[str]:
    out = []
    for a in dir(obj):
        low = a.lower()
        if any(k.replace("$", "") in low for k in KEYS):
            out.append(a)
    return out


def main() -> None:
    root_name = sys.argv[1] if len(sys.argv) > 1 else "adcp"
    root = importlib.import_module(root_name)

    mods = [root_name]
    for m in pkgutil.walk_packages(root.__path__, root_name + "."):
        mods.append(m.name)

    rows = []
    unimportable = []
    hits = []
    module_level_hits = collections.Counter()

    for name in sorted(mods):
        if any(seg.startswith("_") for seg in name.split(".")[1:]):
            continue
        try:
            mod = importlib.import_module(name)
        except Exception as exc:
            unimportable.append((name, f"{type(exc).__name__}: {str(exc).splitlines()[0][:100]}"))
            continue

        # module-level provenance (the fallback our own tree relies on)
        mod_sr = None
        for a in ("__adcp_schema__", "__schema__", "__schema_ref__", "__json_schema__"):
            if hasattr(mod, a):
                mod_sr = f"{name}.{a}"
                module_level_hits[a] += 1
                break

        declared = getattr(mod, "__all__", None)
        if declared is not None:
            names = [n for n in declared if isinstance(n, str)]
        else:
            names = [n for n in vars(mod) if not n.startswith("_")]

        for n in names:
            try:
                obj = getattr(mod, n)
            except Exception:
                continue
            ref = None
            for a in ("__adcp_schema__", "__schema__", "__schema_ref__", "__json_schema__"):
                v = getattr(obj, a, None)
                if v is not None:
                    ref = f"attr {a}={v!r:.60}"
                    break
            if ref is None:
                cfg = getattr(obj, "model_config", None)
                if isinstance(cfg, dict):
                    for k, v in cfg.items():
                        if any(key.replace("$", "") in str(k).lower() for key in KEYS):
                            ref = f"model_config[{k}]={v!r:.60}"
                            break
                    if ref is None and "json_schema_extra" in cfg:
                        extra = cfg.get("json_schema_extra")
                        if isinstance(extra, dict):
                            for k in extra:
                                if any(key.replace("$", "") in str(k).lower() for key in KEYS):
                                    ref = f"json_schema_extra[{k}]"
                                    break
            if ref is None and mod_sr is not None:
                ref = f"module {mod_sr}"
            rows.append((name, n, ref or ""))
            if ref:
                hits.append((name, n, ref))

    print(f"{root_name} {md.version(root_name.replace('_', '-'))}")
    print(f"public (module, name) rows: {len(rows)}")
    print(f"modules walked           : {len(mods)}  (unimportable {len(unimportable)})")
    print(f"ROWS CARRYING A SCHEMA REFERENCE: {len(hits)}")
    print(f"modules carrying a module-level schema reference: {sum(module_level_hits.values())}")
    for h in hits[:10]:
        print("  ", h)
    print()
    print("sanity -- attribute names on public objects that merely MENTION a schema key:")
    seen: collections.Counter[str] = collections.Counter()
    for mname, n, _ in rows[:4000]:
        try:
            obj = getattr(importlib.import_module(mname), n)
        except Exception:
            continue
        for a in candidate_attrs(obj):
            seen[a] += 1
    for a, c in seen.most_common(12):
        print(f"   {a:34s} {c}")

    Path(f"provenance-{root_name}.json").write_text(
        json.dumps(
            {
                "dist": root_name,
                "version": md.version(root_name.replace("_", "-")),
                "public_rows": len(rows),
                "rows_with_schema_ref": len(hits),
                "hits": hits[:200],
                "unimportable": unimportable,
            },
            indent=1,
        )
    )


if __name__ == "__main__":
    main()
