"""The deselect list: upstream's tests that assert on THEIR generator's invented default.

**WHY A TEST IS DECLINED AND NEVER "FAILED".**  ``adcp-client-python-eknd``'s worked proof is
the template and nothing qualifies that does not match it:

    ``media-buy/create-media-buy-response.json`` is ``allOf[2]`` + ``oneOf[3]``.  ``allOf[1]``
    declares ``status`` and lists it in ``required``, so the CONJUNCTION requires ``status``
    for every branch; only ``oneOf[2]`` narrows its value to the const ``'submitted'``.
    Upstream emits ``CreateMediaBuyResponse1.status: Literal['completed'] = 'completed'``.  A
    DEFAULT MAKES A REQUIRED FIELD OPTIONAL, so their class ADMITS a payload the document
    REFUSES, and it additionally pins a value the document states nowhere for that branch.

A test asserting that default is asserting a defect.  It grades upstream's GENERATOR and not
the protocol, and **it cannot pass against any implementation that honours the document** --
so counting it in the denominator makes our own figure a lie in the direction that flatters
us.  Target 4 is "every test that grades the PROTOCOL passes", not "upstream's suite passes";
the second is unachievable without reproducing their bugs, and chasing it is how a defect gets
copied to make a number go up.

**THE DROP IS DERIVED FROM THE CLASSIFICATION AND NEVER FROM A RUN.**  The only input is
``survey/invented_defaults.attribute`` -- the 867 pairs, each ``OURS``, ``THEIRS`` or
``ELSEWHERE`` -- and a test is listed ONLY where it asserts on a ``THEIRS`` pair.  Nothing
here reads a test result, a duration or a traceback: a red test that is not on a ``THEIRS``
pair stays in the denominator, and a green one that is on one is still declined, because the
question is what the test GRADES and not what it currently does.

**UPSTREAM'S SUITE STAYS BYTE-IDENTICAL.**  Nothing is edited under ``tests/``.  The output is
a list of node ids the RUNNER declines, each carrying the pair it asserts and the document and
pointer that refutes it, so a reader can check any single row against the bundle without
running anything.  If the classification moves, the list regenerates and nothing is
hand-maintained.

Run::

    PYTHONPATH=.:src ./.venv/bin/python survey/dropin/deselect.py --write
    PYTHONPATH=.:src ./.venv/bin/python survey/dropin/deselect.py --pytest-args
    PYTHONPATH=.:src ./.venv/bin/python survey/dropin/deselect.py --collect

and the runner declines them with the list this writes::

    ./.venv/bin/python -m pytest tests/ \\
        $(PYTHONPATH=.:src ./.venv/bin/python survey/dropin/deselect.py --pytest-args)
"""

from __future__ import annotations

