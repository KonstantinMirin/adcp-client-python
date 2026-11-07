"""WHAT DOES UPSTREAM'S TEST TEST? — behaviour, or their own implementation.

**THE DENOMINATOR IS THE CLAIM, NOT THE PASS-COUNT.**  Reading 10 is graded against the
imports an application already wrote, and upstream's 577 behavioural files are the one
measurement of it that is not a claim about our own table.  But a pass-count against
*their* suite is only meaningful to the extent their suite asserts BEHAVIOUR.  An
assertion about where a type lives, how it was generated, what its ``model_fields`` table
holds or which annotation OBJECT a field carries is a statement about *their generator*,
and ``docs/plan/final-state.md``'s preamble settles what to do with it: "reading 10 may
not reshape any of the nine to make itself easier.  Designing the classes so the aliases
are convenient is how upstream's mistakes arrive through the back door."  Conforming to
such an assertion is exactly that back door, so the assertion does not count and the test
behind it leaves the denominator.

**SO EVERY TEST FUNCTION GETS ONE OF THREE WORDS**, decided by what it ASSERTS and by the
route it takes to the subject — never by whether it passes:

``DELETE``
    The assertion itself is about their implementation.  There is no behaviour behind it:
    no payload, no envelope, no value the document admits or refuses.  Decided by AST over
    ``ast.Assert`` and over ``pytest.raises`` bodies, by the token table below, which is
    ``fwvm``'s rule carried forward and widened to the annotation object and the import
    system.

``PORT``
    The assertion is behavioural and the ROUTE is a spelling of their implementation —
    ``adcp.types.domains.**`` (their generated layout), ``adcp.types._generated`` (their
    eager re-export), ``adcp.types.domains.bundled.**`` (a projection
    ``codegen.bundle.PROJECTIONS`` excludes by its own words), or their hand-written
    boundary layer.  The behaviour is worth having and the test is worth keeping: it is
    re-pointed at ``adcp.types.<domain>`` and the assertion survives unchanged.

``BEHAVIOUR``
    The assertion is behavioural and the route is a surface a consumer writes — the flat
    ``adcp.types``, ``adcp.server``, ``adcp.client``, ``adcp.decisioning``,
    ``adcp.reporting``.  These are the tests whose verdict is about the ARTIFACT, and a
    failure among them is ours until proved otherwise.

**THE TOKENS ARE READ INSIDE ASSERTIONS ONLY, which is what keeps the rule honest.**  A
test may import ``model_fields`` to build a fixture and then assert on a wire envelope;
that is behaviour reached awkwardly, not an implementation assertion.  ``fwvm`` already
measured the converse trap and kept 12 tests a cruder rule would have taken, because
``model_fields_set`` mirrors a WIRE fact — whether the key was present on the payload —
so it is excluded from the table by name.

**AND THE COUNT IS OF TEST FUNCTIONS, NOT OF COLLECTED ITEMS.**  One parametrised
function is one row here and many rows in a junit; ``--junit`` joins the two so a figure
can be stated over either, and which one a number is over is printed with it.
"""

from __future__ import annotations

import argparse
import ast
import collections
import json
import pathlib
import sys

#: An assertion mentioning one of these is about their generator's REPRESENTATION and not
#: about a value on the wire.  Each carries the reason it is not behaviour, because a
#: discarded test is named with its ground or it is not discarded.
IMPLEMENTATION_TOKENS: tuple[tuple[str, str], ...] = (
    ("__module__", "asserts WHERE a type lives, which reading 6 makes ours to choose"),
    ("__qualname__", "asserts the generated class's qualified name"),
    ("__name__ ", "asserts a generated class's own name rather than a value"),
    ("__all__", "asserts an export inventory, not behaviour"),
    ("model_fields[", "asserts pydantic's field table — their generator's representation"),
    ("model_fields)", "asserts pydantic's field table — their generator's representation"),
    (".model_fields", "asserts pydantic's field table — their generator's representation"),
    ("model_fields ", "asserts pydantic's field table — their generator's representation"),
    ("model_rebuild", "asserts their generator's deferred-reference machinery"),
    (".annotation", "asserts the ANNOTATION OBJECT their generator emitted (0hp7/oswm)"),
    ("get_type_hints", "asserts the annotation objects their generator emitted"),
    ("__annotations__", "asserts the annotation objects their generator emitted"),
    ("adcp.types._generated", "asserts against their eager generated re-export module"),
    ("adcp.types.domains", "asserts against their generated module LAYOUT"),
    ("datamodel", "asserts on datamodel-code-generator's behaviour"),
    ("sys.modules", "asserts on the import system's state rather than on a response"),
    ("_dropin", "asserts on the drop-in finder itself"),
    ("__bases__", "asserts the inheritance their generator chose"),
    ("__mro__", "asserts the inheritance their generator chose"),
    ("__pydantic_", "asserts pydantic's private machinery"),
    ("inspect.getsource", "asserts the TEXT of a generated module"),
    ("inspect.signature", "asserts a generated signature rather than a value"),
)

