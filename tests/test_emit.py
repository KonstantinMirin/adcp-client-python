"""Grade the committed emitted tree against the documents it was emitted from.

Every assertion here is over something DERIVED: the population comes from the
bundle, the pairs come from the emitter's own binding table, and the verdict
comes from the harness.  There is no expected class list, no snapshot and no
blessed value, so a test that passes cannot be passing because someone recorded
what the tree happened to hold (P10).

The bundle directory is a constant here and nowhere inside ``codegen/``: step 11
derives it from ``adcp.get_adcp_spec_version()`` (D9, P9).
"""

from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from codegen import adapter, bundle, emit
from codegen.harness import check_pair

REPO = Path(__file__).resolve().parents[1]
BUNDLE = REPO / "schemas" / "cache" / "3.2"
TREE = REPO / emit.TREE


def leaves() -> list[str]:
    """Step 1's population: an object root with no reference anywhere in it."""
    return [d for d in bundle.portable(BUNDLE) if bundle.is_leaf_object(bundle.read(BUNDLE, d))]


def referencing() -> list[str]:
    """Step 2's population: every reference is a property's own schema or its items."""
    return [
        d for d in bundle.portable(BUNDLE) if bundle.references_a_property(bundle.read(BUNDLE, d))
    ]


def population() -> list[str]:
    """What the committed tree is emitted from.  A reference TARGET is not here and
    does not need to be: ``emit`` walks ``$ref`` and emits the closure."""
    return sorted(set(leaves()) | set(referencing()))


def test_the_population_is_the_one_the_step_is_stated_over() -> None:
    """A verdict read off a population nobody counted is a verdict over however
    many documents there turned out to be, including none."""
    assert len(bundle.portable(BUNDLE)) == 1054
    assert len(leaves()) == 85
    assert len(referencing()) == 249
    assert len(population()) == 334
    assert "core/pagination-request.json" in leaves()
    assert "error-details/creative-revision-content-mismatch.json" in referencing()


def test_every_named_document_is_either_emitted_or_refused_by_name_and_keyword() -> None:
    out = emit.emit(BUNDLE, population())
    assert set(population()) <= set(out.bindings) | set(out.refusals)
    assert not set(out.bindings) & set(out.refusals)
    for document, row in out.refusals.items():
        assert row["keyword"] and row["pointer"], document


def test_a_reference_target_is_emitted_even_though_no_one_named_it() -> None:
    """Transitive emission, and that the walk terminates: the whole closure of a
    document's references is emitted, or the document is refused with the target
    that stopped it.  An import of a symbol from a module no run wrote is an
    ImportError, so there is no third outcome."""
    out = emit.emit(BUNDLE, population())
    pulled_in = set(out.bindings) - set(population())
    assert pulled_in, "no document was reached through a reference; the walk graded nothing"
    assert "core/creative-revision-id.json" in pulled_in
    # every reference of every emitted document resolves to a document also emitted
    known = set(bundle.portable(BUNDLE))
    for document in out.bindings:
        for _, uri in bundle.references(bundle.read(BUNDLE, document)):
            target = bundle.document_for(uri, known)
            assert target in out.bindings, (document, uri)


def test_pagination_request_is_graded_green_in_both_directions() -> None:
    """Step 1's own document, graded over EVERY constraint site it has."""
    pairs = {p.name: p for p in adapter.pairs(BUNDLE, TREE)}
    rep = check_pair(pairs["core/pagination-request.json"], max_steps=None)
    assert rep.missing_formats == []
    assert rep.accepts.outcome == "pass", (rep.accepts.detail, rep.accepts.counterexample)
    assert rep.step_sites == 3, rep.step_sites  # minimum, maximum, additionalProperties
    assert [r.outcome for r in rep.refuses] == ["pass"] * 3


def test_the_referencing_model_refuses_a_constraint_ANOTHER_document_declares() -> None:
    """Step 2's own control, over every constraint site it has.

    The sharp half of "both graded green" here: two of the six sites --
    ``minLength`` and ``maxLength`` at ``/properties/revision_id`` -- are declared
    by ``core/creative-revision-id.json`` and by nothing in this document, and the
    referencing model refuses a violation of each.  The constraint arrives through
    the import; there is nowhere else it could have come from.

    This does NOT grade P2, and the pair of tests is deliberate: a COPY of the
    target's constraints also refuses, so this one passes while
    ``..._is_an_import_and_not_a_copy`` fails -- probed, by emitting the copy.
    """
    control = "error-details/creative-revision-content-mismatch.json"
    pair = next(p for p in adapter.pairs(BUNDLE, TREE) if p.name == control)
    target = bundle.read(BUNDLE, "core/creative-revision-id.json")
    theirs = set(target) & set(emit.CONSTRAINTS)
    ours = {
        k
        for _, node in bundle.nodes(bundle.read(BUNDLE, control))
        if "$ref" not in node
        for k in node
        if k in emit.CONSTRAINTS
    }
    assert theirs - ours, "the target declares no constraint this document does not"

    rep = check_pair(pair, max_steps=None)
    assert rep.missing_formats == []
    assert rep.accepts.outcome == "pass", (rep.accepts.detail, rep.accepts.counterexample)
    assert [r.outcome for r in rep.refuses] == ["pass"] * rep.step_sites
    assert {r.keyword for r in rep.refuses if r.pointer == "/properties/revision_id"} == theirs