import argparse
import ast
import collections
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for entry in (str(ROOT), str(ROOT / "src"), str(ROOT / "survey")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

import invented_defaults as classification  # noqa: E402

#: Upstream's own behavioural suite, on this branch.  ``tests/`` is THEIRS here and
#: ``tests_emit/`` is ours -- the same reading ``./check`` makes of which directory holds a
#: suite, and the reason nothing in this file may write under it.
UPSTREAM = ROOT / "tests"

#: Where the list is written.
TABLE = HERE / "deselected-9.6.1.tsv"

#: Upstream's own test files that grade THEIR GENERATOR rather than SDK behaviour, DECLARED in
#: this repository because no predicate over a path separates them.  A row from one of these
#: is reported with ``generator-grading`` in its own column: those files are already outside
#: the behavioural denominator, so declining them changes no figure and the column says so
#: rather than letting a reader think the drop is larger than it is.
GENERATOR_TESTS = HERE / "upstream-tests-about-their-generator.txt"

#: The two idioms a test uses to depend on a default, and the whole of what this reads.
#:
#: **A THIRD IDIOM IS NOT READ AND IS NAMED RATHER THAN GUESSED AT**: a payload built in one
#: place and validated in another has no keys at the call site, so this cannot see whether the
#: field is in it.  The list is therefore a FLOOR, which is the safe direction -- a test this
#: misses stays in the denominator and counts against us.
IDIOMS = ("keyword-construction", "model_validate-dict-literal")


class Dropped(NamedTuple):
    """One test declined, and everything needed to check the decision without a run."""

    #: The pytest node id, which is what the runner declines.
    node_id: str
    #: Upstream's file, as the declared split sees it.
    upstream_file: str
    #: ``behavioural`` or ``generator-grading``.
    denominator: str
    #: The class whose default the test leans on.
    model: str
    #: The field, by the WIRE key the document states.
    field: str
    #: The document and pointer that REFUTES the default -- where the conjunction requires it.
    document: str
    pointer: str
    #: What upstream's class defaults it to.
    upstream_default: str
    #: What the document states at that position: ``const=...`` or ``nothing``.
    document_states: str
    #: Which of :data:`IDIOMS` the test used.
    idiom: str
    #: The set's own kind for the pair, carried so a reader can sort by harm.
    kind: str


def _node_ids(tree: ast.Module) -> dict[ast.FunctionDef | ast.AsyncFunctionDef, str]:
    """Every test function of a module, with the node id pytest will give it.

    Classes are carried, because ``tests/`` holds ``TestX::test_y`` node ids and a list that
    spelled them as bare functions would decline nothing.  Nesting deeper than one class is
    not collected by pytest either, so it is not spelled here.
    """
    out: dict[ast.FunctionDef | ast.AsyncFunctionDef, str] = {}

    def walk(body: list[ast.stmt], prefix: str) -> None:
        for node in body:
            if isinstance(node, ast.ClassDef):
                if node.name.startswith("Test"):
                    walk(node.body, f"{prefix}{node.name}::")
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("test"):
                    out[node] = f"{prefix}{node.name}"

    walk(tree.body, "")
    return out


def _omits(call: ast.Call, fields: set[str]) -> str | None:
    """Which idiom this call uses to omit one of ``fields``, or ``None``.

    Two screens keep the answer a floor rather than an estimate:

    * a call carrying ``**`` is skipped outright -- the field may be in the mapping, and a
      site this cannot decide must not put a test on the list;
    * a ``model_validate`` whose first argument is not a dict LITERAL is skipped for the same
      reason: the keys are not at the site.
    """
    if isinstance(call.func, ast.Name):
        if any(word.arg is None for word in call.keywords):
            return None
        named = {word.arg for word in call.keywords}
        return "keyword-construction" if any(f not in named for f in fields) else None
    if (
        isinstance(call.func, ast.Attribute)
        and call.func.attr in ("model_validate", "model_validate_json")
        and call.args
        and isinstance(call.args[0], ast.Dict)
    ):
        literal = call.args[0]
        if any(key is None for key in literal.keys):
            return None
        keys = {
            key.value
            for key in literal.keys
            if isinstance(key, ast.Constant) and isinstance(key.value, str)
        }
        return "model_validate-dict-literal" if any(f not in keys for f in fields) else None
    return None


def _named(call: ast.Call) -> str | None:
    """The class name a call constructs or validates through, or ``None``."""
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name):
        return call.func.value.id
    return None


def theirs_by_class(pairs: list[classification.Whose]) -> dict[str, list[classification.Whose]]:
    """``class name -> its THEIRS pairs``.  **The only thing that puts a test on the list.**

    Keyed on the bare class name because that is what a test writes; upstream's own module
    path is carried on each pair, so a row still names the full class.
    """
    out: dict[str, list[classification.Whose]] = collections.defaultdict(list)
    for pair in pairs:
        if pair.whose == "THEIRS":
            out[pair.upstream.rsplit(".", 1)[1]].append(pair)
    return out


