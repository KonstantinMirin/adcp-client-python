"""WHICH of upstream's `types/` files are hand-written MACHINERY, and which are LIVE.

**MEASURED OVER UPSTREAM'S OWN TREE AND NEVER LISTED.**  Two readings of upstream's own
evidence decide every row, and both are counted here rather than asserted anywhere:

GENERATED or HAND-WRITTEN -- the file's own header names the script and the source document
    (`registry.py`: "DO NOT EDIT -- regenerate with: python scripts/generate_registry_types.py
    ... Source: schemas/registry-openapi.yaml"), and a generated aggregator is dominated by
    `from adcp.types...` lines (`_generated.py` carries 1,038 of them, `core.py` zero).  What
    a generator wrote stays deleted; `remove(types)` was right about those.

LIVE or TEST-ONLY -- how many of upstream's NON-`types/` source files import the module,
    against how many of their tests do.  Zero source importers and a handful of test
    importers is upstream's CURATED TOPIC MODULE: a hand-picked partial view, narrower than
    the generated tree and not derived from the bundle, whose only consumer is the test
    asserting it exists.  Our emitted domain surface is the DERIVED version of that idea, so
    a test over their hand-picked view asserts THEIR implementation and the module is in the
    delete category -- restoring it would put a second, undeclared partial surface beside
    the one the bundle states.  `buyer`, `seller`, `creative`, `media_buy`, `protocol`,
    `signals` and `error_details` are all 0 source importers.

The `src` count EXCLUDES `src/adcp/types/` itself, because a `types/` module importing
another is the layer talking to itself and says nothing about whether the SDK needs it; the
`src_all` column keeps the number that includes them so a transitively-live module
(`media_buy_status_helpers` is `canonical_creative`'s, and `canonical_creative` has three
source importers) is visible rather than silently dropped.

    PYTHONPATH=.:src ./.venv/bin/python survey/upstream_machinery.py --rev 4ed0bce87 \
        --table survey/upstream-machinery-9.6.1.tsv

---

**AND OF THE LIVE ONES, WHICH ARE AN IMPORT-TIME PATCH LAYER, AND DOES IT RUN.**  The
second question about the same population, asked with `--wheel`:

    PYTHONPATH=.:src ./.venv/bin/python -m survey upstream_machinery \
        --wheel /tmp/upwheel/lib/python3.12/site-packages --tree /srv/ws/dropin-namereach

`--wheel` alone measures the layer; `--tree` adds whether it LOADS there and what the
run cost.  Neither path writes anything, and `--wheel` leaves the classification above
untouched -- `rows`, `restored_paths` and the TSV are the first question's and are not
read here.

**A DEAD PATCH LAYER DOES NOT FAIL LOUDLY, WHICH IS WHY IT NEEDED AN INSTRUMENT.**  Four
modules under `types/` mutate OTHER modules' generated models at import: they widen an
annotation, add a coercing validator, or install an optional extension a bundle does not
yet declare.  Nothing imports them for a return value -- they are imported for the SIDE
EFFECT, and upstream's own `types/__init__.py` is what imports them.  The drop-in
replaces that `__init__` with ours, and ours does not.  So in every run graded so far the
layer was ABSENT, and the tests exercising it failed naming something else:
`ReportingWebhook.operation_id` read as "a field upstream's class states and its document
does not" when the document admits it and a patcher installs it
(`verdicts/name-reaches-machinery.md` cause 3).  It is the same shape as the harness
laying upstream's whole `src/adcp/` and substituting only `types/` -- a lane repaired nine
sites and the suite moved by ZERO tests, because the file the run executed was upstream's.

**THE SET IS DERIVED AND NOT THE FOUR NAMES `CLAUDE.md` CARRIES.**  A module qualifies
when its own AST STORES into some other object's `model_fields` or `__annotations__`,
deletes from one, or calls `model_fields.pop`/`update`/`setdefault`.  A READ --
`if "operation_id" not in X.model_fields` -- is not a patch, which is why the predicate is
a store and not a mention.  The derived set is printed beside the documented four, so a
module gained or lost upstream reads as a difference rather than as silence.

**AND THE SIZE IS MEASURED DYNAMICALLY, BECAUSE THE AST UNDERSTATES IT.**  Counting store
SITES reads 9 over 3 modules; the patches are applied in loops over tuples of models, so
the true figure is 19 classes and 22 fields.  `layer_size` snapshots every class in
upstream's `domains/` tree in one subprocess, imports one patcher and snapshots again in
another, and diffs.

**TWO CORRECTIONS ARE BAKED INTO THAT DIFF, and each moved the headline by 40x.**  Stated
here because a reader who re-derives this without them gets a number forty times too big
and has no reason to doubt it:

1. **Both sides are REBUILT.**  Under `defer_build=True` an untouched model's
   `FieldInfo.annotation` is still a `ForwardRef`, and importing a patcher builds models
   as a side effect -- so the "after" side has resolved annotations the "before" side does
   not.  Uncorrected: 794 classes touched.  With `model_rebuild()` on both sides: 19.
2. **Function addresses are NORMALISED out of the repr.**  A `FieldInfo`'s metadata reprs
   as `BeforeValidator(func=<function as_json_schema_integer at 0x7b4b927a2>)`, and the two
   snapshots are two PROCESSES, so every address differs.  Uncorrected: 1,392 altered
   fields.  With ` at 0x…` stripped: 19.

**WHAT IT DOES NOT DO.**  It never decides whether a patch SHOULD be carried.  Carrying an
extension is a widening (reading 2) and that is an owner-level decision; this module's job
is to make the decision possible by stating the size, the blast radius and the cost.
"""