@pytest.mark.parametrize("document", sorted(adapter.bindings(TREE)))
def test_every_binding_is_graded_green_in_both_directions(document: str) -> None:
    """N: emitted AND graded green against the EMITTING document, both ways."""
    pair = next(p for p in adapter.pairs(BUNDLE, TREE) if p.name == document)
    rep = check_pair(pair, max_steps=None)
    assert rep.missing_formats == []
    assert rep.accepts.outcome == "pass", (rep.accepts.detail, rep.accepts.counterexample)
    bad = [(r.keyword, r.pointer, r.outcome, r.counterexample, r.harness) for r in rep.refuses]
    assert [b for b in bad if b[2] not in ("pass", "no_evidence")] == []


def test_a_reference_cycle_refuses_rather_than_recurring(tmp_path) -> None:
    """The walk terminates, graded on a bundle built so that it would not.

    The 3.2 bundle's reference graph is acyclic -- a three-colour DFS over its
    3,094 document-to-document edges finds 0 cycles -- so this branch is
    unreachable from it, which is exactly why it gets a bundle of its own instead
    of a comment saying it cannot happen.  Two modules importing each other's
    symbol at module scope is an ImportError, not a type, so a cycle has to refuse
    before it is written.
    """
    ref = "https://example.org/whatever/{}.json"
    for name, other in (("a", "b"), ("b", "a")):
        (tmp_path / f"{name}.json").write_text(
            json.dumps(
                {
                    "title": name.upper(),
                    "type": "object",
                    "required": [other],
                    "properties": {other: {"$ref": ref.format(other)}},
                }
            )
        )
    out = emit.emit(tmp_path, ["a.json", "b.json"])
    assert out.bindings == {}
    assert sorted(out.refusals) == ["a.json", "b.json"]
    for document, row in out.refusals.items():
        assert row["keyword"] == "$ref", (document, row)
        assert "cycle" in row["detail"], (document, row)


def _source(document: str) -> str:
    return (TREE / f"{emit.module_path(document)}.py").read_text()


def test_a_cross_document_reference_is_an_import_and_not_a_copy() -> None:
    """P2, on the AST of the emitted module rather than on its text.

    The previous attempt's whole premise was that three generators all flatten a
    ``$ref`` into a COPY of its target, so "it emits an import" is the claim this
    step has to make falsifiable.  Two halves, because either alone passes while
    the other fails:

      * the referencing field's annotation NAMES the target's symbol and contains
        no call -- a copy of the target's constraints is a ``Field(...)`` call,
        and a copy that replaced the reference does not name the symbol at all;
      * no ``Field`` kwarg ANYWHERE in the module is one this document does not
        declare locally -- so a constraint of the target has nowhere else in the
        module to hide either.

    Deliberately says nothing about HOW an optional property is wrapped.  That is
    D4's, it has been re-decided once already (a per-field null-refusing alias,
    then plain ``T | None`` with the schema as the gate), and a test naming the wrapper's
    spelling would have to be edited by the lane that changes it -- which is how a
    P2 instrument comes to be adjusted by someone who is not grading P2.  Both
    renderings satisfy what is asserted here, and so does any third.

    Everything compared is derived: the import module from ``relative_module``,
    the symbol from the emitter's own binding table, the local constraint set from
    the document's non-reference nodes.
    """
    known = set(bundle.portable(BUNDLE))
    table = adapter.bindings(TREE)
    graded = 0
    for document in sorted(table):
        doc = bundle.read(BUNDLE, document)
        refd = {
            key: sub["$ref"]
            for key, sub in doc.get("properties", {}).items()
            if isinstance(sub, dict) and "$ref" in sub
        }
        if not refd:
            continue
        tree = ast.parse(_source(document))
        imported = {
            ("." * n.level + (n.module or ""), a.name)
            for n in ast.walk(tree)
            if isinstance(n, ast.ImportFrom)
            for a in n.names
        }
        symbol_of = table[document]["symbol"]
        root = next(c for c in tree.body if isinstance(c, ast.ClassDef) and c.name == symbol_of)
        annotated = {
            t.target.id: t.annotation
            for t in root.body
            if isinstance(t, ast.AnnAssign) and isinstance(t.target, ast.Name)
        }
        for key, uri in sorted(refd.items()):
            target = bundle.document_for(uri, known)
            symbol = table[str(target)]["symbol"]
            module = emit.relative_module(document, str(target))
            assert (module, symbol) in imported, (document, key, module, symbol)
            got = annotated[emit.field_name(key)]
            named = {n.id for n in ast.walk(got) if isinstance(n, ast.Name)}
            assert symbol in named, (document, key, ast.unparse(got))
            calls = [ast.unparse(n) for n in ast.walk(got) if isinstance(n, ast.Call)]
            assert calls == [], (document, key, ast.unparse(got), calls)
            graded += 1
        local = {
            emit.CONSTRAINTS[k]
            for _, node in bundle.nodes(doc)
            if "$ref" not in node
            for k in node
            if k in emit.CONSTRAINTS
        }
        used = {
            kw.arg
            for n in ast.walk(tree)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "Field"
            for kw in n.keywords
        }
        assert used <= local | {"alias", "default"}, (document, sorted(used - local))
    assert graded, "no referencing property was graded"


