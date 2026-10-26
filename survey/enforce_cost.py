"""What would enforcing x-adcp-validation's structured minority cost?

The question is whether the DOCUMENT accepts an instance the keyword forbids.  If it does,
a class enforcing the keyword refuses a payload `strict_validate`'s schema half accepts --
the model-narrower-than-its-document direction, which `check_accepts` reports as
`model_refused_valid`.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, ".")
from hypothesis import HealthCheck, Phase, given, settings
from jsonschema import Draft7Validator, FormatChecker

from codegen import bundle, harness

B = Path("schemas/cache/3.2")
SITES = [
    ("core/creative-representation-set.json", "/properties/representations", "representation_id"),
    ("core/preview-provider.json", "/properties/routes", "format_option_id"),
    ("creative/sync-creatives-request.json", "/properties/creatives", "creative_id"),
    ("error-details/creative-representation-unresolved.json",
     "/properties/representation_rejections", "representation_id"),
]

for doc_name, ptr, key in SITES:
    try:
        root = bundle.record(B, doc_name)
    except Exception as exc:
        print(f"{doc_name}: unresolvable ({type(exc).__name__})")
        continue
    node = root
    for part in [p for p in ptr.strip("/").split("/") if p]:
        node = node[part]
    items = node.get("items")
    if not isinstance(items, dict):
        print(f"{doc_name}{ptr}: items is {type(items).__name__}")
        continue
    drawn: list = []
    try:
        strat = harness.strategy(items, {})
    except Exception as exc:
        print(f"{doc_name}{ptr}: no strategy ({type(exc).__name__})")
        continue

    @settings(max_examples=1, deadline=None, database=None,
              suppress_health_check=list(HealthCheck), phases=[Phase.generate])
    @given(strat)
    def grab(x: object) -> None:
        if not drawn:
            drawn.append(x)

    try:
        grab()
    except Exception as exc:
        print(f"{doc_name}{ptr}: generation failed ({type(exc).__name__}: {exc!r:.80})")
        continue
    if not drawn:
        print(f"{doc_name}{ptr}: no instance drawn")
        continue
    one = drawn[0]
    if not isinstance(one, dict) or key not in one:
        print(f"{doc_name}{ptr}: drawn item carries no {key!r} "
              f"(keys {sorted(one)[:6] if isinstance(one, dict) else type(one).__name__})")
        continue
    pair = [copy.deepcopy(one), copy.deepcopy(one)]
    uniq = bool(node.get("uniqueItems"))
    note = "identical items"
    if uniq:
        # identical items are refused by uniqueItems itself, so make them differ somewhere
        # ELSE while still sharing the key the extension says must be unique.
        other = next((k for k, v in one.items() if isinstance(v, str) and k != key), None)
        if other is None:
            print(f"{doc_name}{ptr}: uniqueItems and no second string field to vary")
            continue
        pair[1][other] = (pair[1][other] or "") + "x"
        note = f"items differing only in {other!r}"
    v = Draft7Validator(node, format_checker=FormatChecker())
    errs = sorted({e.validator for e in v.iter_errors(pair)})
    shares = pair[0][key] == pair[1][key]
    print(f"\n{doc_name}{ptr}")
    print(f"  uniqueItems={uniq}   unique_item_properties=[{key!r}]")
    print(f"  two conforming {note}, both carrying {key}={pair[0][key]!r}:")
    print(f"    the DOCUMENT says: "
          f"{'ACCEPTED' if not errs else 'refused by ' + str(errs)}"
          f"   (they share the key: {shares})")
    if not errs and shares:
        print("    => enforcing the keyword would refuse a payload the document accepts")
