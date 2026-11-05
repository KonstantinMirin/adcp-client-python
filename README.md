# The AdCP types, compiled from the schema bundle

**This is a TYPES package. It is not a replacement for upstream `adcp` and does not
intend to become one.** What it ships is every type the AdCP schema bundle states, derived
from the bundle and carrying the schema node it was derived from. What it does not ship is
the hand-written machinery upstream's wheel also carries — the server, the decisioning and
reporting layers, the signing and canonical-format code — because none of that is stated by
a schema and nothing here can derive it.

A reader deciding whether to install this needs the second sentence as much as the first,
so both are measured below, and every figure names the population it is over. Re-derive
them rather than trust them; the instruments are named beside each one.

## What a caller imports today, and how much of it is types

Measured against upstream **`adcp` 9.6.1** installed as a wheel from PyPI, over the code
upstream itself offers a reader as the way to use the package: the **80 `examples/*.py`
files and 477 Python fences** of `README.md`, `llms.txt`, `MIGRATION*.md`, `docs/**.md`
and `skills/**` in the `v9.2.0` checkout. Every `import adcp…` parsed with `ast` — **1,322
import statements** — and every imported name attributed to the module that *defines* it on
the installed wheel, because packaging is what decides what a caller gets.

**Consumer-facing code imports 503 distinct names from 82 distinct modules. 120 of them —
23.9% — are defined by `adcp.types`.**

| defining subpackage | distinct names | | defining module | distinct names |
|---|---|---|---|---|
| `types` | **120 (23.9%)** | | `exceptions` | 13 |
| `reporting` | 74 (14.7%) | | `adagents` | 11 |
| `server` | 69 (13.7%) | | `client` | 10 |
| `decisioning` | 68 (13.5%) | | `webhooks` | 9 |
| `canonical_formats` | 26 (5.2%) | | `media_buy_actions` | 6 |
| `signing` | 23 (4.6%) | | `oauth` | 5 |
| `compat`, `testing` | 6 each | | 16 further modules | 1–4 each |
| `validation` | 3 | | | |

The remaining **23 names (4.6%) resolve nowhere on upstream's own 9.6.1 wheel**, and 21 of
them raise — `BrandManifest` and `Pricing` with an `ImportError` carrying upstream's own
migration note, `SubAsset` and `ImageAsset` with an `AttributeError`. A name that raises on
upstream's wheel is a finding about them and is not a name this package owes. (They are
spelled here without a leading `adcp.` on purpose: they are upstream's names, and writing
them as dotted paths would read as a claim about what this package exports.)

**So three quarters of what a caller spells is machinery, and that is the measurement the
first paragraph rests on.** It is also why the figure is given over *consumer code* and not
over upstream's export surface: that surface is 27,094 public `(module, name)` rows across
1,508 modules, most of it reachable only because a module declares no `__all__`, and a
percentage over it would mean nothing.

Re-derive with `survey/consumer_imports.py`, run on an interpreter that has upstream
installed. It prints this table, the unresolvable names and the subpackage lists, and its
docstring carries the two commands that build that interpreter.

## What this ships

Built from this tree, installed into a virtual environment that has never seen the
repository:

```python
from adcp.types.core import PaginationRequest
from adcp.types.enums import MediaBuyStatus
from adcp.types.media_buy import GetMediaBuyDeliveryRequest

# Every model names the schema node it was compiled from.
assert PaginationRequest.__adcp_schema__.document == "core/pagination-request.json"
assert GetMediaBuyDeliveryRequest.__adcp_schema__.document == (
    "media-buy/get-media-buy-delivery-request.json"
)

# The document decides acceptance -- not the annotations alone.
assert PaginationRequest.strict_validate({"max_results": 50}).max_results == 50
assert PaginationRequest(max_results=50).model_dump(exclude_none=True) == {"max_results": 50}
assert MediaBuyStatus("active").value == "active"
```

`adcp` with **`types` as its only subpackage**, and under it **25 domain modules** named
from the documents' own paths — `adcp.types.core`, `adcp.types.media_buy`,
`adcp.types.enums`, `adcp.types.brand`, `adcp.types.creative` and twenty more. One import
path per declaration; the generated tree underneath (`adcp.types._schemas`) is private and
free to change.