from __future__ import annotations

import argparse
import ast
import collections
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

#: The table :func:`main` writes and :func:`restored_paths` reads back.  One name, because a
#: second reader spelling the path itself is how two instruments come to classify two trees.
TABLE = HERE / "upstream-machinery-9.6.1.tsv"

#: The marker a module of ours sets to say it restates upstream's words rather than declaring
#: a subject (`survey/alias_surface.MODULE_MARKER`), read here to tell an ADAPTER module of
#: ours from a module of ours proper.
MARKER = "__adcp_restates_upstream__"

#: Upstream's generated tree, whose modules this survey does not range over: the question is
#: about the files BESIDE it.
THEIR_GEN = "src/adcp/types/domains/"


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=HERE.parent, capture_output=True, text=True, check=True
    ).stdout


def files(rev: str) -> list[str]:
    out = git("ls-tree", "-r", "--name-only", rev, "--", "src/adcp/types/")
    return sorted(
        p
        for p in out.splitlines()
        if p.endswith(".py") and not p.startswith(THEIR_GEN) and p != "src/adcp/types/__init__.py"
    )


def importers(rev: str, module: str, scope: str) -> list[str]:
    """Upstream's own files under `scope` that import `adcp.types.<module>` at any depth."""
    pattern = rf"(from|import) +adcp\.types\.{re.escape(module)}\b"
    out = subprocess.run(
        ["git", "grep", "-l", "-E", pattern, rev, "--", scope],
        cwd=HERE.parent,
        capture_output=True,
        text=True,
    ).stdout
    return sorted(line.split(":", 1)[1] for line in out.splitlines() if ":" in line)


#: A header that names a generator and the document it read is upstream SAYING the file is
#: generated; the second arm is the shape of an aggregator, measured rather than guessed
#: (`_generated.py` 1,038 `from adcp.types` lines over 6,687 lines of nothing else).
GENERATED_HEADER = re.compile(
    r"DO NOT EDIT|regenerate with|generated from OpenAPI|@generated|Auto-generated by",
    re.IGNORECASE,
)

#: **THE BUNDLE THIS COMPILER COMPILES, which is the whole of its input.**  Named so
#: :func:`reproducible_here` can ask the question the verdict is actually about instead of a
#: correlate of it.
BUNDLE = ROOT / "schemas/cache/3.2"

