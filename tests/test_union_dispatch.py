"""§4's FIRST dispatch source, and the one thing a consumer of a union root meets.

``docs/plan/final-state.md`` reading 3: "A payload offered to a union base resolves to
its branch, for every payload the document admits.  The dispatch key is one that
**determines** the branch, which requires the document to guarantee its presence in
every instance it admits -- pinning a key is not determining it.  **Decided by**
constructing every union base's dispatch over the whole tree and requiring that none
raises, plus: no union dispatches on a key its document lets an instance omit."

Both halves are here, and the first is the one that catches a root a consumer cannot use
at all: ``Field(discriminator=<key>)`` over an ``Optional[Literal[...]]`` is refused by
pydantic when the ADAPTER IS BUILT, not when a payload arrives, so every
``model_validate`` on such a root raises ``PydanticUserError`` before validating
anything.  ``media-buy/refine-proposals-response.json`` was one
(``adcp-client-python-82m.23``), and nothing else in this suite saw it: the module
imports, every branch class validates, and ``./check`` counts the document as emitted
and unrefused.  Only a draw through the ROOT meets it.

**NEITHER HALF ASSERTS CODE SHAPE.**  The first constructs the dispatch and requires no
exception; the second reads the document and compares it with the key the class carries.
``_BRANCH_DISCRIMINATOR`` is read because it IS the ``Field(discriminator=)`` the base
installs (``BranchDispatchMixin._branch_adapter``) and there is nothing else at runtime
that names the key.

**THE DOCUMENT SIDE IS THE DOCUMENT OF RECORD** (``bundle.record``, §9), so a branch
that is a bare ``$ref`` has its target's ``required`` where the branch sits and this file
resolves nothing of its own.

The payload rows for ``adcp-client-python-82m.23`` and ``.24`` are at the end.  Each is a
claim about an ACCEPTED SET, so ``jsonschema`` states it first and the class is then
asked to agree -- a class wider than its document is what both rows were.
"""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from typing import Any

import jsonschema
import pytest
from pydantic import BaseModel, ValidationError

import adcp.types._schemas as schemas_pkg
from adcp.types._base import BranchDispatchMixin, through_the_store
from codegen import bundle
from tests.nodeset import claimed

REPO = Path(__file__).resolve().parents[1]
BUNDLE = REPO / "schemas" / "cache" / "3.2"
#: The two union keywords, in the order §5 reads them.  A node states at most one of
#: them: the bundle holds 0 nodes stating both, and ``lower_union.keyword`` refuses one.
UNION = ("oneOf", "anyOf")


def _records() -> dict[str, dict]:
    """Every portable document as its document of record, read once."""
    known = set(bundle.portable(BUNDLE))
    out = {}
    for document in sorted(known):
        got = bundle.record(BUNDLE, document, known)
        if isinstance(got, dict):
            out[document] = got
    return out


def _at(root: Any, pointer: str) -> Any:
    """The node ``pointer`` names in a document of RECORD, READ THROUGH ITS STORAGE.

    ``docs/plan/architecture.md``, "A READER ASKING WHAT THE DOCUMENT STATES READS
    THROUGH THE STORAGE": the record holds each distinct subtree once and references the
    entry at every occurrence, so **a reference to a storage entry is not a fact the
    document states -- it is where the fact is kept.**  Every question this file asks is
    semantic (what does this document require at this pointer, what does it admit there),
    so every walk here dereferences.

    **The dereference is the package's own seam and not a second reading written here**,
    which is the other half of that section: ``through_the_store`` for the hop a DESCENT
    crosses -- a pointer that walked into the inlined text walks into a reference now, and
    that function is what makes the two the same pointer -- and ``bundle.expanded`` for the
    node handed back.

    The node is handed back EXPANDED because every caller here makes it the ROOT of a
    ``jsonschema.Draft7Validator``, where a surviving ``#/definitions/Shared<N>`` resolves
    against the node rather than against the record and raises ``PointerToNowhere``.  That
    is what three checks did on the merged tree, and the classes they grade were right:
    ``Account._ROOT_REQUIRED`` is ``('brand', 'operator')`` and the arm's ``required`` is
    ``['status', 'task_id']``.  The stored form is the record's and is not the thing to
    change; the raw walk was.
    """
    node = root
    for part in [p for p in pointer.lstrip("#").split("/") if p]:
        node = through_the_store(node, root)
        node = node[int(part)] if isinstance(node, list) else node[part]
    return bundle.expanded(node, root)