def test_a_scalar_root_emits_an_annotated_alias_and_not_a_class() -> None:
    """D2's root-scalar row: a node with no field to hang itself on is an alias.

    A wrapper class would be a second name for the same node (P2), and every
    referencing model would then carry an object where the document carries a
    string.
    """
    table = adapter.bindings(TREE)
    graded = 0
    for document in sorted(table):
        if bundle.read(BUNDLE, document).get("type") not in emit.SCALAR:
            continue
        tree = ast.parse(_source(document))
        assigned = {
            t.id
            for n in tree.body
            if isinstance(n, ast.Assign)
            for t in n.targets
            if isinstance(t, ast.Name)
        }
        assert table[document]["symbol"] in assigned, document
        assert [n for n in tree.body if isinstance(n, ast.ClassDef)] == [], document
        graded += 1
    assert graded, "no scalar root was graded"

    control = "core/creative-revision-id.json"
    doc = bundle.read(BUNDLE, control)
    alias = next(
        n
        for n in ast.parse(_source(control)).body
        if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == table[control]["symbol"]
    )
    want = f"Annotated[str, Field(min_length={doc['minLength']}, max_length={doc['maxLength']})]"
    assert ast.unparse(alias.value) == want


def test_the_committed_tree_is_what_a_fresh_run_emits(tmp_path) -> None:
    """P10, and D8's byte compare: the tree equals f(bundle, emitter), so a
    defect is fixed in the emitter and nothing rewrites the output."""
    out = emit.emit(BUNDLE, population())
    emit.write(out, tmp_path)

    def tree(root: Path) -> dict[str, str]:
        return {
            str(p.relative_to(root)): p.read_text()
            for p in root.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts
        }

    committed, fresh = tree(TREE), tree(tmp_path)
    assert sorted(fresh) == sorted(committed)
    for rel in sorted(fresh):
        assert fresh[rel] == committed[rel], rel


def test_the_output_is_a_function_of_its_inputs_and_of_nothing_else() -> None:
    """P7: determinism is a precondition of grading, not a fix.

    Argument order is NOT what this grades, and a test that compared a forward
    run with a reversed one was kept here until it was probed: ``emit`` sorts its
    documents, so no permutation of its arguments can change the output and the
    comparison could not fail.  P7 holds for order by construction.

    What CAN vary between runs is set iteration -- the import lines come out of a
    ``set[tuple[str, str]]`` -- and that varies by hash seed, not by anything a
    caller passes.  So the two runs are two processes with different
    ``PYTHONHASHSEED`` values, which is the perturbation this property has.
    """
    cmd = [sys.executable, "-m", "codegen.emit", "--bundle", str(BUNDLE), "--tree"]
    outs = []
    for seed in ("0", "12345"):
        into = Path(tempfile.mkdtemp())
        env = {**os.environ, "PYTHONHASHSEED": seed, "PYTHONPATH": str(REPO)}
        subprocess.run(
            [*cmd, str(into), *population()], check=False, cwd=REPO, env=env, capture_output=True
        )
        outs.append({str(p.relative_to(into)): p.read_text() for p in sorted(into.rglob("*.py"))})
        shutil.rmtree(into)
    assert outs[0] and outs[0] == outs[1]


def test_the_adapter_refuses_a_module_from_a_tree_it_was_not_pointed_at(tmp_path) -> None:
    """The guard that makes N mean anything, exercised rather than asserted: a
    harness pointed at a tree this run did not emit grades another generator's
    output and reports it as this one's."""
    table = {"core/pagination-request.json": adapter.bindings(TREE)["core/pagination-request.json"]}
    (tmp_path / "_bindings.json").write_text(json.dumps(table))
    with pytest.raises(AssertionError, match="outside the emitted tree"):
        adapter.pairs(BUNDLE, tmp_path)