#: A SOURCE PATH a generated header names -- `Source: schemas/registry-openapi.yaml`, or the
#: input a rebuild command reads.  Only a path is matched: a URL is not a file a run can
#: open and falls through to "names no source", which is the reproducible case.
SOURCE_NAMED = re.compile(r"(?:Source|Generated from|Input)\s*:\s*([\w./-]+\.\w+)")


def reproducible_here(head: str) -> tuple[bool, str]:
    """Is the SOURCE this generated file names a document of the compiler's input?

    **THE PROPERTY, after a correlate stood in for it through three rulings**
    (`adcp-client-python-jlsp`).  `GENERATED-STAYS-DELETED` is a claim that OUR compiler
    produces these subjects from its OWN input, so the file is owed no restore.  The test
    for it was "does a header name a generator", which is a fact about upstream's prose
    rather than about our input -- and it held for four of the five generated modules only
    because those four happen to be generated FROM the bundle.

    `registry.py` separated them.  Its header says `Source: schemas/registry-openapi.yaml`;
    that file is in this repository and is NOT under :data:`BUNDLE`, and measured, nothing
    under `codegen/` opens a `.yaml` at all.  So its 155 classes are unreproducible here --
    `BrandActivity` occurs zero times in `codegen/published.json` because it was never in
    the JSON-Schema tree -- and "stays deleted" was a promise about 155 classes no run can
    emit.

    **THE READING IS THE PATH AND NOT THE SUFFIX.**  A named source counts as the
    compiler's input when :data:`BUNDLE` contains it, so a future generator reading some
    other non-bundle file is caught whatever it is written in, and a header naming a bundle
    document stays reproducible.  A header naming no path at all is reproducible, which is
    the four: they say "from JSON schemas", "regenerated from schemas" and "from the
    generated domain tree" -- the bundle, and the tree the bundle produces.
    """
    for match in SOURCE_NAMED.finditer(head):
        named = match.group(1)
        candidate = ROOT / named
        if candidate.is_file() and BUNDLE not in candidate.resolve().parents:
            return False, f"its generator reads {named}, which is not in the compiler's input"
    return True, "upstream's own header names the generator"


def blob(data: bytes) -> str:
    """Git's own object name for these bytes, which is byte identity said in one word."""
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()  # noqa: S324 -- git's


def rows(table: Path = TABLE) -> tuple[str, list[dict[str, str]]]:
    """The classification's rows, and the upstream commit every one of them is about.

    The rev is read off the table's own header line -- the line :func:`main` writes -- so a
    reader cannot pin a commit the table was not taken at.
    """
    text = table.read_text().splitlines()
    rev = next(
        (ln.rsplit(" ", 1)[1] for ln in text if ln.startswith("# ") and "upstream " in ln), ""
    )
    assert rev, f"{table} names no upstream commit in its header"
    return rev, list(csv.DictReader([ln for ln in text if not ln.startswith("#")], delimiter="\t"))


def restored_paths(table: Path = TABLE) -> frozenset[Path]:
    """The paths where UPSTREAM'S OWN hand-written file is sitting right now, byte for byte.

    **THE POPULATION IS THE CLASSIFICATION'S AND THE ANSWER IS A MEASUREMENT.**  The table
    supplies the rows (which of upstream's `types/` files exist at all, and which commit
    they are read at); byte identity against that commit supplies the verdict, so a module
    restored AFTER the table was last written is protected without anyone editing a list --
    and a table gone stale the other way cannot report a file as upstream's when the bytes
    at the path are not.  `here_now` is :func:`main`'s record of the same reading and is what
    `tests_emit/test_the_restored_machinery.py` ranges over; this is the reading taken live,
    for an instrument that is about to WRITE one of these paths.

    One `git ls-tree` and no `git show` per row: byte identity IS blob identity, so the
    comparison is upstream's object name against :func:`blob` of what is on disk.

    The marker clause is the one case where identical bytes would be the wrong answer:
    nothing an adapter of ours wrote can be upstream's file, and a path carrying the marker
    is answered by the writer's own ownership rule rather than by this one.
    """
    rev, table_rows = rows(table)
    listing = git("ls-tree", "-r", rev, "--", "src/adcp/types/")
    theirs: dict[str, str] = {}
    for line in listing.splitlines():
        meta, _, path = line.partition("\t")
        parts = meta.split()
        if len(parts) == 3 and parts[1] == "blob":
            theirs[path] = parts[2]
    out = set()
    for row in table_rows:
        path = row["upstream_path"]
        here = ROOT / path
        if not here.is_file() or path not in theirs:
            continue
        data = here.read_bytes()
        if MARKER.encode() in data:
            continue
        if blob(data) == theirs[path]:
            out.add(here.resolve())
    return frozenset(out)