def _union_node(node: Any) -> dict | None:
    """The node that states the combinator, found from the one a CLASS is cut at.

    A union root reached through an ``allOf`` conjunct is a class at the COMPOSING
    node's pointer, so the keyword is one hop down -- and the record has already inlined
    the reference, which is why this descends ``allOf`` and nothing else.
    """
    if not isinstance(node, dict):
        return None
    if any(kw in node for kw in UNION):
        return node
    for conjunct in node.get("allOf") or []:
        found = _union_node(conjunct)
        if found is not None:
            return found
    return None


def _required_names(node: Any, root: Any) -> frozenset[str]:
    """Every name this declaration requires ON ITS OWN, through its ``allOf`` conjuncts
    and through a LOCAL ``$ref``.

    ``codegen.lower.union.requires``' reading of a branch, on the document side: a
    ``required`` inside a conjunct requires those names just as much, because draft-07
    applies a conjunct to the same instance, and a bare ``$ref`` branch requires what its
    TARGET requires -- which is where that branch's fields come from (§4's two bases).

    **The LOCAL pointer is followed and the absolute one is already gone**: the record
    inlines every cross-document reference and leaves a ``#/definitions/x`` alone, so
    ``core/requirements/catalog-field-binding.json``'s two branches are each
    ``{"$ref": "#/definitions/<X>"}`` and the ``kind`` they pin is required by the ENTRY.
    Read without this hop they look like branches requiring nothing, and the check
    reports a defect the document does not have.
    """
    if not isinstance(node, dict):
        return frozenset()
    names = frozenset(n for n in (node.get("required") or []) if isinstance(n, str))
    for conjunct in node.get("allOf") or []:
        names |= _required_names(conjunct, root)
    ref = node.get("$ref")
    if isinstance(ref, str) and ref.startswith("#"):
        names |= _required_names(_at(root, ref), root)
    return names


def _emitted_mixin_classes() -> dict[str, type[BaseModel]]:
    """Every class of the committed tree that carries :class:`BranchDispatchMixin`.

    Keyed by its qualified name, which is what a failure has to report: a base and the
    branches that inherit its ``_branch_adapter`` fail together, so the three names tell
    a reader which base the one defect is.
    """
    names = sorted(
        info.name
        for info in pkgutil.walk_packages(schemas_pkg.__path__, schemas_pkg.__name__ + ".")
        if not info.ispkg
    )
    out: dict[str, type[BaseModel]] = {}
    for name in names:
        module = importlib.import_module(name)
        for value in vars(module).values():
            if (
                isinstance(value, type)
                and issubclass(value, BaseModel)
                and issubclass(value, BranchDispatchMixin)
                and value.__module__ == name
            ):
                out[f"{name}.{value.__name__}"] = value
    return out


def test_every_union_bases_dispatch_constructs() -> None:
    """Reading 3's first half: constructing the dispatch raises for no class.

    **The FAILURE IS COLLECTED AND NOT RAISED**, because the obligation is over every
    class and the first raising one would otherwise hide the rest -- which is the defect
    82m.23 records from the other side: pydantic's message names the first branch it
    INSPECTS (``RefineProposalsResponseCompleted``, the one that IS pinned) rather than
    the branch at fault, so a reader following one traceback goes to the wrong class.
    The whole list is the finding.

    Ranged over every class carrying the mixin and not over the bases alone, for the
    same reason: ``_branch_adapter`` is inherited, so a branch of a broken base raises
    too, and a population of bases would report the one defect as one line where the
    consumer meets three.
    """
    classes = _emitted_mixin_classes()
    population = claimed("classes carrying BranchDispatchMixin", classes)
    raised = {}
    for name in sorted(population):
        try:
            classes[name]._branch_adapter()
        except Exception as why:  # the failure IS the finding
            raised[name] = f"{type(why).__name__}: {why}"
    assert raised == {}, raised


