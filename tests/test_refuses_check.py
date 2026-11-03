"""**Every value the document REFUSES, offered TO THE CLASS, which must refuse it.**

``docs/plan/final-state.md`` reading 1 is the sentence this file is about:

    Every class accepts every value its document admits, **refuses every value its
    document refuses**, and what it dumps validates against that document again.

``harness.check_accepts`` is the first half.  ``adcp-client-python-6oe`` is what the
absence of the second half cost: ``core/positive-postal-area-support.json`` refuses ``{}``
-- ``minProperties: 1`` in an ``allOf`` conjunct -- and
``PositivePostalAreaSupport.model_validate({})`` built one with ``__adcp_approximations__``
empty, a P0 in the shipped artifact that nothing reported for as long as it existed.

**AND ONE FORM OF THIS CHECK IS A MEASURED DEAD END.  IT IS NOT THE FORM BUILT HERE, AND
THE DIFFERENCE IS THE WHOLE DESIGN.**  ``codegen/harness.py``'s module docstring records
the refutation, under *"WHAT THIS MODULE USED TO DO AND NO LONGER DOES"*:

    The refuses check mutated ONE KEYWORD at a time, drew an instance the mutated schema
    accepts, and passed it to the caller's ``accept`` -- **which validates against THE
    DOCUMENT before constructing.**  So a step site asserted that ``jsonschema`` rejects a
    payload violating the schema it was handed, and **the generated class took no part in
    the outcome**: on ``core/pagination-request.json`` a model with ``Any`` on every field
    accepted, refused 75 of 75 instances and recorded no wrong acceptance, exactly as a
    faithful one did.  27,791 of those sites over the graded population were the suite's
    entire wall clock, spent on a property of a third-party validator.

So that instrument was deleted correctly and ``check_liveness`` is what survives it -- ONE
payload through ``strict_validate``, proving the schema half is CONNECTED, and its own
docstring forbids reading the answer as a measurement of the class.  **The ``refuses N/0``
figure the pair reports is liveness and has never been a refuses-check on the class.**

**THREE THINGS KEEP THIS FILE OUT OF THAT TRAP, and each is gated below rather than
asserted here:**

1. **The value is offered to the CLASS and to nothing else.**  ``check_refuses`` takes a
   ``construct`` callable and the production caller passes ``model_validate``, never
   ``pair.accept``.  No document-side gate runs between the witness and the class, so the
   class is the only thing that can produce the verdict.
2. **THE REFUTATION IS THE GATE.**
   :func:`test_a_model_with_any_on_every_field_fails_this_check` is the discarded
   instrument's own counterexample, run against this one: a model with ``Any`` on every
   field must FAIL.  If it ever passes, this has been rebuilt as the thing that measured
   ``jsonschema``, and the gate says so by name.
3. **Nothing is drawn and nothing is mutated.**  The witness is derived from the
   UNMODIFIED document by taking each keyword's boundary on the far side, and every
   candidate is screened by ``conforms(document, candidate) is False`` before it is
   offered -- so the document refuses it as the document is written, not as a mutation
   left it.  The cost is one ``conforms`` per keyword: ``hypothesis_jsonschema.from_schema``
   is never called, and that function is 151.24 s of a 151.51 s accepts pair
   (``tests/corpus.py``'s own table).

**WHY A PER-PAIR FORM IS KEPT BESIDE THE CELL FORM, on the measurement.**  The owner left
the choice open and the numbers answer it both ways, so both are kept and each says what
the other cannot:

* the CELL form (``tests/cells.py``'s ``grade``, which reads both of §2's directions) is
  COMPLETE over §5's 289 live cells and costs seconds, because a cell's cost is a function
  of the keyword and not of any document -- it reaches the 86 documents no draw finishes.
  What it cannot say is whether the WALK applied that cell at a real document's node,
  which is premise 3 of §8's induction.
* this file is the artifact, and it is affordable for the reason above: 15 pairs, no draw,
  one accepted instance each derived from the document's own ``const``/``enum``
  declarations.  It found nothing the cell form did not -- it CONFIRMS ``6oe`` at the
  document the P0 was measured on, which is the one thing a cell cannot do.

**WHAT IS NOT HERE.**  The sweep over the whole graded population, and the obstruction is
the INSTANCE rather than the check: over that population the accepted instance is
``check_accepts``' draw, held under a key whose computation needs the pair, so wiring it
means building 1,628 pairs -- ``tests/test_emit.py::graded_reports``, measured at "2h21m of
CPU at 20.3 GB" without completing (``adcp-client-python-82m.37``).  The per-pair check
costs one ``conforms`` per keyword inside that reader when it runs; until then the cell
form carries the completeness and the 15 pairs below carry the artifact.
"""