# ------------------------------------------------------------------ the PATCH LAYER
#: What `CLAUDE.md` names, printed beside the DERIVED set.  Not an input to anything: a
#: difference between this and :func:`patchers_by_ast` is itself the finding.
DOCUMENTED = ("_ergonomic", "_forward_compat", "canonical_creative", "aliases")

#: Attributes whose SUBSCRIPT ASSIGNMENT is a patch of a generated model.
PATCHED_ATTRS = ("model_fields", "__annotations__")

#: Methods on `model_fields` that MUTATE it.  `get`, `items` and `keys` are reads and are
#: deliberately absent -- the predicate is a store, never a mention.
MUTATORS = ("pop", "update", "setdefault", "clear")

#: `<function f at 0x7b4b927a2>`.  Two snapshots are two processes, so the address always
#: differs and is never a patch.  Docstring correction 2.
ADDRESS = re.compile(r" at 0x[0-9a-f]+")

#: Snapshot every class upstream's generated tree DEFINES, with enough of each field to see
#: a patch.  Rebuilt first -- docstring correction 1 -- and run in the WHEEL's interpreter,
#: because the tree being measured is the wheel's and not this repository's.
SNAPSHOT = r"""
import sys, json, warnings, pkgutil, importlib
warnings.simplefilter("ignore")
which = sys.argv[1]
if which != "none":
    try:
        importlib.import_module(which)
    except Exception as exc:
        print(json.dumps({"__error__": type(exc).__name__ + ": " + str(exc)}))
        raise SystemExit(0)
import adcp.types.domains as D
classes = {}
for mod in pkgutil.walk_packages(D.__path__, D.__name__ + "."):
    try:
        m = importlib.import_module(mod.name)
    except Exception:
        continue
    for k, v in vars(m).items():
        if not (isinstance(v, type) and hasattr(v, "model_fields")):
            continue
        if getattr(v, "__module__", "") == mod.name:
            classes[mod.name + "." + k] = v
for v in classes.values():
    try:
        v.model_rebuild()
    except Exception:
        pass
def finfo(f):
    return {
        "ann": repr(f.annotation), "req": f.is_required(), "def": repr(f.default),
        "meta": repr(sorted(map(repr, f.metadata))), "alias": f.alias,
        "depr": bool(getattr(f, "deprecated", None)),
    }
print(json.dumps({k: {n: finfo(f) for n, f in v.model_fields.items()} for k, v in classes.items()}))
"""

#: Import one module in the tree under test and say whether it loads and where it dies.
#: The LAST frame inside the package is the site that matters: a patcher dying at its own
#: module scope names the import it cannot satisfy.
PROBE = r"""
import sys, json, warnings, traceback, importlib
warnings.simplefilter("ignore")
name = sys.argv[1]
try:
    importlib.import_module(name)
    print(json.dumps({"module": name, "loads": True}))
except BaseException as exc:
    frames = [f for f in traceback.extract_tb(sys.exc_info()[2]) if "adcp" in (f.filename or "")]
    last = frames[-1] if frames else None
    print(json.dumps({
        "module": name, "loads": False,
        "error": type(exc).__name__, "message": str(exc).split(" (")[0],
        "at": (last.filename.split("/src/")[-1] + ":" + str(last.lineno)) if last else None,
    }))
"""