def test_no_union_dispatches_on_a_key_its_document_lets_an_instance_omit() -> None:
    """Reading 3's second half, read off the documents of record.

    §4's first dispatch source, corrected 2026-11-02: "A ``const`` every branch pins on
    one shared property AND every branch REQUIRES."  A discriminator is a total function
    from the instance to one branch, so the key has to be present in every instance the
    document admits, and two entailments give that:

    * the ROOT's own ``required`` names it -- draft-07 applies a root's ``required`` to
      the same instance every branch describes, so the key is there whatever a branch
      says about it.  ``creative/preview-creative-response.json``'s results item is the
      bundle's one case of this alone: both branches pin ``success`` and NEITHER requires
      it, and the root's ``required`` is what makes the pin a discriminator;
    * or every BRANCH requires it, which is every other discriminated root here.

    Asserted as "no root dispatches on a key NEITHER entailment covers", which is the
    sentence rather than a census: a root that gains a key passes if the key is
    guaranteed and fails if it is not, and no number here moves when the emitter emits
    more.
    """
    records = _records()
    classes = _emitted_mixin_classes()
    keyed = {
        name: cls
        for name, cls in classes.items()
        if cls.__dict__.get("_branch_models") and cls.__dict__.get("_BRANCH_DISCRIMINATOR")
    }
    population = claimed("emitted union bases carrying a dispatch key", keyed)
    undetermined = {}
    for name in sorted(population):
        cls = keyed[name]
        key = cls.__dict__["_BRANCH_DISCRIMINATOR"]
        ref = cls.__dict__["__adcp_schema__"]
        root = records[ref.document]
        node = _union_node(_at(root, ref.pointer))
        assert node is not None, (name, ref.document, ref.pointer, "no combinator found")
        kw = next(k for k in UNION if k in node)
        if key in _required_names(node, root):
            continue
        omitting = [i for i, b in enumerate(node[kw]) if key not in _required_names(b, root)]
        if omitting:
            undetermined[name] = (ref.document, f"{ref.pointer}/{kw}", key, omitting)
    assert undetermined == {}, undetermined


# --------------------------------------------------------------------------- #
# adcp-client-python-82m.23: a union arm's property restatement, dropped whole
# --------------------------------------------------------------------------- #
REFINE = "media-buy/refine-proposals-response.json"


def _refine_record() -> dict:
    return bundle.record(BUNDLE, REFINE, set(bundle.portable(BUNDLE)))


@pytest.mark.parametrize(
    "payload",
    [
        {"status": "submitted", "task_id": "0"},
        {"status": "completed", "results": [], "products": []},
        {},
    ],
    ids=["arm1", "arm0-with-an-empty-results", "empty"],
)
def test_the_refine_proposals_root_answers_every_payload(payload: dict) -> None:
    """82m.23 direction 1: the root RESOLVES or REFUSES, and never raises.

    All three raised ``PydanticUserError: Model
    'RefineProposalsResponseCompleted' needs field 'status' to be of type Literal``
    before the row landed -- at adapter-build time, so the payload was never looked at
    and the verdict was the same for a payload the document admits and one it refuses.

    The two sides are asserted TOGETHER rather than as "it does not raise", because
    "does not raise" is also satisfied by a root that admits everything: the document's
    own verdict is what each resolution is compared against.
    """
    admitted = jsonschema.Draft7Validator(_refine_record()).is_valid(payload)
    module = importlib.import_module("adcp.types._schemas.media_buy.refine_proposals_response")
    root = module.RefineProposalsResponse
    try:
        got = root.model_validate(payload)
    except ValidationError:
        assert not admitted, f"the document admits {payload!r} and the root refused it"
    else:
        assert admitted, f"the document refuses {payload!r} and the root returned {got!r}"
        assert isinstance(got, root)