from __future__ import annotations

import importlib
import json
from functools import cache
from pathlib import Path
from typing import Annotated, Any

import fresh
import pytest
from compiled import compiled
from nodeset import claimed
from pydantic import BaseModel, StringConstraints, TypeAdapter

from codegen import bundle, harness
from codegen.harness import check_refuses, own_facts, refused_witnesses

REPO = Path(__file__).resolve().parents[1]
BUNDLE = REPO / "schemas" / "cache" / "3.2"

#: The two keywords ``adcp-client-python-6oe`` is about: a property COUNT, which §5 lowers
#: to a ``PropertyCount`` rule over the keys the class RETAINED, and which the
#: document-side VALUE fold does not carry from a conjunct to the composed root.
COUNTS = ("minProperties", "maxProperties")

#: A bounded string, as the emitter writes it.  Built here rather than imported from the
#: tree so the INSTRUMENT's own gates do not depend on which documents happen to emit.
Bounded3 = Annotated[str, StringConstraints(max_length=3)]


# --------------------------------------------------------------------------- #
# the refutation: the discarded instrument's own counterexample, run against this one
# --------------------------------------------------------------------------- #
class AnyOnEveryField(BaseModel):
    """The model the deleted refuses-check could not tell from a faithful one.

    ``codegen/harness.py``'s refutation: "on ``core/pagination-request.json`` a model with
    ``Any`` on every field accepted, refused 75 of 75 instances and recorded no wrong
    acceptance, exactly as a faithful one did."  It is a BaseModel with ``extra="allow"``
    and no constraint anywhere, so it builds every object there is.
    """

    model_config = {"extra": "allow"}

    limit: Any = None
    cursor: Any = None


def test_a_model_with_any_on_every_field_fails_this_check() -> None:
    """**THE GATE THAT SAYS THIS IS NOT THE DISCARDED INSTRUMENT.**

    The deleted check routed its payload through ``accept``, which validates against the
    document first, so the document's own refusal was the whole outcome and a model with
    ``Any`` on every field scored exactly as a faithful one did.  This check offers the
    payload to ``model_validate``, so the class is the only thing that can answer -- and
    the proof of that is that the same model now FAILS, by value and by keyword.

    A document with a bound on every field it declares, and a class that carries none of
    them: every witness the reduction derives is a value the document refuses and the
    model builds.
    """
    schema = {
        "type": "object",
        "properties": {
            "limit": {"type": "integer", "minimum": 1, "maximum": 100},
            "cursor": {"type": "string", "maxLength": 8},
        },
        "required": ["limit"],
        "minProperties": 2,
    }
    result = check_refuses(schema, AnyOnEveryField.model_validate, {"limit": 1, "cursor": "a"})
    assert result.outcome == "widened_undeclared", result
    # The class took part: every witness it admitted is named, with the keyword the
    # document refused it on.
    assert result.undeclared, result
    assert {row[1] for row in result.undeclared} >= {"required", "minProperties"}, result


def test_the_same_document_passes_for_a_class_that_carries_the_facts() -> None:
    """The other side of the refutation, and it has to be here or the gate above is vacuous.

    A check that failed EVERY class would also fail a model with ``Any`` on every field,
    so the pair of tests is what says the verdict is a function of the class.  This model
    declares the same facts the document states, so every witness is refused.
    """

    class Faithful(BaseModel):
        model_config = {"extra": "forbid"}

        limit: Annotated[int, None] | int
        cursor: Bounded3 | None = None

    schema = {
        "type": "object",
        "properties": {
            "limit": {"type": "integer"},
            "cursor": {"type": "string", "maxLength": 3},
        },
        "required": ["limit"],
        "additionalProperties": False,
    }
    result = check_refuses(schema, Faithful.model_validate, {"limit": 1, "cursor": "abc"})
    assert result.rows, "the witnesses do not discriminate"
    assert result.outcome == "pass", result