def patchers_by_ast(types_dir: Path) -> dict[str, list[str]]:
    """Every module under `types/` whose AST STORES into another model's fields.

    The value is the store sites as `owner.attr[key]` text, so a reader sees WHAT each
    module claims to patch without opening it.  A module that only READS `model_fields` is
    absent by construction.
    """
    found: dict[str, list[str]] = {}
    for path in sorted(types_dir.glob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except (OSError, SyntaxError):
            continue
        sites: list[str] = []
        for node in ast.walk(tree):
            stores: list[ast.expr] = []
            if isinstance(node, ast.Assign):
                stores = list(node.targets)
            elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
                stores = [node.target]
            elif isinstance(node, ast.Delete):
                stores = list(node.targets)
            for target in stores:
                if (
                    isinstance(target, ast.Subscript)
                    and isinstance(target.value, ast.Attribute)
                    and target.value.attr in PATCHED_ATTRS
                ):
                    verb = "del" if isinstance(node, ast.Delete) else "set"
                    sites.append(f"{verb} {ast.unparse(target)}")
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in MUTATORS
                and isinstance(node.func.value, ast.Attribute)
                and node.func.value.attr == "model_fields"
            ):
                sites.append(f"call {ast.unparse(node.func)}()")
        if sites:
            found[path.stem] = sites
    return found


def probe(python: Path, script: str, *args: str) -> dict[str, object]:
    """One probe, in the interpreter that OWNS the tree being measured.

    **``-I``, AND IT IS THE WHOLE CORRECTNESS OF THIS FUNCTION.**  The documented way to
    run this instrument is ``PYTHONPATH=.:src python -m survey upstream_machinery``, and a
    subprocess INHERITS that -- so the wheel's interpreter imported THIS repository's
    ``src/adcp`` and reported ``No module named 'adcp.types._ergonomic'`` for three of
    upstream's own modules, which is true of our tree and says nothing about the wheel's.
    ``-I`` is ``-E -s``: it drops ``PYTHONPATH`` and user site, while a venv interpreter
    still finds its OWN ``site-packages`` through its prefix.  So each probe sees exactly
    the tree whose interpreter it is, which is the only reading either figure can mean.
    """
    done = subprocess.run(
        [str(python), "-I", "-c", script, *args], capture_output=True, text=True, check=False
    )
    lines = done.stdout.strip().splitlines()
    if not lines:
        return {"__error__": (done.stderr or "no output").strip()[-300:]}
    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError:
        return {"__error__": lines[-1][:300]}


def _normalised(field: dict[str, object]) -> dict[str, object]:
    return {k: (ADDRESS.sub("", v) if isinstance(v, str) else v) for k, v in field.items()}


def layer_size(
    python: Path, patchers: list[str]
) -> tuple[dict[str, tuple[int, int, int]], dict[str, list[str]]]:
    """Per patcher: classes touched, fields added, fields altered -- and the inventory.

    The bare snapshot is taken ONCE and reused: it walks upstream's whole generated tree,
    and the baseline is the same for every patcher.
    """
    bare = probe(python, SNAPSHOT, "none")
    if "__error__" in bare:
        raise SystemExit(f"could not snapshot the wheel's generated tree: {bare['__error__']}")
    sizes: dict[str, tuple[int, int, int]] = {}
    inventory: dict[str, list[str]] = {}
    for name in patchers:
        after = probe(python, SNAPSHOT, f"adcp.types.{name}")
        if "__error__" in after:
            sizes[name] = (-1, -1, -1)
            inventory[name] = [f"(does not import in the wheel: {after['__error__']})"]
            continue
        touched: set[str] = set()
        entries: list[str] = []
        for cls, before in bare.items():
            now = after.get(cls)
            if not isinstance(before, dict) or not isinstance(now, dict):
                continue
            short = cls.replace("adcp.types.domains.", "")
            for field in sorted(set(now) - set(before)):
                entries.append(f"+{short}.{field}")
                touched.add(cls)
            for field in sorted(set(before) - set(now)):
                entries.append(f"-{short}.{field}")
                touched.add(cls)
            for field in sorted(set(before) & set(now)):
                if _normalised(before[field]) != _normalised(now[field]):
                    entries.append(f"~{short}.{field}")
                    touched.add(cls)
        sizes[name] = (
            len(touched),
            sum(1 for e in entries if e[0] == "+"),
            sum(1 for e in entries if e[0] == "~"),
        )
        inventory[name] = entries
    return sizes, inventory


