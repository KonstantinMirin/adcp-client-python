"""Which of the 97 keywords does docs/plan/rebuild-plan.md never name?  Exhaustive."""
from __future__ import annotations
import json, re, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, ".")
from codegen import bundle
from jsonschema import Draft7Validator

BUNDLE = Path("schemas/cache/3.2")
PLAN = Path("docs/plan/rebuild-plan.md").read_text()
VOCAB = set(Draft7Validator.VALIDATORS)

kw = Counter()
root_only = {}
for d in bundle.portable(BUNDLE):
    doc = bundle.read(BUNDLE, d)
    for ptr, n in bundle.nodes(doc):
        for k in n:
            kw[k] += 1
            root_only.setdefault(k, Counter())["ROOT" if ptr == "" else "nested"] += 1

named, unnamed = [], []
for k, c in sorted(kw.items(), key=lambda x: -x[1]):
    hits = len(re.findall(re.escape(k), PLAN))
    (named if hits else unnamed).append((k, c, hits))

print(f"{len(kw)} distinct keywords at a schema position over 1,054 portable documents")
print(f"  named at least once in the plan: {len(named)}")
print(f"  NEVER named in the plan:         {len(unnamed)}\n")
print("=== NEVER NAMED (count, in-draft07-vocabulary, root/nested) ===")
for k, c, _ in unnamed:
    r = root_only[k]
    print(f"{c:6d}  {'VOCAB' if k in VOCAB else '     '}  root={r['ROOT']:4d} nested={r['nested']:5d}  {k}")
print("\n=== named, but with 3 or fewer mentions (check each by hand) ===")
for k, c, h in named:
    if h <= 3:
        print(f"{c:6d}  mentions={h}  {'VOCAB' if k in VOCAB else '     '}  {k}")
json.dump({"unnamed": [[k, c] for k, c, _ in unnamed],
           "named": [[k, c, h] for k, c, h in named]},
          open("survey/coverage.json", "w"), indent=1)