# --------------------------------------------------------------------------- #
# the instrument, in the directions §2 reads a disagreement in
# --------------------------------------------------------------------------- #
def test_a_class_wider_than_its_document_fails_and_names_the_value() -> None:
    """The half ``check_accepts`` structurally cannot reach.

    A bare ``str`` against a document that bounds its length: the document refuses
    ``"abcd"`` and the class builds it, and the row carries the value AND the keywords the
    DOCUMENT refused it on -- asked of the document rather than assumed from the
    perturbation, which is ``violated_keywords``' own reason.
    """
    schema = {"type": "string", "maxLength": 3}
    result = check_refuses(schema, TypeAdapter(str).validate_python, "abc")
    assert result.outcome == "widened_undeclared", result
    row = next(r for r in result.undeclared if r[1] == "maxLength")
    # EXACTLY one character past the bound: §8's witness is "both sides of each bound and
    # the bound itself", so a reader of the failure sees which boundary was crossed.
    assert len(json.loads(row[0])) > len("abc")
    assert len(json.loads(row[0])) < len("abcd") + 1
    assert "maxLength" in row[2]
    # The same document and a class that carries the bound: every witness is refused.
    assert check_refuses(schema, TypeAdapter(Bounded3).validate_python, "abc").outcome == "pass"


def test_a_widening_passes_exactly_where_the_run_declares_one() -> None:
    """§2's rule read as a check, in both directions.

    A declaration that excused every keyword would be the allowlist §2's declared set
    exists not to be, so the keyword is compared: a declaration naming ``maxLength``
    passes the pair and one naming ``minLength`` does not.
    """
    schema = {"type": "string", "maxLength": 3}
    accept = TypeAdapter(str).validate_python
    assert check_refuses(schema, accept, "abc", declared=("maxLength",)).outcome == "pass"
    assert (
        check_refuses(schema, accept, "abc", declared=("minLength",)).outcome
        == "widened_undeclared"
    )


def test_a_document_that_refuses_nothing_this_reduction_builds_is_not_graded() -> None:
    """``no_witness`` is its own answer and not a pass smuggled through.

    The empty schema admits every instance there is, so there is nothing for a class to
    refuse.  Reporting ``pass`` would make a pair that offered NOTHING read identically to
    one that offered everything and was right, which is the shape §8 deleted an instrument
    for.
    """
    result = check_refuses({}, TypeAdapter(object).validate_python, {"a": 1})
    assert result.outcome == "no_witness"
    assert result.rows == ()


def test_a_conjuncts_keyword_is_a_witness_source_and_the_value_fold_does_not_carry_it() -> None:
    """``harness.own_facts`` and not ``_composed``, and ``6oe`` is why.

    ``FOLDED_FACTS`` is ``keywords.rendered_at(ROOT)`` and carries no property count, so
    the document-side VALUE fold does not bring ``minProperties`` from a conjunct to the
    composed root -- asserted, because the witness that found the P0 is derived from that
    keyword and from no other.  :func:`own_facts` asks the other question: which keywords
    are there to take a boundary FROM.
    """
    assert "minProperties" not in harness.FOLDED_FACTS
    composed = {
        "type": "object",
        "allOf": [{"minProperties": 1}, {"properties": {"a": {"const": True}}}],
    }
    assert own_facts(composed)["minProperties"] == 1
    witnesses = refused_witnesses(composed, {"a": True})
    assert any(keyword == "minProperties" for _, keyword, _ in witnesses), witnesses
    assert any(candidate == {} for candidate, _, _ in witnesses), witnesses


