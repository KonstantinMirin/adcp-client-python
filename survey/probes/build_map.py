"""The node-keyed alias map, built by `survey/dropin_blocking.py`'s own four rules.

1. upstream's defining module names the DOCUMENT (`bundled/` and `mcp/` are PROJECTIONS, so
   they name the canonical document -- `codegen.bundle.PROJECTIONS` and f99s);
2. the candidates are the declarations OURS compiled FROM THAT DOCUMENT, read off
   `__adcp_schema__` and never off a word;
3. IDENTITY IS A GATE ON THAT CANDIDATE SET AND NEVER THE PROPOSAL -- the error-envelope
   field set is shared by forty classes of ours, so identity alone over the whole tree
   "matches" everything;
4. a row no rule resolves is left UNRESOLVED and reported, because minting a class to
   satisfy an import is the back door reading 10's ordering exists to close.
"""
import json, sys
from pathlib import Path

HERE = Path("/srv/ws/.adcp-scratch/moveit")
up = json.loads((HERE / "up.dom.json").read_text())["rows"]
ours = json.loads((HERE / "our.sch.json").read_text())["rows"]
PROJECTIONS = ("bundled", "mcp")

# our declarations grouped by the document they were compiled from
by_document = {}
for key, row in ours.items():
    if not row["schema"]:
        continue
    by_document.setdefault(row["schema"][0], []).append((key, row))

#: our module path -> the document it mirrors, for a declaration carrying no `__adcp_schema__`
#: (a type alias is not a class and has no record), derived from the declarations that do.
module_document = {}
for key, row in ours.items():
    if row["schema"]:
        module_document.setdefault(key.split(":")[0], row["schema"][0])


def document_of(their_module: str) -> str | None:
    rest = their_module.removeprefix("adcp.types.domains.")
    head, _, tail = rest.partition(".")
    if head in PROJECTIONS:
        rest = tail
    return module_document.get("adcp.types._schemas." + rest)


out, unresolved, stats = {}, [], {"node+identity": 0, "node+identity-several": 0,
                                  "node-no-identity-match": 0, "no-document": 0}
for key, row in sorted(up.items()):
    their_module, _, name = key.rpartition(":")
    if not their_module.startswith("adcp.types.domains."):
        continue
    document = document_of(their_module)
    if document is None:
        stats["no-document"] += 1
        unresolved.append([key, "no document of ours mirrors their module"])
        continue
    agree = [
        (ours_key, ours_row)
        for ours_key, ours_row in by_document.get(document, [])
        if ours_row["kind"] == row["kind"] and ours_row["ident"] == row["ident"]
    ]
    if not agree:
        stats["node-no-identity-match"] += 1
        unresolved.append([key, f"{len(by_document.get(document, []))} of ours from "
                                f"{document}, none with their identity"])
        continue
    if len(agree) > 1:
        stats["node+identity-several"] += 1
        agree.sort(key=lambda kv: (len(kv[1]["schema"][1]), kv[0]))
    else:
        stats["node+identity"] += 1
    target_module, _, target_name = agree[0][0].rpartition(":")
    out[key] = [target_module, target_name, "node+identity", document,
                agree[0][1]["schema"][1]]

prior = json.loads((HERE / "shim" / "probe_map.json").read_text())
# **THE PRIOR MAP WINS**, because its rows carry fwvm's per-name READING of the node and
# this one carries a derivation.  A derivation may add a row and may never overrule one.
merged = {**out, **prior}
(HERE / "shim" / "probe_map.json").write_text(json.dumps(merged, indent=0))
print(json.dumps(stats, indent=1))
print(f"derived {len(out)}; prior {len(prior)}; merged {len(merged)}; unresolved {len(unresolved)}")
(HERE / "unresolved.json").write_text(json.dumps(unresolved, indent=1))
