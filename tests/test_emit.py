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
from pydantic import ValidationError

from codegen import adapter, bundle, emit
from codegen.harness import check_pair

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


def test_strict_validate_decides_acceptance_against_the_document() -> None:
    """D4, in the place step 1's 52-property nullability instrument used to sit.

    That instrument asserted the MODEL refuses an explicit null at every optional
    non-nullable property, and it had to be per-property because the RENDERING
    was: each annotation carried its own validator, so a missing wrap on one
    property was invisible.  The rendering is now plain ``T | None = None`` and
    the refusal is one function reading the document, so the 52 sites collapse to
    one mechanism and asserting it 52 times would be asserting it with 52 inputs.

    What nothing else in this file reaches: that the schema half of
    ``strict_validate`` runs at all, and that the keyword it refuses on is the
    DOCUMENT'S name for it.  ``check_pair`` cannot grade either -- ``steps()`` has
    no nullability step, and a model graded through ``strict_validate`` refuses
    whatever the control already says the document refuses.  Measured: with the
    schema check deleted from ``strict_validate``, this is the only test in the
    suite that goes red.
    """
    model = {p.name: p for p in adapter.pairs(BUNDLE, TREE)}["core/pagination-request.json"].model

    with pytest.raises(ValidationError) as caught:
        model.strict_validate({"cursor": None})
    assert [(e["type"], e["loc"]) for e in caught.value.errors()] == [("type", ("cursor",))]

    # ``minimum: 1`` is in the annotation too, as ``Field(ge=1)``, so the second
    # half is the keyword MAPPING: pydantic's own name for it is
    # ``greater_than_equal`` and the document's is ``minimum``.
    with pytest.raises(ValidationError) as caught:
        model.strict_validate({"max_results": 0})
    assert [(e["type"], e["loc"]) for e in caught.value.errors()] == [("minimum", ("max_results",))]


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