#: ``model_fields_set`` mirrors a WIRE fact — whether the key was present on the payload —
#: so a test that checks it is checking what the envelope carried.  ``fwvm`` kept 12 tests
#: on this ground and the exclusion is inherited rather than re-decided.
WIRE_NOT_IMPLEMENTATION: tuple[str, ...] = ("model_fields_set",)

#: A spelling of their implementation.  A behavioural assertion reached through one of
#: these is PORTED — re-pointed at ``adcp.types.<domain>`` with the assertion unchanged.
THEIR_ROUTE: tuple[str, ...] = (
    "adcp.types.domains",
    "adcp.types._generated",
    "adcp.types._forward_compat",
    "adcp.types.projections",
    "adcp.types.aliases",
    "adcp.types.canonical_creative",
    "adcp.types.registry",
    "adcp.types._eager",
    "adcp.types._ergonomic",
)


#: **AND A FAILING BEHAVIOURAL TEST IS PORTED OR ADMITTED BY ITS CAUSE, NOT BY ITS SUBJECT.**
#: The AST decides DELETE and it decides the ROUTE, but it cannot decide why a behavioural
#: test failed -- and that is what separates "re-point it at ours and keep it" from "we are
#: wrong".  So the residue carries a second table, read off the failure's own text, and every
#: row names the document's verdict and ours.  ``PORT`` where the behaviour asserted is
#: untouched by the repair and the repair is in the FIXTURE or in their kept code; ``ADMIT``
#: where the repair is in OUR artifact.
CAUSE_RULES: tuple[tuple[str, tuple[str, ...], str, str], ...] = (
    (
        "PORT",
        ("input_value=None",),
        "explicit-null-the-document-refuses",
        "the document states the property `type: \"string\"` (not `[\"string\",\"null\"]`) and "
        "does not require it, so `{\"k\": null}` is a value it REFUSES; ours refuses it "
        "(reading 1) and upstream's generator emits `str | None = None`, which admits it. "
        "Their own kept code and fixtures then pass None EXPLICITLY. Under `exclude_none` the "
        "posted envelope is byte-identical with the key omitted, so the assertion survives "
        "the port unchanged.",
    ),
    (
        "PORT",
        ("Field required [type=missing",),
        "required-field-omitted-by-their-fixture",
        "`core/protocol-envelope.json` states `required: [\"status\"]` and every response "
        "document `allOf`s it, so a response without `status` is a document the bundle "
        "REFUSES; ours refuses it and theirs admits it. The fixture or stub platform supplies "
        "the field and the behaviour asserted -- routing, the envelope, the error code -- is "
        "unchanged.",
    ),
    (
        "PORT",
        ("is an invalid keyword argument for int()",),
        "their-RootModel-wrapper-for-a-constrained-scalar",
        "upstream's generator mints a `RootModel` per constrained scalar (`MajorVersion("
        "root=3)`); §5 sends such a node to an annotated scalar with NO class, so the "
        "wrapper has nothing to be. The fixture writes the value itself and the assertion is "
        "unchanged -- an alias cannot help, because there is no object to point at.",
    ),
    (
        "ADMIT",
        ("graded differently by the bundled schema",),
        "our-model-is-LAXER-than-the-document",
        "upstream's own conformance test perturbs each document and compares the bundled "
        "schema's verdict with the model's. EVERY divergence is in one direction: *the model "
        "accepts a document the bundled schema refuses* -- `'1'` and `True` where the document "
        "says `integer`, `'0'` and `False` where it says `number`. That is pydantic's lax "
        "coercion admitting a value reading 1 forbids, and it is OURS to fix.",
    ),
    (
        "ADMIT",
        ("type=model_type",),
        "an-alias-owed-for-an-inner-node",
        "their instance of a class upstream names at an inner node is refused where our field "
        "expects the §4-derived word for the same node. The repair is an alias or an export "
        "and touches no type.",
    ),
    (
        "ADMIT",
        ("resolves at no module",),
        "a-flat-name-with-a-subject-and-no-word",
        "the flat word reaches neither the alias table nor a kept module. Where the node is "
        "stated, an alias is owed; where it is not, reading 10 gives a migration note and "
        "never a class, and the test counts.",
    ),
    (
        "ADMIT",
        ("cannot import name",),
        "a-flat-name-with-a-subject-and-no-word",
        "same cause reached through `from adcp.types import X` rather than an attribute.",
    ),
)


def cause(text: str) -> tuple[str, str, str] | None:
    """The first rule whose tokens are all in the failure's own text, or ``None``."""
    for verdict, tokens, name, why in CAUSE_RULES:
        if all(token in text for token in tokens):
            return verdict, name, why
    return None