def test_the_submitted_arm_requires_what_its_target_requires() -> None:
    """82m.23 direction 2: the branch class is not wider than its own node.

    ``#/anyOf/1`` is a bare ``$ref`` to ``core/compact-task-submitted.json``, which
    requires ``status`` and ``task_id``.  The branch class subclasses ``(the union base,
    the target)``, so the MRO found the ROOT's optional ``status`` and ``task_id`` and
    the target's required ones were shadowed: the class admitted ``{"task_id": "0"}``,
    which its node refuses.
    """
    node = _at(_refine_record(), "#/anyOf/1")
    module = importlib.import_module("adcp.types._schemas.media_buy.refine_proposals_response")
    arm = module.RefineProposalsResponseSubmitted
    payload = {"task_id": "0"}
    assert not jsonschema.Draft7Validator(node).is_valid(payload)
    with pytest.raises(ValidationError):
        arm.model_validate(payload)
    # The control, so the row is a NARROWING of the class and not a closing of it: the
    # same payload with ``status`` is admitted by node and class alike.
    whole = {"status": "submitted", "task_id": "0"}
    assert jsonschema.Draft7Validator(node).is_valid(whole)
    assert arm.model_validate(whole).task_id == "0"


# --------------------------------------------------------------------------- #
# adcp-client-python-82m.24: a restatement requiring a key the target declares
# only inside a combinator arm
# --------------------------------------------------------------------------- #
#: Each site of the bundle where a property position restates ``required`` over a target
#: that declares those names only inside one of its own arms, and a CLASS is cut at the
#: restatement's own pointer.  The symbol is the module attribute the class is bound to.
#:
#: Pinned as a set of SITES and not as a count: these are positions of the bundle
#: SOURCE, which does not move when a row lands.
ACCOUNT_RESTATEMENTS = (
    ("media-buy/buy-products-request.json", "#/anyOf/1/properties/account",
     "adcp.types._schemas.media_buy.buy_products_request", "Account"),
    ("media-buy/request-proposals-request.json", "#/anyOf/1/properties/account",
     "adcp.types._schemas.media_buy.request_proposals_request", "Account"),
)


@pytest.mark.parametrize(("document", "pointer", "module", "symbol"), ACCOUNT_RESTATEMENTS)
def test_a_restated_required_key_is_required_of_the_class(
    document: str, pointer: str, module: str, symbol: str
) -> None:
    """82m.24: ``allOf`` INTERSECTS, so the restated required keys bind at that position.

    The judged node is the CONJUNCTION the class stands for -- what the root declares at
    ``properties/account`` and what the branch restates there -- because that is what
    draft-07 applies to an instance at that pointer and what §2's intersection rule has
    the class carry.  Both conjuncts are read off the record rather than written here.

    The restated names are declared only inside the target's own ``anyOf/1``, so the base
    has no field for either and its ``account_id`` branch declares neither: the class
    resolved ``{"account_id": "a1"}`` to that branch and returned it.
    """
    record = bundle.record(BUNDLE, document, set(bundle.portable(BUNDLE)))
    conjunction = {
        "allOf": [
            _at(record, "#/properties/account"),
            _at(record, pointer),
        ]
    }
    cls = getattr(importlib.import_module(module), symbol)
    payload = {"account_id": "a1"}
    assert not jsonschema.Draft7Validator(conjunction).is_valid(payload)
    with pytest.raises(ValidationError):
        cls.model_validate(payload)
    # The control: an instance carrying the restated keys is admitted by both, so the
    # row narrowed the class to its document and did not close it.
    natural = {"brand": {"domain": "nova-athletics.example"}, "operator": "nova.example"}
    assert jsonschema.Draft7Validator(conjunction).is_valid(natural)
    assert isinstance(cls.model_validate(natural), cls)