def tree_verdict(python: Path, patchers: list[str]) -> list[dict[str, object]]:
    """Does each patcher LOAD in the tree under test, and where exactly does it die."""
    return [probe(python, PROBE, f"adcp.types.{n}") for n in [*patchers, "_eager"]]


def patch_cost(tree: Path, inventory: dict[str, list[str]]) -> dict[str, object]:
    """How many of the tree's FAILING tests name a class or field the layer patches.

    Read off pytest's own JSON report -- the same files `survey/causes.py` reads, so the
    two instruments cannot disagree about an outcome.

    **AN UPPER BOUND ON ATTRIBUTION AND A LOWER BOUND ON REACH, and both halves matter.**
    A failure naming a patched class is not proof the missing patch caused it, and a
    failure the patch would have prevented need not name the class.  Stated here rather
    than smoothed into one number a reader would take for an attribution.
    """
    chunks = sorted((tree / "junit").glob("chunk-*.json"))
    if not chunks:
        return {"chunks read": 0}
    tests: dict[str, dict[str, object]] = {}
    for chunk in chunks:
        for entry in json.loads(chunk.read_text())["tests"]:
            tests[entry["nodeid"]] = entry
    # **ONLY REAL ENTRIES, because a placeholder is not a patched name.**  A patcher that
    # does not import leaves its reason in the inventory, and reading that string as
    # `class.field` yielded the word `adcp` -- which matched 652 of 1,202 failures and
    # reported a parse accident as the layer's blast radius.
    words: set[str] = set()
    for entries in inventory.values():
        for entry in entries:
            if entry[:1] not in "+-~":
                continue
            cls, _, field = entry[1:].rpartition(".")
            words.add(cls.rpartition(".")[2])
            words.add(field)
    words.discard("")
    if not words:
        return {"chunks read": len(chunks), "no patched names to look for": True}
    hits: collections.Counter[str] = collections.Counter()
    failing = 0
    for nodeid, entry in tests.items():
        if entry["outcome"] not in ("failed", "error"):
            continue
        failing += 1
        blob = []
        for phase in ("call", "setup", "teardown"):
            part = entry.get(phase) or {}
            if part.get("outcome") in ("failed", "error"):
                blob.append((part.get("crash") or {}).get("message", ""))
                blob.append(part.get("longrepr") or "")
        if any(word in "\n".join(blob) for word in words):
            hits[nodeid.split("::")[0]] += 1
    return {
        "chunks read": len(chunks),
        "failing in this run": failing,
        "naming a patched class or field": sum(hits.values()),
        "files": hits.most_common(14),
    }