# --------------------------------------------------------------------------- #
# the artifact: the pairs whose composed root states a property count
# --------------------------------------------------------------------------- #
@cache
def counting_roots() -> dict[str, dict]:
    """Every portable document whose COMPOSED ROOT states a property count, with its node.

    Derived over the bundle through ``harness.own_facts`` -- the same fold the witness
    builder reads -- so the set is the bundle's answer and a document that grows a count
    joins it without being told.  The node is the document OF RECORD, which is the schema
    a class's own ``strict_validate`` answers from (D4).
    """
    known = set(bundle.portable(BUNDLE))
    out: dict[str, dict] = {}
    for document in sorted(known):
        node = bundle.record(BUNDLE, document, known)
        if not isinstance(node, dict):
            continue
        if any(keyword in own_facts(node) for keyword in COUNTS):
            out[document] = node
    return out


def an_instance_the_document_admits(node: dict) -> dict | None:
    """One instance for the reduction to perturb, built from the node's own declarations.

    **Not a draw**, which is this check's whole cost argument: an object root whose
    properties pin a ``const`` or an ``enum`` is satisfied by the object carrying one
    pinned value per key, and a count's witness is derived by REMOVING keys from it.  A
    node this cannot satisfy is skipped by name rather than graded against a guess -- and
    the instance is offered to the DOCUMENT before anything else reads it, so a wrong one
    skips the pair instead of producing a verdict.
    """
    built: dict[str, Any] = {}
    for key, pinned in _pins(node, node).items():
        built[key] = pinned
    return built or None


def _pins(view: Any, root: dict, depth: int = 0) -> dict[str, Any]:
    """Each property key some VIEW of this node pins to a value, with that value.

    **One view per ``allOf`` member and the key is NOT won by the first of them**, which is
    a measured skip of this gate rather than a refinement:
    ``core/positive-postal-area-support.json`` declares ``us_zip`` twice -- the inlined
    base types it ``boolean`` and the conjunct pins it ``const: true`` -- so a reader that
    took one view's declaration for the key found no pin at all, no instance was derivable,
    and the pair ``adcp-client-python-6oe`` was measured on SKIPPED while fourteen others
    reported green.  Later views fill a key no earlier view PINNED, which is what makes the
    pin the thing being searched for rather than the declaration.

    A bare local pointer is read as the node it names, because §4 leaves a local ``$ref``
    exactly as the document writes it AND ``bundle.record``'s own sharing writes one: both
    of that document's declarations arrive as ``{"$ref": "#/definitions/Shared<N>"}``.  The
    hop goes through ``bundle.node_at`` and nowhere else -- "two readings of RFC 6901's two
    escapes is how an inliner and a grader come to disagree about which node a reference
    names".  A pointer naming nothing contributes no pin, which is the fail-safe direction:
    the pair skips by name rather than being graded against a guess.
    """
    if not isinstance(view, dict) or depth > 8:
        return {}
    out: dict[str, Any] = {}
    for key, declaration in (view.get("properties") or {}).items():
        resolved = _locally(declaration, root)
        if "const" in resolved:
            out[key] = resolved["const"]
        elif isinstance(resolved.get("enum"), list) and resolved["enum"]:
            out[key] = resolved["enum"][0]
    for conjunct in view.get("allOf") or ():
        for key, value in _pins(_locally(conjunct, root), root, depth + 1).items():
            out.setdefault(key, value)
    return out


def _locally(declaration: Any, root: dict) -> dict:
    """``declaration`` with a bare local pointer resolved against ``root``."""
    if not isinstance(declaration, dict):
        return {}
    ref = declaration.get("$ref")
    if set(declaration) != {"$ref"} or not isinstance(ref, str) or not ref.startswith("#"):
        return declaration
    try:
        target = bundle.node_at(root, ref[1:])
    except (KeyError, IndexError, TypeError, ValueError):
        return declaration
    return target if isinstance(target, dict) else declaration