def _tests(tree: ast.Module):
    """Every test function, with the class that holds it where there is one."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith(
            "test"
        ):
            yield node


def _assertion_text(fn: ast.AST) -> list[str]:
    """Everything this test ASSERTS, as source text.

    ``ast.Assert`` is the plain form; ``pytest.raises`` is the other one, because a test
    whose whole claim is "this construction raises" asserts through the context manager
    and carries no ``assert`` at all.
    """
    out = []
    for sub in ast.walk(fn):
        if isinstance(sub, ast.Assert):
            out.append(ast.unparse(sub))
        elif isinstance(sub, ast.withitem):
            out.append(ast.unparse(sub))
        elif isinstance(sub, ast.Call):
            func = ast.unparse(sub.func)
            if func.endswith("assert_called_with") or func.startswith("assert"):
                out.append(ast.unparse(sub))
    return out


def _their_bindings(tree: ast.AST) -> dict[str, str]:
    """Every local NAME bound from a spelling of their implementation.

    **A FILE-LEVEL IMPORT IS NOT A ROUTE UNTIL A TEST USES WHAT IT BOUND**, which is the
    same rule the token table obeys one level along: one test in a file reaching
    ``adcp.types.domains`` does not make its 40 neighbours ports.  So the import is read
    for the names it BINDS and a test is a port when it references one of them.
    """
    bound: dict[str, str] = {}
    for sub in ast.walk(tree):
        if isinstance(sub, ast.ImportFrom) and sub.module:
            if any(sub.module == r or sub.module.startswith(r + ".") for r in THEIR_ROUTE):
                for alias in sub.names:
                    bound[alias.asname or alias.name.split(".")[0]] = sub.module
        elif isinstance(sub, ast.Import):
            for alias in sub.names:
                if any(alias.name == r or alias.name.startswith(r + ".") for r in THEIR_ROUTE):
                    bound[alias.asname or alias.name.split(".")[0]] = alias.name
    return bound


def _routes(bound: dict[str, str], fn: ast.AST) -> list[str]:
    """The implementation spellings THIS test actually reaches its subject through."""
    used = set()
    for sub in ast.walk(fn):
        if isinstance(sub, ast.Name) and sub.id in bound:
            used.add(bound[sub.id])
        elif isinstance(sub, ast.Attribute):
            text = ast.unparse(sub)
            for route in THEIR_ROUTE:
                if text.startswith(route + ".") or text == route:
                    used.add(route)
    return sorted(used)


def classify(path: pathlib.Path) -> list[dict]:
    """One row per test function in one file."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return []
    rows = []
    bound = _their_bindings(tree)
    for fn in _tests(tree):
        asserts = _assertion_text(fn)
        verdict, why, quoted = "BEHAVIOUR", "", ""
        for text in asserts:
            stripped = text
            for keep in WIRE_NOT_IMPLEMENTATION:
                stripped = stripped.replace(keep, "«wire»")
            hit = next((t for t in IMPLEMENTATION_TOKENS if t[0] in stripped), None)
            if hit is not None:
                verdict, why, quoted = "DELETE", hit[1], text[:220]
                break
        routes = _routes(bound, fn) + _routes(_their_bindings(fn), fn)
        if verdict == "BEHAVIOUR" and routes:
            verdict, why = "PORT", "behaviour reached through " + ", ".join(routes[:3])
        rows.append(
            {
                "file": str(path),
                "test": fn.name,
                "verdict": verdict,
                "why": why,
                "assertion": quoted,
                "routes": routes,
                "assertions": len(asserts),
            }
        )
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", help="the tree upstream's test files live in")
    ap.add_argument("--files", help="newline-separated list of paths relative to root")
    ap.add_argument("--junit", nargs="*", default=(), help="junit xml to join collected items on")
    ap.add_argument("--json", help="write every row here")
    ap.add_argument("--residue-json", help="write every failing row, with its verdict, here")
    args = ap.parse_args(argv)

    root = pathlib.Path(args.root)
    if args.files:
        rels = [l.strip() for l in pathlib.Path(args.files).read_text().split() if l.strip()]
    else:
        rels = [str(p.relative_to(root)) for p in sorted(root.glob("tests/**/test_*.py"))]

    rows: list[dict] = []
    for rel in rels:
        path = root / rel
        if path.is_file():
            for row in classify(path):
                row["file"] = rel
                rows.append(row)

    by = collections.Counter(r["verdict"] for r in rows)
    print(f"files read                      : {len(rels)}")
    print(f"TEST FUNCTIONS                  : {len(rows)}")
    for word in ("DELETE", "PORT", "BEHAVIOUR"):
        print(f"  {word:28s}: {by[word]}")
    print(f"  of which assert nothing at all: {sum(1 for r in rows if not r['assertions'])}")

    if args.junit:
        import xml.etree.ElementTree as ET

        key = {(r["file"], r["test"]): r for r in rows}
        items = collections.Counter()
        unmapped = collections.Counter()
        residue: list[dict] = []
        for p in args.junit:
            troot = ET.parse(p).getroot()
            suites = [troot] if troot.tag == "testsuite" else troot.findall("testsuite")
            for s in suites:
                for tc in s.findall("testcase"):
                    cn = (tc.get("classname") or "").split(".")
                    name = (tc.get("name") or "").split("[")[0]
                    outcome = (
                        "errored"
                        if tc.find("error") is not None
                        else "failed"
                        if tc.find("failure") is not None
                        else "skipped"
                        if tc.find("skipped") is not None
                        else "passed"
                    )
                    row = None
                    for cut in range(len(cn), 0, -1):
                        row = key.get(("/".join(cn[:cut]) + ".py", name))
                        if row is not None:
                            break
                    node = tc.find("error")
                    if node is None:
                        node = tc.find("failure")
                    msg, full = "", ""
                    if node is not None:
                        full = (node.get("message") or "") + "\n" + (node.text or "")
                        msg = (node.get("message") or "").strip().splitlines()
                        msg = msg[0] if msg else ""
                    if row is None:
                        unmapped[outcome] += 1
                        if outcome in ("failed", "errored"):
                            residue.append(
                                {
                                    "verdict": "UNMAPPED",
                                    "decided_by": "no test function this id maps to",
                                    "id": f"{tc.get('classname')}::{tc.get('name')}",
                                    "message": msg,
                                }
                            )
                    else:
                        items[(row["verdict"], outcome)] += 1
                        if outcome in ("failed", "errored"):
                            # DELETE is decided by the ASSERTION and outranks the cause: a
                            # test with no behaviour behind it does not become behaviour by
                            # failing for a reason we could repair.
                            found = None if row["verdict"] == "DELETE" else cause(full)
                            residue.append(
                                {
                                    "verdict": row["verdict"]
                                    if found is None
                                    else found[0],
                                    "decided_by": "assertion"
                                    if found is None
                                    else "cause:" + found[1],
                                    "id": f"{tc.get('classname')}::{tc.get('name')}",
                                    "file": row["file"],
                                    "test": row["test"],
                                    "why": row["why"] if found is None else found[2],
                                    "assertion": row["assertion"],
                                    "message": msg,
                                }
                            )
        print()
        print("COLLECTED ITEMS joined onto the verdicts (the junit's own rows):")
        tot = collections.Counter()
        for word in ("DELETE", "PORT", "BEHAVIOUR"):
            line = {o: items[(word, o)] for o in ("passed", "failed", "errored", "skipped")}
            n = sum(line.values())
            tot.update(line)
            print(
                f"  {word:10s} items {n:6d} | passed {line['passed']:6d} "
                f"failed {line['failed']:5d} errored {line['errored']:4d} "
                f"skipped {line['skipped']:5d}"
            )
        n = sum(unmapped.values())
        print(
            f"  {'UNMAPPED':10s} items {n:6d} | passed {unmapped['passed']:6d} "
            f"failed {unmapped['failed']:5d} errored {unmapped['errored']:4d} "
            f"skipped {unmapped['skipped']:5d}"
        )
        tot.update(unmapped)
        print(f"  {'TOTAL':10s} items {sum(tot.values()):6d} | " + " ".join(
            f"{o} {tot[o]}" for o in ("passed", "failed", "errored", "skipped")
        ))

        print()
        print(f"THE RESIDUE, {len(residue)} rows, partitioned:")
        import re as _re

        def _cls(m: str) -> str:
            m = _re.sub(r"\d+", "N", m)
            m = _re.sub(r"'[^']{0,80}'", "'…'", m)
            return m[:96]

        for word in ("DELETE", "PORT", "ADMIT", "BEHAVIOUR", "UNMAPPED"):
            part = [r for r in residue if r["verdict"] == word]
            label = "NOT-YET-DIAGNOSED" if word == "BEHAVIOUR" else word
            print(f"\n  {label} — {len(part)} rows")
            for name, n in collections.Counter(
                r["decided_by"] for r in part
            ).most_common():
                print(f"    {n:5d}  by {name}")
            if word in ("BEHAVIOUR", "UNMAPPED"):
                for m, n in collections.Counter(
                    _cls(r["message"]) for r in part
                ).most_common(12):
                    print(f"           {n:5d}  {m}")
        total = sum(1 for _ in residue)
        print(f"\n  A/B/C/D sums to {total}, and the junit's failed+errored is the same number.")
        if args.residue_json:
            pathlib.Path(args.residue_json).write_text(json.dumps(residue, indent=1))

    if args.json:
        pathlib.Path(args.json).write_text(json.dumps(rows, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