def report_patch_layer(wheel: Path, tree: Path | None, inventory_wanted: bool) -> int:
    """The second question, printed.  Reads two trees and writes neither."""
    types_dir = wheel / "adcp" / "types"
    if not types_dir.is_dir():
        raise SystemExit(f"no adcp/types/ under {wheel}")
    # `site-packages` is `<venv>/lib/pythonX.Y/site-packages`, so the interpreter that owns
    # it is three levels up.  DERIVED and not a flag: a `--python` that disagreed with
    # `--wheel` would measure one tree and name another.
    wheel_python = wheel.parents[2] / "bin" / "python"
    if not wheel_python.exists():
        raise SystemExit(f"no interpreter at {wheel_python}")

    print(f"== upstream's types/ at {wheel}")
    derived = patchers_by_ast(types_dir)
    print(
        f"\n== the patch layer, DERIVED from the AST "
        f"({len(derived)} modules store into a model)"
    )
    for name, sites in derived.items():
        print(f"   {name:24s} {len(sites):3d} store site(s)")
        for site in sites[:3]:
            print(f"       {site[:92]}")
        if len(sites) > 3:
            print(f"       ... {len(sites) - 3} more")
    print(f"\n   CLAUDE.md names : {sorted(DOCUMENTED)}")
    print(f"   derived here    : {sorted(derived)}")
    if only_doc := sorted(set(DOCUMENTED) - set(derived)):
        print(f"   documented but STORES NOTHING directly: {only_doc}")
    if only_der := sorted(set(derived) - set(DOCUMENTED)):
        print(f"   derived but UNDOCUMENTED              : {only_der}")

    # Every DOCUMENTED patcher is measured too, even where it stores nothing directly: a
    # module can install a facade CLASS rather than edit a field, and a zero is the finding.
    measured = sorted(set(DOCUMENTED) | set(derived))
    print(
        f"\n== the layer's SIZE, measured in {wheel_python} "
        f"(both sides rebuilt, addresses normalised)"
    )
    sizes, inventory = layer_size(wheel_python, measured)
    print(f"   {'patcher':26s} {'classes':>8s} {'+fields':>8s} {'~fields':>8s}")
    for name in measured:
        touched, added, altered = sizes[name]
        if touched < 0:
            print(f"   {name:26s}   {inventory[name][0][:60]}")
            continue
        print(f"   {name:26s} {touched:8d} {added:8d} {altered:8d}")
    whole = {e for entries in inventory.values() for e in entries if e[:1] in "+-~"}
    print(
        f"   {'-- the layer, deduplicated':26s} "
        f"{len({e[1:].rpartition('.')[0] for e in whole}):8d} "
        f"{sum(1 for e in whole if e[0] == '+'):8d} {sum(1 for e in whole if e[0] == '~'):8d}"
    )
    if inventory_wanted:
        for entry in sorted(whole):
            print(f"       {entry}")

    if tree is None:
        return 0
    tree_python = tree / ".venv" / "bin" / "python"
    if not tree_python.exists():
        raise SystemExit(f"no interpreter at {tree_python}")
    print(f"\n== does the layer LOAD in {tree}")
    dead = []
    for row in tree_verdict(tree_python, measured):
        name = str(row.get("module", "?"))
        if row.get("loads"):
            print(f"   OK      {name}")
            continue
        dead.append(name)
        print(f"   BROKEN  {name}")
        print(f"             at {row.get('at')}  ->  {row.get('error')}: {row.get('message')}")
    print(f"\n   {len(dead)} of {len(measured) + 1} do not load, so their patches never run.")

    print(f"\n== the cost, from {tree}/junit/chunk-*.json")
    for key, value in patch_cost(tree, inventory).items():
        if key == "files":
            print("   failing tests naming one, by file:")
            for name, n in value:  # type: ignore[union-attr]
                print(f"       {n:4d}  {name}")
        else:
            print(f"   {key}: {value}")
    print(
        "\n   UPPER BOUND on attribution, LOWER BOUND on reach: naming a patched class is"
        "\n   not proof the missing patch caused the failure, and a failure the patch would"
        "\n   have prevented need not name the class."
    )
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rev", default="4ed0bce87", help="upstream's commit, recorded on every row")
    ap.add_argument("--table", type=Path, metavar="PATH")
    ap.add_argument(
        "--wheel", type=Path, metavar="PATH",
        help="upstream's site-packages: ask the PATCH-LAYER question instead",
    )
    ap.add_argument(
        "--tree", type=Path, metavar="PATH",
        help="a drop-in --out, for whether the layer loads there and what it cost",
    )
    ap.add_argument(
        "--inventory", action="store_true", help="with --wheel, list every patched field"
    )
    args = ap.parse_args()

    # **TWO QUESTIONS, ONE POPULATION, AND THE FLAG CHOOSES.**  `--wheel` needs no git and
    # writes no table; the classification needs git and no wheel.  Branching here keeps
    # every existing invocation -- `--rev`/`--table` -- byte-identical in behaviour.
    if args.wheel:
        raise SystemExit(report_patch_layer(args.wheel, args.tree, args.inventory))

    rows = []
    for path in files(args.rev):
        module = path[len("src/adcp/types/") : -len(".py")].replace("/", ".")
        body = git("show", f"{args.rev}:{path}")
        head = "\n".join(body.splitlines()[:30])
        adcp_types_lines = sum(
            1 for ln in body.splitlines() if re.match(r"\s*(from|import) +adcp\.types", ln)
        )
        src_all = importers(args.rev, module, "src/adcp")
        src = [p for p in src_all if not p.startswith("src/adcp/types/")]
        tests = importers(args.rev, module, "tests")
        generated = bool(GENERATED_HEADER.search(head)) or adcp_types_lines > 200
        # **GENERATED IS NOT THE SAME CLAIM AS REPRODUCIBLE** (:func:`reproducible_here`).
        # A file upstream generated from OUR input stays deleted, because our compiler
        # emits those subjects; one generated from a source the compiler never reads is
        # owed a restore like any hand-written module, and `registry` is that case.
        from_our_input, generated_why = reproducible_here(head) if generated else (True, "")
        here = HERE.parent / path
        if generated and from_our_input:
            verdict, why = "GENERATED-STAYS-DELETED", generated_why
        elif generated:
            verdict, why = "VENDOR-UPSTREAMS-BYTES", generated_why
        elif src:
            verdict, why = "LIVE-RESTORE", f"{len(src)} source importers outside types/"
        elif src_all:
            verdict, why = (
                "LIVE-TRANSITIVELY",
                f"no direct source importer; {len(src_all)} importers inside types/",
            )
        else:
            verdict, why = (
                "TEST-ONLY-DELETE",
                f"0 source importers, {len(tests)} test importers: a curated topic module",
            )
        # **"IS UPSTREAM'S FILE HERE" IS BYTE IDENTITY AND NOT "DOES A FILE EXIST".**  Our
        # EMITTED domain surfaces occupy `core`, `creative`, `media_buy`, `protocol`,
        # `signals` and `error_details` -- names upstream used for machinery -- so a column
        # that said "present" because something is at the path reported five modules of OURS
        # as upstream's restored machinery, and the gate that reads this column then demanded
        # a fresh emit not write `core.py`.  Measured: the test failed on exactly those five
        # and on nothing else, which is the column being wrong and the gate being right.
        if not here.exists():
            state = "absent"
        elif MARKER in (text := here.read_text()):
            state = "adapter-module"
        elif text == body:
            state = "restored"
        else:
            state = "ours"
        rows.append(
            {
                "module": module,
                "upstream_path": path,
                "lines": len(body.splitlines()),
                "adcp_types_imports": adcp_types_lines,
                "src": len(src),
                "src_all": len(src_all),
                "tests": len(tests),
                "generated_header": int(bool(GENERATED_HEADER.search(head))),
                "verdict": verdict,
                "here_now": state,
                "why": why,
            }
        )

    import collections

    for verdict, n in collections.Counter(r["verdict"] for r in rows).most_common():
        print(f"  {verdict:26} {n:4} modules")
    if args.table:
        cols = list(rows[0])
        with args.table.open("w") as fh:
            fh.write(f"# survey/upstream_machinery.py over upstream {args.rev}\n")
            fh.write("\t".join(cols) + "\n")
            for r in rows:
                fh.write("\t".join(str(r[c]) for c in cols) + "\n")
        print(f"  table -> {args.table}")


if __name__ == "__main__":
    main()