**2,114 exported declarations** — 1,520 models, 232 enumerations, 362 constrained scalars —
behind **1,014 distinct documents** of the bundle's 1,054 portable ones.

**The provenance key is the property upstream's tree cannot offer, and here is the exact
measurement rather than the slogan.** `1,519 of the 1,520 exported models` carry
`__adcp_schema__ = SchemaRef(document=…, pointer=…)` as a class attribute. The one
exception is `adcp.types.envelopes.FailedResponse`, which belongs to no document and says so
in its own docstring: the documents of that family disagree about what they accept, so no
single reference would be right for all of them. An `Enum` subclass and an `Annotated[…]`
alias *cannot* hold a class attribute, so for those the node is on the declaring private
module — reachable for 214 of 232 enumerations and 48 of 362 constrained scalars, and not
reachable for the rest, of which 218 live in `adcp.types.constraints`, one whole-run file
that is keyed to no single document by design.

**Against upstream: 0 of its 27,094 public rows carry any schema reference** — not on the
object, not in `model_config`, not on the defining module. Measured by searching every
place one could live; the two near-hits are an inlined constraint fragment in
`json_schema_extra`, which names no document. Re-derive with
`survey/upstream_provenance.py`, on the same interpreter.

## What this does not ship, by name

Of upstream's 13 top-level subpackages, consumer code reaches 9. One of those is `types`.
**The other 8 are not here:**

`canonical_formats` · `compat` · `decisioning` · `reporting` · `server` · `signing` ·
`testing` · `validation`

Consumer code also reaches **22 top-level modules**, none of which are here:

`acceptance` · `adagents` · `audit_sink` · `client` · `exceptions` · `feed_mirror` ·
`governance` · `identifiers` · `media_buy_actions` · `negotiation` ·
`notification_outbox_pg` · `oauth` · `observability` · `property_lists` · `registry` ·
`substitution` · `task_options` · `webhook_receiver` · `webhook_sender` ·
`webhook_supervisor` · `webhook_transport_hooks` · `webhooks`

Four of upstream's subpackages — `migrate`, `protocols`, `schemas`, `utils` — are touched
zero times by its examples or docs and are internal to it.

This is what that absence does, and it is executed rather than described:

```python
import importlib

for absent in ("adcp.server", "adcp.decisioning", "adcp.reporting", "adcp.signing"):
    try:
        importlib.import_module(absent)
    except ModuleNotFoundError:
        pass
    else:
        raise AssertionError(f"{absent} imported; this README is out of date")
```

**There is no migration guide yet, and this sentence is deliberately not a path.** The
names above need one entry each saying what to use instead, or saying there is nothing and
why. Writing a path here before the document exists is the defect
`tests/test_prose_resolves.py` was written for, so the row that owes it is
`adcp-client-python-3fw.1`, and when it lands this paragraph names it.

A type spelling has a different answer, and it is not this one: the flat `adcp.types`
namespace becomes an **alias layer** onto the generated classes, so an application keeps
its current import spellings. That is `adcp-client-python-82m.7`, and the rule it is held
to is in `docs/plan/final-state.md` reading 10 — an alias is keyed on a schema subject and
never on a name, and a name with no schema subject gets a migration note and never a class.

---

# The generator

The rest of this document is about the half that produces the above: this tree is the
emitter, and the package is its output.

## What is here

