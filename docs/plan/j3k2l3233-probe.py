"""INSTRUMENT B: grade the documents salesagent-j3k2l.26's two guards refuse.

The guards live in ``codegen/lower/union.py``, which this lane does not own, so
they are disabled AT RUNTIME -- no file is edited.  The whole bundle is then
emitted into a COPY of ``src/`` so D5's alias module is complete and the
committed tree is untouched, and every pair of the unlocked documents is graded
by ``compare_schema`` with the document-side readings.

Run from the repo root, after copying ``src/`` to a scratch directory:

    mkdir -p /tmp/probe && cp -R src/. /tmp/probe/
    CCM_INDEX_BYPASS=1 env -u VIRTUAL_ENV uv run --no-sync \
        python docs/plan/j3k2l3233-probe.py /tmp/probe [both|localref|fold]

Measured 2026-10-23 on sdk/j3k2l3233-comparison (base 9e9da67e1), with the
document-side readings in ``compare_schema``.  Every emitted count matches
``salesagent-j3k2l.26``'s independently measured figures:

    guards        emitted   unlocked pairs   added   missing   differs
    (neither)     686       --               --      --        --
    localref      690       16               0       0         0
    fold          693        7               3       3         4
    both          697       23               3       3         4

``localref`` is ``_refuse_a_local_reference_branch`` and can come off with no
residual.  ``fold`` is ``_refuse_a_shape_the_comparison_cannot_read``, and its
residual is two things neither reading owns: ``salesagent-j3k2l.35``'s
const-at-a-named-node rendering (3 added + 3 missing at
``creative/get-creative-features-terminal-success.json``) and the pre-existing
``/properties/slots/{default,description}`` family (4 differs, joining 12 of
trunk's own 43 across 7 ``formats/canonical/*.json`` that already emit).

The same tree graded by the BASE commit's ``compare_schema`` -- one variable,
same 23 pairs -- reads ``added=55 missing=3 differs=4``: 43 for the
document-side local ``$ref``, 5 for the bare-type fold, 4 for the null-arm
fold, and the 3 that are ``.35``'s.
"""

from __future__ import annotations

import importlib
import pkgutil
import sys
from pathlib import Path

DEST = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(DEST))
sys.path.insert(0, "tests")

#: .32's four documents and .33's seven, read off the two beads issues.
LOCAL_REF = [
    "core/bidding-policy-capability.json",
    "core/placement-presentation.json",
    "core/canonical-media-buy-features.json",
    "core/media-buy-features.json",
]
FOLDED = [
    "compliance/get-creative-features-completion.json",
    "creative/creative-feature-result.json",
    "creative/get-creative-features-terminal-success.json",
    "formats/canonical/audio_hosted.json",
    "formats/canonical/video_hosted.json",
    "property/property-feature-result.json",
    "property/property-feature-value.json",
]

from codegen import bundle, emit  # noqa: E402
from codegen.lower import union  # noqa: E402

BUNDLE = Path(__file__).resolve().parent / "schemas" / "cache" / "3.2"

WHICH = sys.argv[2] if len(sys.argv) > 2 else "both"
if WHICH in ("both", "localref"):
    union._refuse_a_local_reference_branch = lambda *a, **k: None  # noqa: SLF001
if WHICH in ("both", "fold"):
    union._refuse_a_shape_the_comparison_cannot_read = lambda *a, **k: None  # noqa: SLF001

docs = bundle.portable(BUNDLE)
out = emit.emit(BUNDLE, docs)
print(f"GUARDS={WHICH}  emitted={len(out.emitted)} refused={len(out.refusals)} of {len(docs)}")
emit.write(out, DEST / "adcp" / "types" / "_schemas", DEST / "adcp" / "types")

for d in LOCAL_REF + FOLDED:
    verdict = "EMITTED" if d in out.emitted else f"REFUSED {out.refusals.get(d, {}).get('detail', '')[:90]}"
    print(f"  {d}: {verdict}")

# ------------------------------------------------------------------ grade them
import adcp.types._schemas as pkg  # noqa: E402
from adcp.types._base import AdCPBaseModel, SchemaRef, schema_at  # noqa: E402
from codegen.harness import compare_schema  # noqa: E402

assert Path(pkg.__file__).is_relative_to(DEST), f"graded the committed tree, not {DEST}"

WANT = set(LOCAL_REF + FOLDED)
refs: list[tuple[SchemaRef, object, str]] = []
for info in sorted(pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."), key=lambda i: i.name):
    module = importlib.import_module(info.name)
    for value in vars(module).values():
        if (
            isinstance(value, type)
            and issubclass(value, AdCPBaseModel)
            and "__adcp_schema__" in value.__dict__
            and value.__module__ == info.name
        ):
            refs.append((value.__adcp_schema__, value, info.name))
    ref = vars(module).get("__adcp_schema__")
    if isinstance(ref, SchemaRef) and callable(vars(module).get("strict_validate")):
        (symbol,) = module.__all__
        refs.append((ref, getattr(module, symbol), info.name))

pairs = a = m = dd = 0
for ref, model, _mod in refs:
    if ref.document not in WANT:
        continue
    pairs += 1
    c = compare_schema(
        schema_at(ref), model, document=schema_at(SchemaRef(ref.document, "#"))
    )
    a += len(c.added)
    m += len(c.missing)
    dd += len(c.differs)
    for row in c.added:
        print(f"ADDED   {ref.document}{ref.pointer} {row}")
    for row in c.missing:
        print(f"MISSING {ref.document}{ref.pointer} {row}")
    for row in c.differs:
        print(f"DIFFERS {ref.document}{ref.pointer} {row}")
print(f"UNLOCKED PAIRS={pairs} added={a} missing={m} differs={dd}")
