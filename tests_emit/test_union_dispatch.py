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
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import fresh
import jsonschema
import pytest
from pydantic import BaseModel, ValidationError

import adcp.types._schemas as schemas_pkg
from adcp.types._base import BranchDispatchMixin, applied_schema, through_the_store
from codegen import bundle, catalogue, harness, held
from nodeset import claimed, partitions, ratchet

REPO = Path(__file__).resolve().parents[1]
#: **The bundle a run reads, taken from the ONE declaration of it**
#: (``adcp-client-python-lzzj.11.1``).  This module held its own PUBLISHED literal while
#: every class it grades was emitted from the PATCHED bundle, so its two halves ranged over
#: two different document sets.  Measured against ``fresh.PUBLISHED``: the published
#: directory is portable over 1,054 documents and the run's over 1,059, the five only the
#: patched one holds are documents ``patches/8525`` ADDS, and of the 1,054 they share 211
#: differ -- 200 of those beyond ``$schema``/``title``/``description``.  So the published
#: path is ``adcp-client-python-fr4r``'s lookup error waiting at whichever clause names a
#: document first, and a quietly different answer at each of the others.
BUNDLE = fresh.BUNDLE
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


def _mixin_classes(package: Any) -> dict[str, type[BaseModel]]:
    """Every class of a tree rooted at ``package`` that carries
    :class:`BranchDispatchMixin`.

    Keyed by its qualified name, which is what a failure has to report: a base and the
    branches that inherit its ``_branch_adapter`` fail together, so the three names tell
    a reader which base the one defect is.

    **A PACKAGE ROOT IS A DOCUMENT'S MODULE, so ``ispkg`` is NOT a screen here**
    (``adcp-client-python-bxu``, the reading, and ``-5uz``, this site).
    ``emit.module_file``'s layout rule writes a document whose own path is also a
    DIRECTORY of the bundle to ``<path>/__init__.py``, so ``brand.json``'s module is
    ``adcp.types._schemas.brand`` and ``pkgutil`` reports it as a package.  Screening
    those out put 31 of the tree's 1,088 modules outside reading 3 -- 30 empty layout
    markers and ``brand/__init__.py``, which carries 111 class statements, 68 pydantic
    classes and 44 enums -- so a union base or branch declared by ``brand.json`` was
    never asked to construct its dispatch.

    **MEASURED HERE, which is what says the screen cost this file a reading and not only
    a module count**: with it, 718 classes carry the mixin; without it, 728.  The ten are
    ``brand``'s, and one of them -- ``ColorRef`` -- is a base CARRYING A DISPATCH KEY, so
    1 of this file's 83 keyed bases was never compared against the key its document
    guarantees (:func:`test_no_union_dispatches_on_a_key_its_document_lets_an_instance_omit`).
    That second gate's OTHER half is sighted: ``_records`` ranges over
    ``bundle.portable``, which holds ``brand.json``.  It is a LOOKUP and not a
    denominator, though, so a sighted document side cannot notice a class side that is
    short -- the enumeration here is the only thing either gate ranges over.

    Recursion was never what the screen cost: ``walk_packages`` descends into a package
    whether or not the caller keeps its ``ispkg`` entry, so what was lost is exactly the
    package's OWN ``__init__.py`` body.  The tree's own root is outside this walk by
    construction and nothing is lost there -- ``walk_packages`` enumerates a package's
    CHILDREN, and a package's ``__init__`` IS the package -- and ``_schemas/__init__.py``
    is the empty marker ``emit.write`` writes.

    **The package is a PARAMETER** so that the reading can be run over a tree built to
    carry a known defect, which is the only thing that says it reaches one:
    :func:`test_the_dispatch_reading_reaches_a_union_base_a_package_root_declares` is
    that A/B, and the real tree is green either way.
    """
    names = sorted(
        info.name
        for info in pkgutil.walk_packages(package.__path__, package.__name__ + ".")
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


def _emitted_mixin_classes() -> dict[str, type[BaseModel]]:
    """:func:`_mixin_classes` over the tree a fresh run emits, which is what §4 grades."""
    return _mixin_classes(schemas_pkg)


def _dispatch_failures(classes: dict[str, type[BaseModel]]) -> dict[str, str]:
    """Every class whose dispatch does not CONSTRUCT, with pydantic's own reason.

    **The failure is collected and not raised**, because the obligation is over every
    class and the first raising one would otherwise hide the rest -- which is the defect
    ``adcp-client-python-82m.23`` records from the other side: pydantic's message names
    the first branch it INSPECTS rather than the branch at fault, so a reader following
    one traceback goes to the wrong class.  The whole list is the finding.
    """
    raised: dict[str, str] = {}
    for name in sorted(classes):
        try:
            classes[name]._branch_adapter()
        except Exception as why:  # the failure IS the finding
            raised[name] = f"{type(why).__name__}: {why}"
    return raised


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

    **THIS GATE HAS NO SECOND DERIVATION**, which is why the one below exists.  It is an
    absence over one enumeration -- nothing else here says how many union bases the
    bundle states -- so a walk that cannot see part of the tree reports green for free on
    that part and no equality disagrees.  ``claimed`` refuses only an EMPTY population.
    """
    classes = _emitted_mixin_classes()
    population = claimed("classes carrying BranchDispatchMixin", classes)
    raised = _dispatch_failures({name: classes[name] for name in population})
    assert raised == {}, raised


def _declaring_bases() -> dict[str, type[BaseModel]]:
    """Every emitted class that DECLARES a branch list, which is what a union base is.

    ``_branch_models`` is inherited, so ``__dict__`` and not ``getattr``: a branch of a
    base carries the attribute and is not a base, and the distinction is the one
    ``test_a_consumers_subclass_of_a_union_base_keeps_its_own_schema`` is about.
    """
    classes = _emitted_mixin_classes()
    return {n: c for n, c in classes.items() if c.__dict__.get("_branch_models")}


def _dispatched_to(branch: type, got: type) -> bool:
    """Is ``got`` the class dispatch reaches from ``branch``?

    ``branch`` itself, or a class one of the union bases beneath it names in its OWN
    ``_branch_models`` -- transitively, because §5's nested row makes a branch that
    composes a union a BASE of its own and the hook fires again inside it.  That second
    hop is ``adcp-client-python-1bj``: ``adagents.json``'s
    ``AdCPAgentsAuthorizationCommunityFormatRegistry`` is the root's ``#/oneOf/1`` and the
    class a payload drawn from it comes back as is ``…CommunityFormatRegistryBranch0``,
    declared at ``#/oneOf/1/allOf/0/anyOf/0`` -- a branch OF that branch, reached by
    dispatch, which is this reading holding at a nested root and not failing at the outer
    one.  The other root branch, ``…AuthoritativeLocation``, REFUSES that payload and the
    document refuses it at ``#/oneOf/0`` on ``'authoritative_location' is a required
    property``, so the two branches do not overlap and the hop is the only admissible
    answer -- which is the measurement that closed that row.

    The walk is over the DECLARED lists and never ``issubclass``, which would admit a
    consumer's unrelated refinement and so would stop the check grading the dispatch at
    all.

    **This is a SECOND SPELLING of ``tests/test_emit.py``'s ``_dispatched_to`` and that is
    ``adcp-client-python-mz8l``'s row**, not a decision taken here: the relation belongs
    beside ``_branch_models``, which ``adcp/types/_base.py`` declares, and moving it is a
    change to a file two other lanes are live in.
    """
    seen: set[type] = set()
    frontier = [branch]
    while frontier:
        at = frontier.pop()
        if at is got:
            return True
        if at in seen:
            continue
        seen.add(at)
        frontier += list(at.__dict__.get("_branch_models", ()))
    return False


def _admits(root: dict, pointer: str, payload: Any) -> str:
    """``""`` where the document admits ``payload`` at ``pointer``, else its first reason.

    **The document side is ``_base.applied_schema``**, which is §8's pairing rule -- "a
    branch class of a root union is paired with its branch node read UNDER THE ROOT'S
    SIBLINGS" -- and not a reading written here.  Asked at ``"#"`` it is the whole
    document, which is the screen reading 3's own sentence names: *for every payload the
    document admits*.

    **The RESOLUTION SCOPE is the document and the SCHEMA is the node, spelled the way
    ``_base._refuse_at`` spells it** -- ``validator(scope).evolve(schema=node)`` -- so a
    local ``$ref`` the record leaves alone resolves against the document and this file
    states no second reading of what a refusal is.  The format checker comes with it for
    the same reason: it is the set the production path asserts under.
    """
    node = applied_schema(root, pointer)
    validator = jsonschema.validators.validator_for(root, jsonschema.Draft7Validator)
    at_the_node = validator(root, format_checker=validator.FORMAT_CHECKER).evolve(schema=node)
    errors = sorted(
        at_the_node.iter_errors(payload), key=lambda e: [str(p) for p in e.absolute_path]
    )
    return "" if not errors else errors[0].message[:160]


def _underdetermined(base: type) -> bool:
    """Does this base DECLARE that which branch an overlapping payload becomes is dropped?

    §4's own answer for a union matching none of the three dispatch sources: "a union
    matching none of the three emits a plain ``A | B`` over its branches and declares an
    UNDERDETERMINED approximation at the union's pointer".  Read off the CLASS's own
    ``__adcp_approximations__`` -- the declaration a consumer of the wheel can see --
    rather than off a compile, so the exemption below is one the TREE states and not one
    this file grants.
    """
    return any(
        a.kind == "UNDERDETERMINED" for a in getattr(base, "__adcp_approximations__", ())
    )


def _answering_pointer(base: type, got: type) -> str:
    """The pointer the class that ANSWERED a dispatch carries, as a document pointer.

    Read off the class's own ``__adcp_schema__`` and not off the branch list's index,
    because the answering class may be a branch OF a branch (``adcp-client-python-1bj``)
    and its pointer is then nested.  ``base`` is unused and kept so that a caller holding
    both reads as asking a question about the pair.
    """
    del base
    ref = got.__dict__.get("__adcp_schema__") or got.__adcp_schema__
    return "#" + ref.pointer.lstrip("#")


def _branches_the_document_admits(base: type, root: dict, payload: Any) -> list[str]:
    """The branch pointers of ``base`` whose own node the DOCUMENT admits ``payload`` at.

    The question ``adcp-client-python-1bj`` says has to be asked before any landing is
    called a defect, asked of EVERY branch rather than of the two the verdict names: a
    dispatch that answers with one of several admissible branches has dropped the fact
    the UNDERDETERMINED declaration at the combinator says is dropped, and a dispatch
    that REFUSES where exactly one branch is admissible has thrown away an answer the
    document determined.  Those are different outcomes and the count is what separates
    them.

    **It also refutes one sentence of ``adcp-client-python-84a9``, which is why it is
    derived here rather than taken from that row.**  84a9 reads "the branches do NOT
    overlap in the DOCUMENT for these four payloads -- the document names exactly one
    admissible branch each".  Measured over the documents of record, the document admits
    17, 16, 16 and 32 of ``core/async-response-data.json``'s 42 branches for those four
    payloads.  The defect stands -- the branch that ANSWERED is one the document refuses
    -- and the repair 84a9's sentence implies, re-dispatching to "the document's branch",
    does not exist.
    """
    return [
        pointer
        for branch in base.__dict__["_branch_models"]
        if not _admits(root, (pointer := _answering_pointer(base, branch)), payload)
    ]


def test_a_payload_the_document_admits_dispatches_to_the_branch_it_was_drawn_from() -> None:
    """Reading 3's SENTENCE, graded on behaviour: offer a payload, read the class back.

    "A payload offered to a union base resolves to its branch, for every payload the
    document admits."  :func:`test_every_union_bases_dispatch_constructs` grades the
    decider's first conjunct -- the dispatch CONSTRUCTS -- and that is not this: a base
    whose adapter builds can still hand a caller an object that is not what it was given,
    silently, which is worse than a refusal.  So this one offers a VALUE and asserts the
    TYPE that comes back.

    **THE PAYLOAD IS DRAWN AND COMMITTED, AND NEITHER HALF IS A CONVENIENCE.**  It is the
    instance the accepts corpus holds at the BRANCH's own pointer -- ``tests/accepts-corpus``,
    the floor, read through ``harness.corpus_key`` over the branch's static identity.
    DRAWN, so this cannot pass by hand-picking an instance that happens to resolve;
    COMMITTED, so every lane and CI grade the same witness and the clause costs file reads
    rather than the 677 s a redraw of the same 584 instances costs
    (``adcp-client-python-1bj``'s second fact).  The CACHE is deliberately not read:
    ``codegen.held``'s own rule is that a warm lane must not grade a witness the tree does
    not carry.

    **THE VERDICT IS COMPARED BY REASON AND NOT ONLY BY OUTCOME**, which is the whole of
    why the exemption below is small enough to state.  A payload landing on another branch
    is not automatically a defect: where the DOCUMENT admits that other branch too, the
    branches overlap and §4's own answer is already written down -- "a union matching none
    of the three emits a plain ``A | B`` over its branches and declares an UNDERDETERMINED
    approximation at the union's pointer", and "WHICH branch an overlapping payload becomes
    is the fact dropped".  So the exemption is the base's OWN DECLARATION
    (:func:`_underdetermined`), read off the class a consumer holds; a base that declares
    nothing gets no exemption, and a base that declares one must still land INSIDE its own
    branch list.

    **AND THE EXEMPTION A DECLARED WIDENING USED TO BUY IS GONE, which is
    ``adcp-client-python-84a9`` answered by the owner's ruling of 2026-11-06** -- *"if the
    discriminator is empty, I believe that's a schema error"*, and a dispatch must not
    guess where the document gives it nothing to dispatch on.  A landing the document
    REFUSES at the answering branch is now ``wrong`` whatever any document declares, and
    nothing is exempted for being widened one document away.  What takes its place is the
    REFUSAL the keyless dispatch now raises
    (``adcp.types._base.BranchDispatchMixin._undetermined``) and the one obligation a
    refusal owes: **where the document admits exactly ONE branch, the dispatch may not
    refuse** -- it had an answer the document determined and threw it away.  Over 0 or 2
    or more admissible branches there is no such answer and the refusal is the only thing
    that is not a guess.

    **Measured on this bundle at this commit**: 141 bases naming 586 branch positions, 584
    of which the committed floor answers for (the two it does not are
    ``adcp-client-python-rgoo``, and ``unheld`` below is what reports them); 497 of those
    584 the document admits at its ROOT, and the 87 it refuses are not what this reading is
    about -- ``trusted-match/provider-registration.json`` is the instructive one, where the
    root's ``if``/``then`` requires ``countries``, the instance drawn at ``#/anyOf/1`` is
    admitted by that branch node and refused by the document, and the base refuses it
    correctly.  Of the 497: 447 reach the branch they were drawn from or a branch of it, 46
    land on a branch the document ALSO admits under a base declaring UNDERDETERMINED, and 4
    are REFUSED by the base -- the four of 84a9, each drawn at a branch of
    ``core/async-response-data.json``'s 42-branch ``anyOf``, each of which used to come
    back as ``#/anyOf/0``'s ``AdCPAsyncResponseDataGetProductsResponse``, which the
    document refuses on ``'errors' is a required property`` or ``'products' is a required
    property``.  The document admits 17, 16, 16 and 32 branches for them, so not one has a
    branch the document determines.

    **AND NONE OF THOSE NUMBERS IS ASSERTED, which is deliberate and is this suite's own
    rule** (``tests/test_every_check_names_its_set.py``: a check may not pin a census as an
    equality).  The non-vacuity defence this clause needs is real all the same, because the
    payloads come from a committed store and a key derivation that stopped matching would
    make every assertion here hold over an empty loop.  So it is :func:`claimed` and
    :func:`partitions` instead: the bases are named, the branch positions the floor answers
    for are named, and both the screen and the outcome are PARTITIONS -- every branch
    position is offered-or-unheld, every offered payload is admitted-or-refused by the
    document, and every graded payload reached its branch or landed elsewhere under a
    declaration.  Measured: pointing :data:`codegen.held.COMMITTED` at a directory that is
    not there takes this clause from green to ``empty set of nodes -- every assertion over
    it holds vacuously``.
    """
    bases = _declaring_bases()
    graded_bases = claimed("emitted union bases declaring a branch list", bases)
    records = _records()
    identities = catalogue.admitted_identities(BUNDLE, stated=harness.stated_instances)
    floor = held.Store(held.COMMITTED)

    positions: set[tuple[str, str]] = set()
    offered: set[tuple[str, str]] = set()
    unheld: set[tuple[str, str]] = set()
    admitted: set[tuple[str, str]] = set()
    refused_by_the_document: set[tuple[str, str]] = set()
    reached_its_branch: set[tuple[str, str]] = set()
    elsewhere_the_document_also_admits: set[tuple[str, str]] = set()
    refused_as_undetermined: set[tuple[str, str]] = set()
    wrong: dict[str, tuple[str, str, str, str]] = {}
    for name in sorted(graded_bases):
        base = bases[name]
        for branch in base.__dict__["_branch_models"]:
            ref = branch.__dict__["__adcp_schema__"]
            site = (ref.document, ref.pointer)
            positions.add(site)
            key = harness.corpus_key(
                {
                    "document": ref.document,
                    "pointer": ref.pointer,
                    "admits": identities.get(ref.document),
                },
                custom_formats=harness.FORMAT_STRATEGIES,
            )
            payload = (floor.get(key) or [None])[0]
            if payload is None:
                unheld.add(site)
                continue
            offered.add(site)
            root = records[ref.document]
            if _admits(root, "#", payload):
                # Not a payload the DOCUMENT admits, so not what this reading is about.
                refused_by_the_document.add(site)
                continue
            admitted.add(site)
            try:
                got = type(base.model_validate(payload))
            except ValidationError:
                # **THE KEYLESS DISPATCH REFUSED RATHER THAN GUESSED**
                # (``adcp.types._base.BranchDispatchMixin._undetermined``,
                # ``adcp-client-python-84a9``).  The one obligation a refusal owes is that
                # the document determined no branch: where it admits exactly ONE, the
                # dispatch had the answer and threw it away, and that is a defect of ours
                # whatever the document does.
                where = f"{name} <- {branch.__name__} -> REFUSED"
                determined = _branches_the_document_admits(base, root, payload)
                if len(determined) == 1:
                    wrong[where] = (
                        ref.document,
                        ref.pointer,
                        "the document admits exactly one branch "
                        f"({determined[0]}) and the dispatch refused",
                        repr(payload)[:200],
                    )
                else:
                    refused_as_undetermined.add(site)
                continue
            if _dispatched_to(branch, got):
                reached_its_branch.add(site)
                continue
            where = f"{name} <- {branch.__name__} -> {got.__name__}"
            if not _underdetermined(base):
                wrong[where] = (
                    ref.document,
                    ref.pointer,
                    "no UNDERDETERMINED declared",
                    repr(payload)[:200],
                )
            elif not any(
                _dispatched_to(other, got) for other in base.__dict__["_branch_models"]
            ):
                wrong[where] = (
                    ref.document,
                    ref.pointer,
                    "outside the base's own branch list",
                    repr(payload)[:200],
                )
            elif not _admits(root, _answering_pointer(base, got), payload):
                # The branches OVERLAP in the document, which is the case the
                # UNDERDETERMINED declaration at the combinator describes in its own words:
                # "WHICH branch an overlapping payload becomes is the fact dropped".
                elsewhere_the_document_also_admits.add(site)
            else:
                # **A LANDING THE DOCUMENT REFUSES IS A WRONG OBJECT IN A CALLER'S HANDS,
                # and nothing exempts it** (``adcp-client-python-84a9``, the owner's ruling
                # of 2026-11-06).  A declared widening one document away used to: the
                # answering branch is a bare ``$ref``, its class inherits a root declaring
                # ``WIDENED`` at ``#``, and the keyless dispatch SELECTS with
                # ``model_validate`` -- the wide verdict -- so a structural first match
                # reached a branch the document gives to someone else.  The exemption is
                # removed rather than narrowed, and what answers the four payloads it
                # covered is the dispatch's own refusal above.
                wrong[where] = (
                    ref.document,
                    ref.pointer,
                    "the document REFUSES the answering branch "
                    f"({_answering_pointer(base, got)}): "
                    f"{_admits(root, _answering_pointer(base, got), payload)}",
                    repr(payload)[:200],
                )
    assert wrong == {}, wrong
    claimed("branch positions a union base names", positions)
    claimed("branch positions the committed accepts floor answers for", offered)
    partitions(positions, offered=offered, unheld=unheld)
    partitions(offered, admitted=admitted, refused_by_the_document=refused_by_the_document)
    claimed("branch payloads the document admits at its root", admitted)
    partitions(
        admitted,
        reached_its_branch=reached_its_branch,
        elsewhere_the_document_also_admits=elsewhere_the_document_also_admits,
        refused_as_undetermined=refused_as_undetermined,
    )
    claimed("branch payloads that reached their own branch", reached_its_branch)


# --------------------------------------------------------------------------- #
# adcp-client-python-84a9: a keyless dispatch, and the four payloads it answered wrong
# --------------------------------------------------------------------------- #
ASYNC = "core/async-response-data.json"

#: The owner's own payload, 2026-11-06: *"The failure payload has to be a get-products
#: error response.  Why does it get differently?"*  It is the committed accepts floor's
#: instance at ``core/async-response-data.json#/anyOf/18`` -- a ``create_media_buy``
#: FAILURE -- and it is spelled here rather than read from the store because a row has to
#: carry its own evidence (``adcp-client-python``'s memory on a bead citing lane scratch).
A_CREATE_MEDIA_BUY_FAILURE = {
    "confirmed_at": None,
    "media_buy_id": "",
    "packages": [],
    "revision": 1,
    "status": "failed",
}
#: The CONTROL, and the floor's instance at ``#/anyOf/0`` itself: a payload the document
#: ADMITS at that branch comes back as that branch, so the row below is a narrowing of the
#: dispatch and not a closing of the base.
A_GET_PRODUCTS_RESPONSE = {
    "cache_scope": "public",
    "status": "failed",
    "unchanged": True,
    "wholesale_feed_version": "",
}


def test_a_keyless_dispatch_refuses_rather_than_answering_with_a_branch_the_document_refuses() -> (
    None
):
    """``adcp-client-python-84a9``, graded by a VALUE on both sides.

    ``core/async-response-data.json``'s root is a 42-branch ``anyOf`` whose branches pin
    no property the document guarantees, so ``_BRANCH_DISCRIMINATOR`` is ``""`` and the
    branch is selected by a structural first match.  ``#/anyOf/0`` is a bare ``$ref`` to
    ``media-buy/get-products-response.json``, whose root DECLARES ``('#', 'WIDENED',
    'if')`` -- its ``if``/``then``/``else`` chain is what requires ``errors`` on a failed
    response, a rule ``model_validate`` does not apply -- so the branch class admits
    payloads its own node refuses and the first match reached it.

    **The four facts, each a value and not a structure.**  The document admits the payload
    at its ROOT; the document REFUSES it at ``#/anyOf/0``; the class at ``#/anyOf/0``
    agrees with its document, because ``strict_validate`` refuses it with THAT SAME reason
    while ``model_validate`` admits; and the BASE therefore refuses, naming the combinator,
    the branch that matched and the document's own sentence.

    **It is not ``adcp-client-python-1bj``**, where the other root branch REFUSED the
    payload and the hop was the only admissible answer.  Here the DRAWN branch
    (``#/anyOf/18``) admits on both sides and ``#/anyOf/0`` refuses on both sides, so the
    class is right and the dispatch was wrong.

    **And the refusal is not a closing of the base**: the control payload, the floor's own
    instance at ``#/anyOf/0``, is admitted by the document there and still comes back as
    that branch's class.
    """
    root = _records()[ASYNC]
    module = importlib.import_module("adcp.types._schemas.core.async_response_data")
    base = module.AdCPAsyncResponseData
    at_zero = next(
        b for b in base.__dict__["_branch_models"] if b.__adcp_schema__.pointer == "#/anyOf/0"
    )

    # The document's own verdicts, with their reasons, on both sides of the dispatch.
    assert _admits(root, "#", A_CREATE_MEDIA_BUY_FAILURE) == ""
    assert _admits(root, "#/anyOf/18", A_CREATE_MEDIA_BUY_FAILURE) == ""
    assert (
        "'errors' is a required property"
        in _admits(root, "#/anyOf/0", A_CREATE_MEDIA_BUY_FAILURE)
    )

    # The CLASS at #/anyOf/0 agrees with its document and only the wide verdict admits,
    # which is the widening arriving at a dispatch.
    assert isinstance(
        at_zero.model_validate(A_CREATE_MEDIA_BUY_FAILURE), at_zero
    ), "the branch class's wide verdict is the premise of this row"
    with pytest.raises(ValidationError) as refused_strictly:
        at_zero.strict_validate(A_CREATE_MEDIA_BUY_FAILURE)
    assert "'errors' is a required property" in str(refused_strictly.value)

    # THE DISPATCH REFUSES, and it names what it refused on.
    with pytest.raises(ValidationError) as refused:
        base.model_validate(A_CREATE_MEDIA_BUY_FAILURE)
    reported = refused.value.errors()[0]
    assert reported["type"] == "anyOf", reported
    assert "#/anyOf/0" in reported["msg"] and "no discriminator" in reported["msg"], reported
    assert "'errors' is a required property" in reported["msg"], reported

    # THE CONTROL: a payload the document admits at #/anyOf/0 still resolves to it.
    assert _admits(root, "#/anyOf/0", A_GET_PRODUCTS_RESPONSE) == ""
    assert _dispatched_to(at_zero, type(base.model_validate(A_GET_PRODUCTS_RESPONSE)))


#: A union root with a dispatch key, as a module declares one: a base naming the key, two
#: branches pinning it, and ``_branch_models`` assigned after they exist.  ``branch_one``
#: is the one thing that varies, because it is where ``adcp-client-python-82m.23``'s
#: defect sits -- a branch whose dispatch key is ``Optional[Literal[...]]`` is refused by
#: pydantic when the ADAPTER IS BUILT, so every class of that union raises.
_A_UNION = """\
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel

from adcp.types._base import BranchDispatchMixin


class {stem}Base(BranchDispatchMixin, BaseModel):
    _BRANCH_DISCRIMINATOR = "kind"


class {stem}One({stem}Base):
    kind: {branch_one}


class {stem}Two({stem}Base):
    kind: Literal["two"]


{stem}Base._branch_models = ({stem}One, {stem}Two)
"""


def test_the_dispatch_reading_reaches_a_union_base_a_package_root_declares(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``adcp-client-python-5uz``: the reading above over a tree whose PACKAGE ROOT is
    where the defect is.

    §9: a rule nothing can break is a finding about the rule.  The gate above is green
    with the ``ispkg`` screen and green without it -- the previous lane A/B'd it and the
    tree is clean behind the screen -- so **its own green says nothing about which modules
    it reached**, and a later edit could restore the screen without reddening anything.
    Here the package root carries a DEFECT, so the reading either names it or does not.

    The population is a hand-built tree and not the bundle's, for
    ``tests/test_the_tree_imports.py``'s reason: what is graded is the READING and not the
    compiler, and four files answer the question in a second where the real tree is 1,088
    modules and costs minutes.  Its shape is ``brand/``'s -- a document's module written to the package's own
    ``__init__.py``, with the directory's documents as its submodules -- which is
    ``adcp-client-python-bxu``'s fixture adapted to the defect THIS gate reports: an
    ``Optional[Literal[...]]`` dispatch key, which is ``82m.23``.

    ``rooted/under.py`` beside it is what says the loss was never recursion:
    ``walk_packages`` descends into ``rooted`` whatever the caller does with its ``ispkg``
    entry, and ``plain.py`` is the control for a module that is not under a package at all.
    Both are clean, so a reading that reported either would be red here too.

    **By behaviour and never by inspection**: nothing here reads :func:`_mixin_classes`'
    source or asks how it walks.  The claim is that a known package module's classes are
    REACHED, and what says so is a dispatch failure reported from inside one.
    """
    tree = tmp_path / "a_tree_with_a_package_root"
    (tree / "rooted").mkdir(parents=True)
    (tree / "__init__.py").write_text("")  # the tree's own root, as ``emit.write`` writes it
    (tree / "rooted" / "__init__.py").write_text(
        _A_UNION.format(stem="Rooted", branch_one='Optional[Literal["one"]] = None')
    )
    (tree / "rooted" / "under.py").write_text(
        _A_UNION.format(stem="Under", branch_one='Literal["one"]')
    )
    (tree / "plain.py").write_text(_A_UNION.format(stem="Plain", branch_one='Literal["one"]'))

    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    try:
        classes = _mixin_classes(importlib.import_module(tree.name))

        # **THE DEFECT IN THE PACKAGE ROOT IS REPORTED.**  Every class of that union
        # raises, because ``_branch_adapter`` is inherited -- the three names a consumer
        # meets, which is what the gate above collects rather than raising.  The two clean
        # modules are reached and report nothing, which is the control: ``rooted.under``
        # says the screen never cost recursion.  With the ``ispkg`` screen restored this
        # set is EMPTY and the gate above is still green.
        raised = _dispatch_failures(classes)
        assert set(raised) == {
            f"{tree.name}.rooted.RootedBase",
            f"{tree.name}.rooted.RootedOne",
            f"{tree.name}.rooted.RootedTwo",
        }, raised
        assert all("needs field 'kind' to be of type `Literal`" in why for why in raised.values()), (
            raised
        )

        # **AND THE WHOLE TREE WAS READ**, as an equality between two derivations and not
        # a count (``tests/test_every_check_names_its_set.py``'s first rule): every
        # qualified name the reading bound, against every ``class`` statement of the
        # fixture's own text.  With the screen restored this is short by the three
        # ``rooted/__init__.py`` declares -- which is ``brand/__init__.py``'s 111, in
        # miniature.
        declared = {
            f"{tree.name}.{'.'.join(path.relative_to(tree).with_suffix('').parts).removesuffix('.__init__')}"
            f".{line.removeprefix('class ').split('(')[0]}"
            for path in sorted(tree.rglob("*.py"))
            for line in path.read_text().splitlines()
            if line.startswith("class ")
        }
        assert set(classes) == declared, (sorted(classes), sorted(declared))
    finally:
        for name in [n for n in sys.modules if n == tree.name or n.startswith(f"{tree.name}.")]:
            del sys.modules[name]


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
#:
#: **THE SITES ARE UNCHANGED AND THE SYMBOLS MOVED, which is §3a step 3 and not a
#: relaxation of this row** (``adcp-client-python-5tf``).  Both of these positions
#: derived the bare name ``Account`` from their own property KEY, and
#: ``core/account.json`` is titled "Account" -- so the name claimed a subject the
#: bundle had already given to another document's root.  "A position has a role, an
#: entry has a subject, and only a subject gets a name": the role word now lengthens
#: by §4's own ancestor axis, and what this row asserts about the two sites is
#: untouched.  The symbol is still read off the module rather than derived here, so a
#: future move reddens at this pin rather than silently grading another class.
ACCOUNT_RESTATEMENTS = (
    ("media-buy/buy-products-request.json", "#/anyOf/1/properties/account",
     "adcp.types._schemas.media_buy.buy_products_request", "BuyProductsRequestBranch1Account"),
    ("media-buy/request-proposals-request.json", "#/anyOf/1/properties/account",
     "adcp.types._schemas.media_buy.request_proposals_request",
     "RequestProposalsRequestAccountAccount"),
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


# --------------------------------------------------------------------------- #
# adcp-client-python-jgsf: a union's refusal names WHERE, and not only THAT
# --------------------------------------------------------------------------- #
#: A value no scalar position admits, and a MAPPING rather than a bare sentinel on
#: purpose: it survives a JSON round trip, so the same perturbation reaches
#: ``model_validate`` and ``model_validate_json``, and pydantic refuses it for a
#: ``str``/``int``/``float``/``bool`` field with that field's own kind
#: (``string_type``, ``int_type``, ...) at that field's own position -- which is the
#: position this reading is about.  A bare ``object()`` would refuse identically and
#: could not be written down as a document.
A_VALUE_NO_SCALAR_ADMITS = {"__not_a_scalar__": True}

#: **THE CEILING ON THE CELL THAT WOULD OTHERWISE ABSORB A REGRESSION**, read off the
#: run's own census and stated here because a cell a check may grow into is a cell a
#: check can hide in.  These are the branch positions whose arms each object to a
#: DIFFERENT field the payload does carry and share none, so there is no position they
#: agree on and the object itself is the answer -- reading 3's keyless case.  A ceiling
#: and not an equality (``tests/test_every_check_names_its_set.py``): the number may
#: only FALL, and nothing is exempted for being in it.
#:
#: **THAT IT IS READING 3's KEYLESS CASE IS MEASURED AND NOT ASSUMED: all of them carry
#: an EMPTY** :attr:`~adcp.types._base.BranchDispatchMixin._BRANCH_DISCRIMINATOR` -- eight
#: documents' worth, ``core/audience-selector.json``'s three alternative-key arms,
#: ``media-buy/build-creative-response.json``'s four, ``brand.json``'s two,
#: ``compliance/comply-test-controller-response.json``'s two (one arm's ``literal_error``
#: at ``('status',)`` against another's ``int_type`` at ``('total_count',)``) and the
#: account references.  A KEYED union landing here would be a position the discriminator
#: names and the dispatch did not report, which is why the ceiling exists rather than a
#: carve-out.
CELL_CEILING = 18


def _scalar_leaves(value: Any, path: tuple[int | str, ...] = ()) -> list[tuple[int | str, ...]]:
    """Every position in ``value`` holding a scalar, as a pydantic ``loc``.

    A ``loc`` and not a JSON pointer, because the thing being compared is the ``loc`` a
    refusal reports: a list index is an ``int`` there and a property is a ``str``, which
    is the same spelling ``ValidationError.errors()`` uses and so needs no translation at
    the comparison.
    """
    if isinstance(value, Mapping):
        out: list[tuple[int | str, ...]] = []
        for key in value:
            out += _scalar_leaves(value[key], (*path, key))
        return out
    if isinstance(value, (list, tuple)):
        out = []
        for index, item in enumerate(value):
            out += _scalar_leaves(item, (*path, index))
        return out
    return [path] if path else []


def _deepest_leaf(value: Any) -> tuple[int | str, ...] | None:
    """The scalar position FURTHEST from the root, or ``None`` where there is none.

    Deepest because nesting is the case this reading earns its keep on: a repair that
    prepends the dispatch's own position and loses the branch's inner path is right on a
    one-level union and wrong on ``('packages', 0, 'targeting_overlay',
    'geo_countries', 0)``, and a shallow witness cannot tell the two apart.  Ties are
    broken by the path itself so the witness is the same on every run and in every lane.
    """
    leaves = _scalar_leaves(value)
    if not leaves:
        return None
    return max(leaves, key=lambda p: (len(p), [str(s) for s in p]))


def _replaced_at(value: Any, path: tuple[int | str, ...], put: Any) -> Any:
    """``value`` with ``path`` holding ``put``, copied rather than mutated.

    Copied because the committed floor's instance is shared with
    :func:`test_a_payload_the_document_admits_dispatches_to_the_branch_it_was_drawn_from`
    through ``held.Store``'s own cache, and a perturbation that wrote through it would
    silently change what that clause grades.
    """
    if not path:
        return put
    head, rest = path[0], path[1:]
    if isinstance(value, Mapping):
        return {k: (_replaced_at(v, rest, put) if k == head else v) for k, v in value.items()}
    return [
        (_replaced_at(item, rest, put) if index == head else item)
        for index, item in enumerate(value)
    ]


def _document_path(loc: tuple[int | str, ...], payload: Any) -> tuple[int | str, ...]:
    """A reported ``loc`` reduced to the positions the PAYLOAD actually has.

    **Pydantic interleaves an arm label at every union it reports THROUGH, and the label
    can land anywhere along the path -- not only in front.**  Measured on this tree:
    ``core/package-signal-targeting.json`` reports a broken ``signal_ref.signal_id`` at
    ``('binary', 'signal_ref', 'data_provider', 'signal_id')`` -- the outer tag in front
    AND an inner branch's own name in the middle -- ``core/placement-selection.json`` at
    ``('selected', 'placement_refs', 0, 'function-after[_enforce_adcp_rules(),
    PlacementRefsItem]', 'publisher_domain')``, ``core/assets/asset-union.json`` at
    ``('card', 'media', 'function-after[_enforce_adcp_rules(), ImageAsset]', 'width')``,
    and the same document at ``('daast_tracker', 'url', 'str')`` and
    ``(..., 'constrained-str')`` for the three arms of one ``url`` field's own union.  A
    rule that tolerated one LEADING label read all of those as the wrong position.

    So the label is IDENTIFIED rather than counted, and by the payload rather than by its
    spelling: a segment that INDEXES the value at hand is a document step, and one that
    does not is pydantic's own word for an arm.  Nothing here matches on
    ``function-after[``, ``tagged-union[`` or a capitalised name -- the heuristic
    upstream's own error narrowing uses, and the one whose residual edge case this
    reduction does not have -- because the payload answers the question exactly.

    **ONE AMBIGUITY IS REAL AND IS RESOLVED BY WHICH READING CONSUMES THE WHOLE ``loc``.**
    A TAGGED union's arm label is the tag VALUE, and a tag value can be spelled the same
    as a property of the object it tags: ``core/vendor-pricing-option.json`` reports a
    broken ``pricing_option_id`` at ``('cpm', 'pricing_option_id')`` on a payload that
    HAS a ``cpm`` key, so reading ``cpm`` as a document step walks into it and then
    cannot find ``pricing_option_id``.  The reading that treats the first segment as the
    label consumes every segment it is given; the other does not, and a reduction that
    accounts for the whole ``loc`` is the one that describes it.
    """

    def walked(steps: tuple[int | str, ...]) -> tuple[int | str, ...]:
        at = payload
        out: list[int | str] = []
        for step in steps:
            indexes = (isinstance(at, Mapping) and step in at) or (
                isinstance(at, (list, tuple)) and isinstance(step, int) and step < len(at)
            )
            if indexes:
                out.append(step)
                at = at[step]
        return tuple(out)

    best: tuple[int | str, ...] = ()
    for drop in (0, 1):
        got = walked(loc[drop:])
        if got and len(got) == len(loc) - drop:
            return got
        if len(got) > len(best):
            best = got
    return best


def _locates(path: tuple[int | str, ...], fault: tuple[int | str, ...]) -> bool:
    """Does a reduced document path name the position the perturbation put the fault at?

    ``()`` never does: "somewhere in your request" is the defect
    ``adcp-client-python-jgsf`` is about.  Anything else counts if it is the fault's own
    position, an ANCESTOR of it -- the union refused the containing object rather than the
    leaf, which still sends the caller to a field of theirs -- or UNDER it, which a fault
    at a scalar leaf makes reachable only through a union inside that very field.
    """
    shared = min(len(path), len(fault))
    return bool(path) and path[:shared] == fault[:shared]


def test_a_union_refusal_names_the_position_it_refuses_at() -> None:
    """``adcp-client-python-jgsf``: a union that refuses a payload says WHERE.

    **THE REQUIREMENT IS READING 3's AND IS OLDER THAN THE SUITE THAT CAUGHT IT.**  A
    union is emitted as a base and one class per branch (§4) *precisely so that a caller
    learns which field was wrong*, so a refusal that reports the combinator at the root
    and discards the path has thrown away the thing the structure was built to carry.
    Measured before the repair: ``BranchDispatchMixin._no_branch`` reported the combinator
    at ``loc=()`` for EVERY union in the tree and ``_undetermined`` did the same, so a
    caller was told the request was invalid and not where.

    **THE POSITION IS A WIRE FACT AND NOT A DIAGNOSTIC.**  ``core/error.json`` types
    ``Error.field`` as a JSONPath-lite pointer and an error narrowing derives it from the
    pydantic ``loc``, so an empty ``loc`` publishes an empty ``Error.field`` on the wire.

    **THE SET IS THE EMITTED TREE AND NOT A LIST OF UNIONS, which is the only way this
    covers a union no other test exercises.**  Every base the tree emits that declares a
    branch list is offered a payload, and the payload is DERIVED: the committed accepts
    floor's instance at the branch's own pointer -- the same witness
    :func:`test_a_payload_the_document_admits_dispatches_to_the_branch_it_was_drawn_from`
    grades, so neither clause can pass on a witness the other does not see -- with its
    DEEPEST scalar position replaced by :data:`A_VALUE_NO_SCALAR_ADMITS`.  Deepest, so
    the witness is a nested path wherever the instance has depth, which is where a repair
    that prepends the dispatch's own position but drops the branch's inner path shows up.

    **THE SCREEN IS THE DOCUMENT'S AND NOT THIS FILE'S.**  A perturbation the DOCUMENT
    still admits did not bite -- the position is typed ``{}`` or the branch ignores it --
    and nothing follows about a refusal that never happened, so those positions are named
    in their own cell.  Of the ones the document refuses, a base that ADMITS the payload
    anyway is laxer than its document, which is ``adcp-client-python-9iee`` and not this
    reading; it is counted and named, and this clause asserts over the refusals.

    **WHAT IS ASSERTED IS THAT NO REFUSAL NAMES THE WRONG POSITION, and the two other
    outcomes are CELLS.**  A refusal reporting a non-empty position that is neither the
    fault nor an ancestor of it sends a caller to a field that is not wrong, which is
    worse than reporting none, and that is the hard failure.  A refusal reporting the
    fault or an ancestor of it is the requirement held.  A refusal reporting the OBJECT is
    reading 3's own keyless case -- the arms each object to a different field the payload
    does carry and share none, so there is no position to name and the document
    determines no branch to prefer one by -- and it is counted in its own named cell
    rather than asserted away.  An ancestor counts as a location because it is one a
    caller can act on; the EXACT pointer is pinned by
    :func:`test_a_union_refusal_names_a_nested_position_through_a_list_and_a_model`, and
    the division of labour between the two is what
    ``perturb_the_union_location.sh`` demonstrates case by case.

    **NO CENSUS IS ASSERTED AS AN EQUALITY** (``tests/test_every_check_names_its_set.py``),
    so the non-vacuity defence is :func:`claimed` and :func:`partitions`: every branch
    position is offered-or-unheld, every offered position is bitten-or-not, and every
    bitten position is refused-or-admitted by the base.  Pointing
    ``codegen.held.COMMITTED`` at a directory that is not there takes this clause from
    green to ``empty set of nodes``.
    """
    bases = _declaring_bases()
    graded_bases = claimed("emitted union bases declaring a branch list", bases)
    records = _records()
    identities = catalogue.admitted_identities(BUNDLE, stated=harness.stated_instances)
    floor = held.Store(held.COMMITTED)

    positions: set[tuple[str, str]] = set()
    offered: set[tuple[str, str]] = set()
    unheld: set[tuple[str, str]] = set()
    the_document_still_admits_it: set[tuple[str, str]] = set()
    bitten: set[tuple[str, str]] = set()
    the_base_admits_what_its_document_refuses: set[tuple[str, str]] = set()
    named_the_position: set[tuple[str, str]] = set()
    the_arms_share_no_position: set[tuple[str, str]] = set()
    bases_that_named_a_position: set[str] = set()
    nameless: dict[str, tuple[str, str, str]] = {}
    for name in sorted(graded_bases):
        base = bases[name]
        for branch in base.__dict__["_branch_models"]:
            ref = branch.__dict__["__adcp_schema__"]
            site = (ref.document, ref.pointer)
            positions.add(site)
            key = harness.corpus_key(
                {
                    "document": ref.document,
                    "pointer": ref.pointer,
                    "admits": identities.get(ref.document),
                },
                custom_formats=harness.FORMAT_STRATEGIES,
            )
            drawn = (floor.get(key) or [None])[0]
            fault = None if drawn is None else _deepest_leaf(drawn)
            if fault is None:
                # No held instance, or one with no scalar position to perturb: there is
                # no witness here and this clause says nothing about the position.
                unheld.add(site)
                continue
            offered.add(site)
            payload = _replaced_at(drawn, fault, A_VALUE_NO_SCALAR_ADMITS)
            root = records[ref.document]
            if not _admits(root, "#", payload):
                the_document_still_admits_it.add(site)
                continue
            bitten.add(site)
            try:
                base.model_validate(payload)
            except ValidationError as why:
                rows = why.errors()
            else:
                the_base_admits_what_its_document_refuses.add(site)
                continue
            paths = [_document_path(tuple(row["loc"]), payload) for row in rows]
            if any(_locates(path, fault) for path in paths):
                named_the_position.add(site)
                bases_that_named_a_position.add(name)
            elif all(not path for path in paths):
                # **READING 3's OWN KEYLESS CASE, and the cell is named rather than
                # asserted away.**  These are the unions whose arms each object to a
                # DIFFERENT field the payload does carry and share none -- measured on
                # ``compliance/comply-test-controller-response.json``'s eight keyless
                # branches, where one arm's ``literal_error`` is at ``('status',)`` and
                # another's ``int_type`` is at ``('total_count',)``.  There is no position
                # the branches agree on, the document determines no branch to prefer one
                # of them by, and picking either is the guess reading 3 forbids.  So the
                # object itself is the position, which is where upstream's own group
                # validator reports the same refusal.
                the_arms_share_no_position.add(site)
            else:
                # A NON-EMPTY position that is not the fault's and not an ancestor of it
                # is WORSE than none: it sends the caller to a field that is not wrong.
                nameless[f"{name} <- {branch.__name__}"] = (
                    ref.document,
                    ref.pointer,
                    (
                        "refused and named the WRONG position: fault at "
                        f"{fault!r}, reported {[tuple(row['loc']) for row in rows]!r}, "
                        f"which reduces to {paths!r}"
                    ),
                )
    assert nameless == {}, nameless
    claimed("branch positions a union base names", positions)
    partitions(positions, offered=offered, unheld=unheld)
    partitions(
        offered,
        bitten=bitten,
        the_document_still_admits_the_perturbation=the_document_still_admits_it,
    )
    partitions(
        bitten,
        named_the_position=named_the_position,
        the_arms_share_no_position_the_payload_has=the_arms_share_no_position,
        the_base_admits_what_its_document_refuses=the_base_admits_what_its_document_refuses,
    )
    claimed("branch positions whose refusal named the position", named_the_position)
    claimed("union bases whose refusal named a position", bases_that_named_a_position)
    # **AND THE CELL IS CEILINGED, BECAUSE A CELL THAT GROWS ABSORBS A REGRESSION.**
    # Measured: with ``_common_position`` returning ``()`` instead of the position every
    # arm names, the sites whose position came from IT move out of
    # ``named_the_position`` and into this cell -- and the partition above still holds,
    # so the clause would read green on a dispatch that had lost half the repair.  A
    # ceiling at the measured truth is what sees that; it is not a budget, because the
    # number may only FALL and nothing is exempted for being here.
    ratchet(
        "branch positions whose arms share no position the payload has",
        len(the_arms_share_no_position),
        at_most=CELL_CEILING,
        because=(
            "a union whose arms each object to a different field the payload DOES carry "
            "has no position they agree on, which is reading 3's keyless case; the count "
            "falls when a union gains a discriminator its document guarantees, and it "
            "RISES only when the dispatch stops naming a position it could have named"
        ),
    )


#: The path the requirement is stated over, and upstream's own assertion: their
#: ``test_direct_validation_error_uses_request_document_path`` offers ``create_media_buy``
#: a package whose ``targeting_overlay.geo_countries`` holds a number and asserts the
#: refusal is reported HERE.  Three levels and two list indices, which is the shape a
#: repair that only prepends the dispatch's own position gets wrong.
A_NESTED_FAULT = ("packages", 0, "targeting_overlay", "geo_countries", 0)


def test_a_union_refusal_names_a_nested_position_through_a_list_and_a_model() -> None:
    """The requirement's hard case, written out: a fault three levels under the union.

    ``core/create-media-buy-request.json`` is an ``anyOf`` of three branches and the
    class a consumer holds is the BASE, so every payload offered to it goes through
    :meth:`adcp.types._base.BranchDispatchMixin._dispatch`.  The fault is at
    :data:`A_NESTED_FAULT` -- into a list, into a nested model, into another list -- and
    all three branches report it at that same position while two of them ALSO report the
    fields only they require (``total_budget``/``budget_allocation``,
    ``proposal_id``/``total_budget``).  So the refusal is the intersection: the one error
    the branches agree on, at the pointer they agree on, which is the error upstream's own
    class raises for the same payload.

    **AND THE SECOND HALF IS THE PREPEND, which the one-level case cannot see.**  The
    same base reached through an enclosing list field must report the enclosing path AND
    keep the branch's inner one, so the assertion below is made twice: at the root, and
    under a ``list[...]`` field of another model.
    """
    cls = importlib.import_module(
        "adcp.types._schemas.media_buy.create_media_buy_request"
    ).CreateMediaBuyRequest
    assert cls.__dict__.get("_branch_models"), "the row is about a DISPATCHING base"
    payload = {
        "adcp_version": "3.2",
        "idempotency_key": "targeting-error-1181",
        "account": {"account_id": "account-1"},
        "brand": {"brand_id": "brand_1", "domain": "brand.example"},
        "start_time": "2026-10-01T00:00:00Z",
        "end_time": "2026-10-31T00:00:00Z",
        "packages": [
            {
                "product_id": "product-1",
                "pricing_option_id": "price-1",
                "budget": 1000,
                "targeting_overlay": {"geo_countries": [123]},
            }
        ],
    }
    with pytest.raises(ValidationError) as refused:
        cls.model_validate(payload)
    assert refused.value.errors(include_input=False, include_context=False, include_url=False) == [
        {
            "type": "string_type",
            "loc": A_NESTED_FAULT,
            "msg": "Input should be a valid string",
        }
    ]

    class Enclosing(BaseModel):
        requests: list[cls]  # type: ignore[valid-type]

    with pytest.raises(ValidationError) as nested:
        Enclosing.model_validate({"requests": [payload]})
    assert [tuple(row["loc"]) for row in nested.value.errors()] == [("requests", 0, *A_NESTED_FAULT)]


#: Offered at a scalar position to find the payloads that reach
#: :meth:`adcp.types._base.BranchDispatchMixin._undetermined` -- the keyless screen, which
#: fires where a branch CLASS admits a payload its own node REFUSES (reading 2's declared
#: widenings).  Three generic values and no document knowledge: ``""`` and ``"0"`` violate
#: the ``minLength``, ``pattern``, ``format`` and ``enum`` a widened annotation does not
#: carry, and ``"not-a-value"`` violates a ``const``.  **Which of them lands is MEASURED
#: and not assumed**: a payload counts only once the document has refused it and the
#: screen has answered, so a value that reaches neither contributes nothing rather than a
#: false witness.
A_VALUE_A_WIDENED_CLASS_STILL_ADMITS = ("", "0", "not-a-value")


def test_a_keyless_dispatch_refusal_names_the_position_the_document_refuses_at() -> None:
    """``adcp-client-python-jgsf``, over :meth:`BranchDispatchMixin._undetermined`.

    **A GOOD SENTENCE IS NOT A LOCATION, and that screen's sentence is very good**: it
    names the branch a structural first match reached, says the union states no
    discriminator its document guarantees, and quotes the document's own reason.  That
    is exactly why it was allowed to carry ``loc=()`` for as long as it did.  A caller
    handed "no branch is determined" with an empty ``loc`` is no better off than one
    handed a type error with an empty ``loc``, because ``core/error.json``'s
    ``Error.field`` is derived from the ``loc`` and is empty either way.  Reading 3 now
    says so: "the message and the location are separate obligations and neither excuses
    the other".

    **AND THE 84a9 WITNESS CANNOT SEE IT, which is why this clause exists beside that
    one.**  Measured: the four payloads
    :func:`test_a_keyless_dispatch_refuses_rather_than_answering_with_a_branch_the_document_refuses`
    is about are each refused by the document at the ROOT, on ``'errors' is a required
    property`` or ``'products' is a required property``, so the document's own pointer
    for them IS ``()`` and a dispatch that discarded the pointer and one that reports it
    give the same answer.  A perturbation of ``_undetermined``'s ``loc`` therefore reads
    GREEN against that row, which is the worthless-guard shape.

    So the witnesses are DERIVED: every keyless base's branch position that the committed
    floor answers for, with a scalar position replaced by one of
    :data:`A_VALUE_A_WIDENED_CLASS_STILL_ADMITS`, keeping only the payloads where the
    DOCUMENT refuses and the screen answers.

    The deepest positions are tried first and the search stops at the first witness per
    branch position, so the cost is bounded by the positions and not by the product.
    """
    bases = {n: c for n, c in _declaring_bases().items() if not c._BRANCH_DISCRIMINATOR}
    graded = claimed("emitted union bases with NO dispatch key", bases)
    records = _records()
    identities = catalogue.admitted_identities(BUNDLE, stated=harness.stated_instances)
    floor = held.Store(held.COMMITTED)

    reached: set[tuple[str, str]] = set()
    named_the_position: set[tuple[str, str]] = set()
    nameless: dict[str, tuple[str, str, str]] = {}
    for name in sorted(graded):
        base = bases[name]
        for branch in base.__dict__["_branch_models"]:
            ref = branch.__dict__["__adcp_schema__"]
            site = (ref.document, ref.pointer)
            key = harness.corpus_key(
                {
                    "document": ref.document,
                    "pointer": ref.pointer,
                    "admits": identities.get(ref.document),
                },
                custom_formats=harness.FORMAT_STRATEGIES,
            )
            drawn = (floor.get(key) or [None])[0]
            if drawn is None:
                continue
            root = records[ref.document]
            leaves = sorted(_scalar_leaves(drawn), key=lambda p: (-len(p), [str(s) for s in p]))
            for leaf in leaves[:3]:
                for put in A_VALUE_A_WIDENED_CLASS_STILL_ADMITS:
                    payload = _replaced_at(drawn, leaf, put)
                    if not _admits(root, "#", payload):
                        continue  # the document admits it: nothing for the screen to do
                    try:
                        base.model_validate(payload)
                    except ValidationError as why:
                        rows = why.errors()
                    else:
                        continue  # no refusal at all, which is adcp-client-python-9iee
                    if not any("no discriminator" in row["msg"] for row in rows):
                        continue  # refused by a branch or by the combinator, not the screen
                    reached.add(site)
                    paths = [_document_path(tuple(row["loc"]), payload) for row in rows]
                    if any(_locates(path, leaf) for path in paths):
                        named_the_position.add(site)
                    else:
                        nameless[f"{name} <- {branch.__name__}"] = (
                            ref.document,
                            ref.pointer,
                            (
                                "the keyless screen refused and named no position: "
                                f"document refuses at {leaf!r}, reported "
                                f"{[tuple(row['loc']) for row in rows]!r}"
                            ),
                        )
                    break
                if site in reached:
                    break
    assert nameless == {}, nameless
    claimed("branch positions whose keyless dispatch reached the undetermined screen", reached)
    partitions(reached, named_the_position=named_the_position)