| | |
|---|---|
| `schemas/cache/3.2/` | **1,625 documents**, of which `codegen.bundle.portable` selects **1,054**. The source of truth and the only input. |
| `codegen/` | The walk, the lowering and the emitter. `python -m codegen` is the command. |
| `codegen/harness.py` | Grades a (schema document, Python class) pair on three checks. Imports `jsonschema`, `hypothesis`, `hypothesis_jsonschema` and `pydantic`; also four sibling modules of `codegen` and six names from `adcp.types._base`, the package it grades. **It is therefore not independent of its subject**, which the earlier text here claimed and which `adcp-client-python-8kx` is open about. |
| `patches/8525/` | A PATCH SET: new documents plus a manifest of the pointers that become a `$ref`. Applied to the published bundle by `codegen/patch.py`; it is also the diff we ask upstream to take, and it retires when the backport lands. Admissibility is checked, not asserted — `tests/test_patch_8525.py` compares the record of every one of the 1,054 documents. |
| `docs/plan/architecture.md` | How the passes are arranged, and §14 "Migration path" is the **ten steps**: the only work list. |
| `docs/plan/rebuild-plan.md` | The semantics document, §1–§9: what we emit and how each keyword compiles. No site counts — a count is a property of one bundle version. |
| `docs/plan/sdk-type-generation.md` | Design intent, P1–P13. Non-negotiable. |
| `docs/plan/final-state.md` | The ten readings the artifact is finished against. Reading 10 is the one this README's first section states. |
| `docs/plan/defect-inventory.md` | The verified defects in the *previous* generated output — 10 model defects in direction 1 (one of which the inventory itself says is not a defect) and 12 distinct triples in direction 2. Its own ticket table says 11 of those 12 have no ticket, so they are not each the control of a step. |
| `docs/plan/spike/` | The worked Route B reference: `route_b.py` is the emitter, `out_b.py` the emitted module. `grade.py` does **not** run — it raises `TypeError` against the current `harness.Pair` (`adcp-client-python-5x5`) — so this is a reference to read and not a command to type. |

## What is deliberately absent

A previous attempt built a generator that emitted no type while its harness read green.
Two things made that possible, and both are absent here on purpose. The figures that used
to be in this paragraph described a tree that is not in this repository — this is an orphan
branch with no shared history — so they were unverifiable from here and are gone rather
than repeated.

- **No adapter, and no binding table.** `adapter_adcp.py` does not exist in this tree, and
  neither does a binding table — `codegen/emit.py` says so where one would go. The old file
  encoded where a *previous* generated tree lived and how its modules were paired to
  documents by a `# filename:` header, and it is the single thing that kept pointing the
  harness at the generator being replaced: that is how a harness came to be green over a
  whole population while nothing was being generated. Instead **every emitted model carries
  a `SchemaRef` on `__adcp_schema__`** (1,519 of the 1,520 exported, as above), so
  `strict_validate` and the grader both read the pairing off the class and there is nothing
  to aim.

- **No naming or module-assignment layer.** Those were built upstream of the lowering, so
  "one node, one class" became "every node needs a name" and "refuse what you cannot derive"
  became "refuse the document for a node that should never have been a class". Here each
  lowering names what it emits.

**`datamodel-code-generator` is present, and pinned exactly (D10).** Our walk decides the
shape and dmcg's pydantic-v2 MODEL layer renders the class — its parser never runs, because
the parser is the half that decides names and structure from a schema and that is the half
with the AdCP knowledge in it. Driving the model layer carries defaults, descriptions,
constraints, aliases and the import set for free.

## The metric

**N = portable documents emitted by `codegen.emit` AND graded green by `codegen.harness`
against the schema the class itself names, on all three checks, with emitted plus refused
equal to the bundle's own size and every refusal named by document, pointer and keyword.**

Over `tests/test_emit.py`'s `tree_population()` — which is `bundle.portable(BUNDLE)`, all
1,054 documents — the current run **emits 1,054 and refuses 0**. The grading is a separate
reading and is not all green. A run writes a per-pair verdict table named `verdicts.tsv`
beside the tree it wrote, and **that file is deliberately untracked** — a file every
invocation regenerates would dirty the tree on every run, which is the property the
committed tree rests on, so a fresh checkout does not have it and this README does not
pretend it does. Produce it with the run itself, then read it. It opens with its own
count, **2,593 graded pairs, 2,582 pass, 11 not pass**, and a second header line breaking
that out per check as pass, fail and absent counts — on which `widening` is absent for 2,539
of the pairs and `refuses` for 13. **An `absent` cell is not a pass** — it is a check that was never put to
that pair — and the file says so in its own header. Read it rather than this paragraph; it
is regenerated by every run and a figure here is a figure that can go stale.

