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

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from pydantic import TypeAdapter, ValidationError

from codegen import adapter, bundle, emit
from codegen.harness import check_pair, violated_keywords

REPO = Path(__file__).resolve().parents[1]
BUNDLE = REPO / "schemas" / "cache" / "3.2"
TREE = REPO / emit.TREE


def leaves() -> list[str]:
    return [d for d in bundle.portable(BUNDLE) if bundle.is_leaf_object(bundle.read(BUNDLE, d))]


def test_the_population_is_the_one_the_step_is_stated_over() -> None:
    """A verdict read off a population nobody counted is a verdict over however
    many documents there turned out to be, including none."""
    assert len(bundle.portable(BUNDLE)) == 1054
    assert len(leaves()) == 85
    assert "core/pagination-request.json" in leaves()


def test_every_leaf_is_either_emitted_or_refused_by_name_and_keyword() -> None:
    out = emit.emit(BUNDLE, leaves())
    assert len(out.bindings) + len(out.refusals) == 85
    assert set(out.bindings) | set(out.refusals) == set(leaves())
    for document, row in out.refusals.items():
        assert row["keyword"] and row["pointer"], document


def test_pagination_request_is_graded_green_in_both_directions() -> None:
    """Step 1's own document, graded over EVERY constraint site it has."""
    pairs = {p.name: p for p in adapter.pairs(BUNDLE, TREE)}
    rep = check_pair(pairs["core/pagination-request.json"], max_steps=None)
    assert rep.missing_formats == []
    assert rep.accepts.outcome == "pass", (rep.accepts.detail, rep.accepts.counterexample)
    assert rep.step_sites == 3, rep.step_sites  # minimum, maximum, additionalProperties
    assert [r.outcome for r in rep.refuses] == ["pass"] * 3


@pytest.mark.parametrize("document", sorted(adapter.bindings(TREE)))
def test_every_binding_is_graded_green_in_both_directions(document: str) -> None:
    """N: emitted AND graded green against the EMITTING document, both ways."""
    pair = next(p for p in adapter.pairs(BUNDLE, TREE) if p.name == document)
    rep = check_pair(pair, max_steps=None)
    assert rep.missing_formats == []
    assert rep.accepts.outcome == "pass", (rep.accepts.detail, rep.accepts.counterexample)
    bad = [(r.keyword, r.pointer, r.outcome, r.counterexample, r.harness) for r in rep.refuses]
    assert [b for b in bad if b[2] not in ("pass", "no_evidence")] == []


def test_an_optional_property_is_absent_or_valid_never_null() -> None:
    """D4 and P12, which ``check_pair`` does not reach.

    ``steps()`` has no nullability step -- it rewrites a constraint keyword, and
    "an optional property accepts an explicit null" is a widening of ``type``,
    not of a constraint.  So a model rendering ``str | None = None`` for a
    property declared ``{"type": "string"}`` is wider than its document and the
    harness reports it green.  This is the instrument for that half, and it is
    derived from the document the same way: the property set comes from the
    schema, the control is that the document refuses the null ON ``type``, and
    the obligation is that the model refuses it AT that property.
    """
    graded = 0
    for pair in adapter.pairs(BUNDLE, TREE):
        required = pair.schema.get("required", [])
        for key, sub in pair.schema["properties"].items():
            kind = sub.get("type")
            if key in required or kind is None or kind == "null" or isinstance(kind, list):
                continue  # required, or a schema that ADMITS the null (D4's other arm)
            instance = {key: None}
            assert "type" in violated_keywords(pair.schema, instance), (pair.name, key)
            with pytest.raises(ValidationError) as caught:
                TypeAdapter(pair.model).validate_python(instance)
            locs = [e["loc"] for e in caught.value.errors()]
            assert (key,) in locs, (pair.name, key, locs)
            graded += 1
    # Non-empty, and no hand-written floor: a floor records what the bundle held
    # the day it was typed, so it detects change rather than wrongness (P10).
    assert graded, "no optional non-nullable property was graded"


def test_the_committed_tree_is_what_a_fresh_run_emits(tmp_path) -> None:
    """P10, and D8's byte compare: the tree equals f(bundle, emitter), so a
    defect is fixed in the emitter and nothing rewrites the output."""
    out = emit.emit(BUNDLE, leaves())
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
            [*cmd, str(into), *leaves()], check=False, cwd=REPO, env=env, capture_output=True
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