@pytest.mark.parametrize("document", sorted(counting_roots()))
def test_every_counting_root_refuses_the_count_its_document_refuses(document: str) -> None:
    """**The gate ``adcp-client-python-6oe`` earns**, over the derived set and not one pair.

    The class is read off the tree a FRESH run emits (``tests/fresh.py``'s rule: "grading
    reads the tree a fresh run emits; the committed tree is an ARTIFACT, verified by one
    byte-compare"), and its declarations are read off it the way a consumer reads any class
    attribute -- ``harness.declarations_of``, which §9 requires of the verifier.

    **Red at ``5021772c`` on ``core/positive-postal-area-support.json``**: the document
    refuses ``{}``, the class built one, and nothing was declared.
    """
    assert fresh.schemas() is not None, fresh.FAILURE
    node = counting_roots()[document]
    instance = an_instance_the_document_admits(node)
    if instance is None:
        pytest.skip(f"no instance derivable from {document}'s own declarations")
    if harness.conforms(node, instance) is not True:
        pytest.skip(f"the derived instance is not one {document} admits")
    symbol = _root_of(document)
    if symbol is None:
        pytest.skip(f"{document} emits no root class")
    result = check_refuses(
        node,
        TypeAdapter(symbol).validate_python,
        instance,
        declared=tuple(one.keyword for one in harness.declarations_of(symbol)),
    )
    assert result.outcome in ("pass", "no_witness"), (document, result)


@cache
def _root_of(document: str) -> Any:
    """The ROOT symbol of a document's FRESH module, or ``None`` where it declares none.

    Read off the module's ``__all__``, which is the emitter's own export record, so no name
    is derived here and a renamed class cannot make this skip silently.
    """
    out = compiled(BUNDLE, sorted(bundle.portable(BUNDLE)))
    #: ``Emitted.emitted`` maps a document to the MODULE NAME the run wrote it to, which
    #: is the dotted name a consumer imports -- so nothing here spells a path.
    name = out.emitted.get(document)
    if name is None:
        return None
    module = importlib.import_module(name)
    exported = getattr(module, "__all__", ())
    return getattr(module, exported[0], None) if exported else None


def test_the_counting_population_is_named_and_derived() -> None:
    """The denominator the gate above ranges over, NAMED rather than counted.

    ``nodeset.claimed`` so a document leaving the set reddens with the document named,
    where an integer would say only that a number moved.  15 of the bundle's 1,015 distinct
    documents state a property count at a composed root -- ``bundle.portable`` returns
    1,054 PATHS over 1,015 documents, 39 of them byte-identical duplicates under
    ``core/async-response-refs/``, and this set holds none of the duplicates.
    """
    population = claimed("portable roots stating a property count", set(counting_roots()))
    assert "core/positive-postal-area-support.json" in population
    assert not any(d.startswith("core/async-response-refs/") for d in population)


def test_the_document_the_p0_was_measured_on_is_GRADED_and_never_skipped() -> None:
    """**The one document ``6oe`` names reaches a verdict, and that is its own gate.**

    ``docs/plan/final-state.md``: "a scope that omits the code the check is about" is one
    of the three forms of the same evasion, and a parametrised gate that SKIPS the pair it
    exists for is exactly that -- it reports green over fourteen other documents while the
    P0's own pair is unrun.  It skipped once, measured: ``harness.own_facts`` gap-filled
    ``properties`` instead of merging by key, so the inlined base won the key map and no
    instance was derivable from the document's own declarations.
    """
    document = "core/positive-postal-area-support.json"
    node = counting_roots()[document]
    instance = an_instance_the_document_admits(node)
    assert instance, "no instance derivable -- the gate for 6oe would skip"
    assert harness.conforms(node, instance) is True, instance
    witnesses = refused_witnesses(node, instance)
    # ``{}`` is THE witness: the document's conjunct states ``minProperties: 1`` and the
    # empty object is the far side of it, which is the value a fresh run's class built
    # at ``5021772c`` with nothing declared.
    assert any(candidate == {} for candidate, _, _ in witnesses), witnesses
    assert fresh.schemas() is not None, fresh.FAILURE
    symbol = _root_of(document)
    assert symbol is not None
    result = check_refuses(
        node,
        TypeAdapter(symbol).validate_python,
        instance,
        declared=tuple(one.keyword for one in harness.declarations_of(symbol)),
    )
    assert result.outcome == "pass", result