What grades the generated code is the ROUND TRIP inside the accepts check: an instance drawn
from the document reaches the class, and what the class DUMPS goes back to the document for
its own verdict. Taking an instance is not enough by itself — a payload reaches the class
through `strict_validate`, whose schema half answers first, so a model with `Any` on every
field accepts the same instances a faithful one does, and it is the dump that tells the two
apart. The liveness check proves that class's schema half is connected at all, and
`check_widening` puts every approximation the artifact declares to a draw of its own.

## Running it

```bash
uv sync --all-extras
```

**That command does not install a type checker, and two tests fail rather than skip without
one.** `mypy` appears nowhere in `pyproject.toml` or `uv.lock` — deliberately, because a
checker is an instrument and the artifact does not depend on it — but
`tests/test_type_checker.py` asserts on its absence instead of skipping, so a freshly
synced environment runs the suite two tests short. Install it alongside
(`uv pip install mypy`) until `adcp-client-python-dwr` settles which of the two it should
be. The same sync removes `pytest-timeout`, `pytest-json-report` and `pytest-metadata` if
they are present.

Build the wheel and install it into an environment that has never seen this repository,
which is the artifact reading 8 is about and the one the examples above were run against:

```bash
uv build --wheel --out-dir dist
uv venv --python 3.12 consumer-venv
uv pip install --python consumer-venv dist/*.whl
```

The emitter, over one document, which is the whole command (D9: the bundle directory is an
argument and there is no default):

```bash
PYTHONPATH=. uv run --no-sync python -m codegen \
  --bundle schemas/cache/3.2 core/pagination-request.json
PYTHONPATH=. uv run --no-sync python -m pytest tests/test_emit.py
```

That command writes no `--package`, so it leaves D5's alias module
(`src/adcp/types/constraints.py`) alone — and that is deliberate rather than an omission.
The alias module is ONE file over the WHOLE run: a run over one document resolves that
document's constrained types and no others, so writing it would replace the committed module
with a shorter one and leave every other module importing a symbol that is gone. `--package`
therefore has no default, and the command says on stdout which file it did not write. To
regenerate the whole tree, name the population and the package together:

```bash
PYTHONPATH=.:tests uv run --no-sync python -c \
  'from codegen import emit, patch; from test_emit import tree_population; from pathlib import Path; \
   out = emit.emit(patch.for_build(Path("schemas/cache/3.2")), tree_population()); \
   emit.write(out, Path("src/adcp/types/_schemas"), Path("src/adcp/types"))'
```

`patch.for_build` is the bundle a RUN reads: the published one with every patch set the build
applies (`patch.BUILD`, today `patches/8735`). It is the one derivation, shared with `./check`
and `tests/fresh.py`, so the fast loop's figures and the gate's range over one input — before
it existed the override table was applied in two test files and in no compile path.

`tree_population()` is deliberately NOT the union of the seven step selectors
(`population()`, 991 documents, which grades the rebuild's phases): a step is a phase and
the tree is an artifact, and a population drawn from the phases made the tree's contents
depend on which documents an earlier run happened to reach through a `$ref`.

That command is also the only one that PRUNES. `package` is the run's scope, so passing it
says this run covers the whole population — and a whole-population run deletes the
`.py`/`.json` pairs it no longer intends, which is what a document that stops emitting
leaves behind. The one-document command above passes no `--package` and so deletes nothing.

`tests/test_emit.py::test_the_committed_tree_is_what_a_fresh_run_emits` compares both against
a fresh emission, byte for byte, so a stale file fails at the gate even if it got into the
tree some other way.

## This document is graded

`tests/test_readme_executes.py` executes every `python` fence above against the package as
an INSTALLED copy — not the source tree, because an example that needs `PYTHONPATH=src` is
an example the reader who installed the wheel cannot run. It also resolves every path and
every git ref this file names, and requires every `adcp.…` path in the prose either to
import or to be shown absent by one of those fences. What it does not grade is a FIGURE: the
numbers above are re-derived by running the instrument named beside each, and that test's
`test_what_these_clauses_do_not_grade` says why no check recomputes them here.

## Merging back

This is an orphan branch with no shared history, by design: an agent reading it cannot be
steered by code that a later measurement retired. It is not yet merged anywhere, and the
destination is the owner's to name — the branch this section used to point at does not
exist, which is the defect that made `tests/test_readme_executes.py` necessary.