def dropped(pairs: list[classification.Whose], where: Path = UPSTREAM) -> list[Dropped]:
    """Every test of upstream's that asserts on a ``THEIRS`` default, with its reason.

    Parsed with ``ast`` and never grepped, so a class named in a string or a comment is not a
    construction.  One row per ``(test, pair, idiom)``: a test leaning on two different
    invented defaults is two rows, because each is a separate reason and dropping the test
    needs only one of them to hold.
    """
    by_class = theirs_by_class(pairs)
    declared = {
        line.strip()
        for line in GENERATOR_TESTS.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }
    rows: list[Dropped] = []
    for path in sorted(where.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        name = str(path.relative_to(ROOT))
        ids = _node_ids(tree)
        for function, suffix in ids.items():
            for inner in ast.walk(function):
                if not isinstance(inner, ast.Call):
                    continue
                held = by_class.get(_named(inner) or "")
                if not held:
                    continue
                for pair in held:
                    idiom = _omits(inner, {pair.field})
                    if idiom is None:
                        continue
                    rows.append(
                        Dropped(
                            node_id=f"{name}::{suffix}",
                            upstream_file=name,
                            denominator=(
                                "generator-grading" if name in declared else "behavioural"
                            ),
                            model=pair.upstream,
                            field=pair.field,
                            document=pair.document,
                            pointer=pair.pointer or "#",
                            upstream_default=pair.upstream_default,
                            document_states=pair.document_states,
                            idiom=idiom,
                            kind=pair.kind,
                        )
                    )
    return sorted(set(rows))


def collected(args: list[str]) -> int | None:
    """How many tests pytest collects for ``args``, or ``None`` where the run did not say.

    Read off pytest's own summary line rather than counted here, because the denominator a
    figure is stated over has to be the one the RUNNER used.  Collection errors do not stop
    the reading: the count is what was collected, and the errors are reported beside it.
    """
    found = subprocess.run(
        [sys.executable, "-m", "pytest", *args, "--collect-only", "-q"],
        capture_output=True,
        text=True,
        cwd=ROOT,
        env={"PYTHONPATH": f"{ROOT}:{ROOT / 'src'}", "PATH": "/usr/bin:/bin"},
        check=False,
    )
    for line in reversed(found.stdout.splitlines()):
        if "collected" in line or "tests collected" in line:
            for word in line.replace("/", " ").split():
                if word.isdigit():
                    return int(word)
    return None


def committed_rows(table: Path = TABLE) -> list[tuple[str, str, str]]:
    """The committed list as ``(path, test, reason)``, for the one table the runner reads.

    **TWO LAYERS DECLINE A TEST AND ONE TABLE HAS TO CARRY BOTH** (``adcp-client-python-l1r3``).
    This module's subject is upstream's INVENTED DEFAULTS -- a test leaning on a default that
    makes a required field optional -- and ``survey/upstream_test_character.py``'s subject is
    an assertion about their REPRESENTATION.  They are different readings of different
    evidence and neither subsumes the other, so both write rows and
    ``survey/regenerate.py`` merges them into the single ``deselect.tsv`` the plugin reads.
    Before that merge a built tree declined only the character classifier's rows and this
    whole classification did nothing to any figure.

    **EACH ROW KEEPS ITS OWN REASON**, which is why this returns a sentence and not a flag:
    the merged table's ``reason`` column for one of these names the model, the field, the
    document and the pointer that refutes the default, so a reader can check the row against
    the bundle without running anything -- exactly what the eleven columns here are for.
    The full eleven stay in ``deselected-9.6.1.tsv``; this is the projection the runner needs.

    A node id can appear more than once here, once per (test, pair).  The reasons are joined
    so one test is one row of the merged table and no pair is lost.
    """
    if not table.is_file():
        return []
    lines = table.read_text(encoding="utf-8").splitlines()
    if not lines:
        return []
    header = lines[0].split("\t")
    index = {name: i for i, name in enumerate(header)}
    merged: dict[tuple[str, str], list[str]] = {}
    for line in lines[1:]:
        if not line.strip():
            continue
        cells = line.split("\t")
        if len(cells) < len(header):
            continue
        node = cells[index["node_id"]]
        path, _, rest = node.partition("::")
        if not rest:
            continue
        # The FUNCTION is the last `::` segment with its parametrisation stripped -- a test
        # inside a class carries `<file>::<Class>::<test>`, and the runner keys on the
        # function exactly as `deselect_plugin` reads it off a nodeid.
        test = rest.split("::")[-1]
        why = (
            f"{cells[index['model']]}.{cells[index['field']]} leans on upstream's default "
            f"{cells[index['upstream_default']]}, which "
            f"{cells[index['document']]}{cells[index['pointer']]} refutes "
            f"(the document states {cells[index['document_states']]}); "
            f"kind {cells[index['kind']]}, idiom {cells[index['idiom']]}"
        )
        merged.setdefault((path, test.split("[")[0]), []).append(why)
    return [(path, test, " | ".join(whys)) for (path, test), whys in sorted(merged.items())]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help=f"write {TABLE.name}")
    parser.add_argument(
        "--pytest-args",
        action="store_true",
        help="print the --deselect flags a runner passes to pytest, one per line",
    )
    parser.add_argument(
        "--collect",
        action="store_true",
        help="ask pytest for the denominator with and without the list (slow: two collections)",
    )
    args = parser.parse_args(argv)

    source = classification.sources(classification.REVISION, ROOT)
    records = classification.records_of(classification.RECORDS)
    rows, _counts, _unread = classification.read(
        classification.declarations(source), records, classification.union_arms(source)
    )
    pairs = classification.attribute(rows, records)
    # **EVERY SET IS CLAIMED BEFORE A FIGURE IS READ OFF IT** -- `tests_emit/nodeset.py`'s
    # rule.  A classification that selected nothing would write an EMPTY deselect list, which
    # reads exactly like "nothing needed dropping" and is the one failure that would go
    # unnoticed.
    if not pairs:
        raise SystemExit("REFUSED: the classification is empty -- no pair to derive a drop from")
    theirs = [p for p in pairs if p.whose == "THEIRS"]
    if not theirs:
        raise SystemExit("REFUSED: no THEIRS pair -- the drop list would be empty by vacuity")

    found = dropped(pairs)
    tests = {row.node_id for row in found}
    behavioural = {row.node_id for row in found if row.denominator == "behavioural"}

    if args.pytest_args:
        for node in sorted(tests):
            print(f"--deselect={node}")
        return 0

    print(f"classification: {len(pairs)} pairs, {len(theirs)} THEIRS over "
          f"{len({p.upstream for p in theirs})} classes")
    print(f"DECLINED: {len(tests)} tests over {len({r.upstream_file for r in found})} files, "
          f"{len(found)} (test, pair) reasons")
    print(f"  {len(behavioural):5d}  in the 577 behavioural files")
    print(f"  {len(tests) - len(behavioural):5d}  in the 104 files that grade their generator")
    for kind, n in sorted(collections.Counter(r.kind for r in found).items()):
        print(f"  {n:5d}  reasons of kind {kind}")
    for idiom, n in sorted(collections.Counter(r.idiom for r in found).items()):
        print(f"  {n:5d}  reasons by idiom {idiom}")

    if args.write:
        lines = ["\t".join(Dropped._fields)]
        lines += ["\t".join(str(v) for v in row) for row in found]
        TABLE.write_text("\n".join(lines) + "\n")
        print(f"-> {TABLE}")

    if args.collect:
        raw = collected(["tests/"])
        flags = [f"--deselect={node}" for node in sorted(tests)]
        kept = collected(["tests/", *flags])
        print()
        print("THE TWO NUMBERS, and they are reported together:")
        print(f"  raw      : {raw} collected over upstream's whole suite")
        print(f"  declined : {len(tests)} tests, every one on a THEIRS pair")
        print(f"  graded   : {kept} collected with the list applied")
        if raw is not None and kept is not None:
            items = raw - kept
            print(f"  items    : {items} collected ITEMS declined, from {len(tests)} FUNCTIONS")
            if items != len(tests):
                # **A NODE ID IS A FUNCTION AND A COLLECTED ITEM IS A CASE**, and the gap is
                # parametrisation: `--deselect=f.py::test_x` declines every `test_x[...]` case
                # pytest generated from it.  Measured rather than assumed -- a collect-only run
                # matched 257 collected ids against these 72 prefixes -- so the two figures are
                # reported in their own units and neither is adjusted to meet the other.
                print(
                    f"           {items} and {len(tests)} are the same drop in two units: a "
                    "declined node id names a FUNCTION, and pytest collects one ITEM per "
                    "parametrised case of it."
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
