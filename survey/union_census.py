"""Every ``oneOf`` and every ``anyOf`` of the bundle, against the class we emit at it.

ONE ROW PER KEYWORD OCCURRENCE, not per node: a node stating both combinators states two
unions and ``codegen/intersect.py`` already reads it that way ("a node stating both
``oneOf`` and ``anyOf`` is two unions"), so a per-node count would hide one of them.
Measured over bundle 3.2 the two sets are disjoint -- 212 ``oneOf`` and 443 ``anyOf``
occurrences at 655 distinct nodes of the 1,054 documents ``codegen.bundle.portable``
publishes -- so for THIS bundle the two counts coincide; the row is per occurrence anyway
because the coincidence is a measurement and not a rule.

**WHY THE PROJECTIONS ARE OUT AND WHAT LEAVING THEM IN WOULD COST.**  ``bundled/`` and
``mcp/`` (``codegen.bundle.PROJECTIONS``) are the same nodes re-cut for one transport, so
a census over them counts one union once per transport that carries it.  Measured: 568
projection documents hold 14,272 further ``>=2``-branch occurrences, 21.8x the 656 here,
and not one of them is a node this compiler emits a class from.  That is the whole of the
exclusion -- a double count, not a judgment about the projections.

**THE REGISTRY FILES ARE IN, and one of them carries a union.**  ``index.json``,
``manifest.json`` and ``manifest.schema.json`` describe the bundle rather than a message,
which is why ``bundle.portable`` drops them from the EMISSION population; this census is
over the bundle's ``*.json`` files outside the projections, so they are counted here and
``manifest.schema.json#/properties/tasks/additionalProperties`` is the one union among
them.  It lands in ``C`` -- object-ish ``oneOf``, no class -- which is the correct and
uninteresting answer: nothing emits from a registry file, so 655 of the 656 rows come from
documents and 1 comes from a file that is not one.  Reported separately by
``--summary`` (``from_documents`` / ``from_registry``) so neither reading has to be
reconstructed from the table.

**OBJECT-ISH IS A PROPERTY OF THE OCCURRENCE AND THE THRESHOLD IS TWO.**  A branch is
object-ish when it carries ``properties``, ``required`` or ``$ref``, or states
``type: "object"``.  An OCCURRENCE is object-ish when AT LEAST TWO of its branches are,
and the threshold is two rather than one because one is not a union of objects: a
``oneOf`` of ``[{"$ref": X}, {"type": "null"}]`` has one object-ish branch and legitimately
becomes ``X | None``, an annotation and not a class.  Measured over the 656: 625
occurrences have at least one object-ish branch, 549 have at least two, 541 have all
branches object-ish.  549 is the denominator the buckets partition; the other 107 are
``G``.

**THE A/B DISCRIMINANT IS A BRANCH CHILD, NOT ANY CHILD**, and that is the one measurement
that moved a bucket.  ``core/creative-asset.json#`` and ``core/creative-manifest.json#``
each emit a single FLATTENED class whose root ``oneOf`` became a ``PresenceGroups`` rule --
no ``BranchDispatchMixin``, no ``_BRANCH_DISCRIMINATOR``, no branch class -- and yet
``CreativeAsset`` has three subclasses and ``CreativeManifest`` one.  Those children sit at
OTHER documents (``media_buy/package_request.CreativesItem``,
``creative/sync_creatives_request.CreativesItem``,
``core/creative_representation.CreativeRepresentation``): they extend the class through a
``$ref``, which is the hierarchy claim working, and they are not arms of this union.
Keying ``A`` on "has a subclass" therefore reports these two as discriminated unions when
they are flattenings, which is exactly the thing bucket ``B`` exists to name.  So a CHILD
column is recorded in full, and the bucket reads only the children whose own
``__adcp_schema__`` pointer is a BRANCH pointer of this occurrence (``<pointer>/oneOf/<i>``).
With that key: ``A=115, B=9, D=16, E=68``.  With "any child": ``A=117, B=7, D=29, E=55``, and
the 13 ``anyOf`` occurrences that move are the same mistake thirteen times over --
``core/attestation-reference.json#`` is flattened into one ``AttestationReference`` and
four classes extend it from three other documents, ``core/frequency-cap.json#`` is
flattened and ``MediaBuyFrequencyCap`` extends it, and so on through ``signal-targeting``,
``forecast-range`` and ``outcome-target``.  Not one of those children sits at an ``anyOf``
branch pointer of the union it is credited to.

**AND A BUCKET NAME IS NOT THE WHOLE ANSWER FOR ``C`` AND ``F``.**  "No class at that
pointer" is a fact about the POINTER, and 37 of ``C``'s 54 and 17 of ``F``'s 287 emit a
class at a BRANCH pointer while emitting nothing at the union's own -- arms with no base.
What stands at the union there is an ANNOTATION: ``content-standards/artifact.json``'s
``#/$defs/asset_access`` emits ``AssetAccessBearerToken``, ``AssetAccessServiceAccount`` and
``AssetAccessSignedUrl``, each deriving ``AdCPBaseModel`` directly, and binds
``AssetAccess = Annotated[A | B | C, Field(...)]`` at module scope.  So the arms exist and
nothing of OURS says they are alternatives to each other: there is no root for reading 3's
"every union root dispatches" to range over, and the hierarchy claim's "union branches
inherit the union base" has no base at those 54 nodes.  Whether an annotation discharges
either reading is not this table's call; the ``arm_classes`` column carries the fact so the
distinction is in the table and not only in this paragraph, and ``--summary`` splits it
under ``C_and_F_with_arms_and_no_base``.  The remaining 17 + 270 emit nothing at the
pointer and nothing at any branch of it.

**AND ``F=287`` IS NOT 287 MISSING CLASSES, WHICH THE ``position`` COLUMN IS THERE TO SAY.**
By the POSITION ``bundle.nodes_at`` assigns -- §6's, assigned from the keyword descended
through and never read off the pointer -- ``F`` splits ``RULE 237, PROP 18, CONJ 12,
DEF 11, ELEM 4, BRANCH 3, MAPV 2``.  At ``RULE`` and ``CONJ`` the union sits inside a
``not``, an ``if``/``then``/``else`` or an ``allOf`` conjunct, where it compiles to a
cross-field rule on the ENCLOSING class and a class at its own pointer would be the defect
rather than the repair; 249 of the 287 are there.  38 are at a position where a class is
the question.  ``C`` splits ``ELEM 26, PROP 21, DEF 4, CONJ 3``, so 51 of its 54 are.

The seven buckets, which partition the 656::

    A  oneOf, object-ish, base + branch children emitted
    B  oneOf, object-ish, FLATTENED -- a class at the pointer, no branch child
    C  oneOf, object-ish, NO class at that pointer
    D  anyOf, object-ish, base + branch children emitted
    E  anyOf, object-ish, FLATTENED
    F  anyOf, object-ish, NO class at that pointer
    G  not object-ish -- fewer than two object-ish branches

``A`` is NOT keyed on the discriminator either, and the split inside it is the finding
worth carrying out of this table: of the 115, only 77 carry a non-empty
``_BRANCH_DISCRIMINATOR``.  The other 38 are a base with branch children and no key a
caller can read to learn which arm they hold -- ``tools/parity/census.py``'s
``undiscriminated`` row, measured here against the document that caused it.  A bucket keyed
on the discriminator would have put those 38 somewhere they do not belong and would have
left ``A`` and ``B`` not partitioning the 124 object-ish ``oneOf`` occurrences that emit a
class.

**``dispatch_mixin`` IS INHERITED AND THE COLUMN SAYS SO RATHER THAN HIDING IT.**  It is
``issubclass(cls, BranchDispatchMixin)``, so a class that is itself an ARM of an outer
``oneOf`` reads ``yes`` whether or not anything dispatches the union in ITS own row --
``core/audience-selector.json#/oneOf/0`` and ``brand.json#/oneOf/2`` are the shape, five
rows of it, all in ``E``.  Reading the mixin off ``__dict__`` instead would answer "which
class declares the mixin", which is a different question and not the one a reader of this
column asks ("can this object dispatch at all").  The bucket is keyed on
``branch_children`` and not on this column for exactly that reason.

Run::

    PYTHONPATH=.:src ./.venv/bin/python survey/union_census.py \
        --bundle schemas/cache/3.2 --tsv survey/union-census-3.2.tsv

    PYTHONPATH=.:src ./.venv/bin/python survey/union_census.py \
        --bundle schemas/cache/3.2 --tsv survey/union-census-3.2.tsv --check

``--check`` rewrites nothing and exits non-zero when the committed table is not what the
bundle and the emitted tree now say, so the table is an ASSERTION and not a snapshot.
"""

from __future__ import annotations

import argparse
import collections
import functools
import importlib
import json
import pkgutil
import sys
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any, NamedTuple

from pydantic import BaseModel

from adcp.types._base import BranchDispatchMixin, SchemaRef
from codegen import bundle, keywords

#: The two combinator keywords this census is over.  ``allOf`` is a CONJUNCTION -- every
#: conjunct holds -- so it is not a union and has no branches to dispatch; ``not`` holds
#: one subschema.  Read as a literal pair rather than off ``bundle.COMPOSITION`` because
#: that tuple is "what holds subschemas in a list", which includes ``allOf``.
UNION_KEYWORDS = ("oneOf", "anyOf")

#: What makes a BRANCH object-ish.  ``$ref`` counts without being resolved: a reference
#: to a document of this bundle is a reference to an object in every case the bundle
#: holds, and resolving to decide would make the column depend on the reference's target
#: being reachable.  ``type: "object"`` is read separately because it is a VALUE and not
#: a key.
OBJECT_ISH_KEYS = ("properties", "required", "$ref")

#: An occurrence is object-ish with at least this many object-ish branches.  The module
#: docstring carries the reason and the measurement.
OBJECT_ISH_BRANCHES = 2

#: How far :func:`resolved` follows ``$ref`` before giving up.  A reference chain in this
#: bundle is at most three hops; the cap is what stops a cycle rather than a budget.
REFERENCE_HOPS = 8

@functools.cache
def read(bundle_dir: Path, document: str) -> dict:
    """``bundle.read`` with the parse memoised, because :func:`resolved` re-reads.

    A cache and not a second reader: the body is the one call.  ``const_keyed`` follows a
    ``$ref`` per branch per occurrence, which over the 656 rows reaches the same few
    hundred documents some thousands of times, and the census took minutes without this.
    """
    return bundle.read(bundle_dir, document)


COLUMNS = (
    "bucket",
    "document",
    "pointer",
    "keyword",
    "position",
    "branches",
    "object_ish_branches",
    "titled_branches",
    "schema_discriminator",
    "const_keyed_property",
    "classes",
    "branch_discriminator",
    "dispatch_mixin",
    "fields",
    "branch_children",
    "other_children",
    "arm_classes",
)


class Row(NamedTuple):
    """One keyword occurrence, the document's facts about it and ours."""

    bucket: str
    document: str
    pointer: str
    keyword: str
    position: str
    branches: int
    object_ish_branches: int
    titled_branches: int
    schema_discriminator: str
    const_keyed_property: str
    classes: str
    branch_discriminator: str
    dispatch_mixin: str
    fields: str
    branch_children: str
    other_children: str
    arm_classes: str

    def node(self) -> str:
        """``document#pointer``, the spelling a reader cites an occurrence by."""
        return f"{self.document}{self.pointer}"


# --------------------------------------------------------------------------- #
# the document side
# --------------------------------------------------------------------------- #
def documents(bundle_dir: Path) -> list[str]:
    """Every ``*.json`` of the bundle outside the projections, bundle-relative, sorted.

    NOT ``bundle.portable``, and the difference is the three registry files.  ``portable``
    answers "which documents does this bundle publish under their own identity", which is
    the EMISSION population; the census population is "every node of the bundle that is
    not a re-cut of another", which keeps ``manifest.schema.json`` in.  The module
    docstring says what that costs (one row, in ``C``) and why it is worth saying.
    """
    return sorted(
        str(path.relative_to(bundle_dir))
        for path in bundle_dir.rglob("*.json")
        if path.relative_to(bundle_dir).parts[0] not in bundle.PROJECTIONS
    )


def occurrences(
    bundle_dir: Path, document: str
) -> Iterator[tuple[str, dict, str, list, keywords.Position]]:
    """``(pointer, node, keyword, branches, position)`` for every ``>=2``-branch union here.

    The walk is ``bundle.nodes``, which is the compiler's own one (§11's one descent
    table), so this census cannot come to disagree with the emitter about what a schema
    POSITION is.  That matters for exactly the keys this census is named after: a document
    holding a PROPERTY called ``oneOf`` would be reported as a union by a blanket
    ``dict``-walk, and ``bundle.subschemas`` descends only where a subschema can legally
    appear.

    **THE POSITION COMES FROM ``nodes_at`` AND IS NEVER READ OFF THE POINTER**, which is
    §6's rule and ``bundle.nodes_at``'s own docstring ("the position is assigned from the
    structural keyword descended through, so no reader derives it from a pointer").  It
    earns the column: 287 of the 656 rows are bucket ``F``, and by POSITION the bulk of
    them are at ``RULE`` or ``CONJ`` -- inside a ``not``/``if``/``then``/``else`` or an
    ``allOf`` conjunct -- where a union compiles to a cross-field RULE and a class at the
    pointer would be wrong rather than missing.  A pointer scan for ``/not`` would also
    have called ``core/catchment.json#/oneOf/0/not`` a rule and ``formats/canonical/
    audio_vast.json#/not/anyOf/2/properties/media_file_requirements`` one too, and only one
    of those is.
    """
    for suffix, node, position in bundle.nodes_at(read(bundle_dir, document)):
        pointer = f"#{suffix}"
        for keyword in UNION_KEYWORDS:
            branches = node.get(keyword)
            if isinstance(branches, list) and len(branches) >= 2:
                yield pointer, node, keyword, branches, position


def object_ish(branch: object) -> bool:
    """Whether one BRANCH is object-ish.  :data:`OBJECT_ISH_KEYS` plus ``type: "object"``.

    A ``type`` stated as a LIST is read too -- draft-07 admits ``["object", "null"]`` -- so
    a nullable object branch is not missed on a spelling.  Measured over bundle 3.2 no
    branch spells one, so the arm changes no count here; it is written because the
    alternative is a column that is right by accident.
    """
    if not isinstance(branch, Mapping):
        return False
    if any(key in branch for key in OBJECT_ISH_KEYS):
        return True
    stated = branch.get("type")
    return stated == "object" or (isinstance(stated, list) and "object" in stated)


def resolved(
    bundle_dir: Path, document: str, known: frozenset[str], node: object, hops: int = 0
) -> tuple[dict[str, Any], frozenset[str]]:
    """``(properties, required)`` of one branch with ``$ref`` followed and ``allOf`` merged.

    Read ONLY by :func:`const_keyed`, which has to look inside a branch to answer whether
    the branches share a const-keyed property -- and in this bundle a union's arms are
    overwhelmingly ``{"$ref": ...}``, so a reader that stopped at the reference would
    report "no shared key" for every discriminated union the bundle has.

    Best-effort and never a refusal: a reference this bundle does not hold, a pointer
    naming no node and a cycle all come back as "nothing known here", because the caller's
    question is "is there a key EVERY branch keys on" and an unanswerable branch is already
    a no.  ``codegen.bundle.record`` is the inliner that may not be best-effort; this is a
    survey.
    """
    if hops > REFERENCE_HOPS or not isinstance(node, Mapping):
        return {}, frozenset()
    properties: dict[str, Any] = {}
    required: set[str] = set()
    held = node.get("properties")
    if isinstance(held, Mapping):
        properties.update(held)
    stated = node.get("required")
    if isinstance(stated, list):
        required.update(str(name) for name in stated)
    conjuncts = node.get("allOf")
    for inner in conjuncts if isinstance(conjuncts, list) else ():
        sub_properties, sub_required = resolved(bundle_dir, document, known, inner, hops + 1)
        properties.update(sub_properties)
        required |= sub_required
    reference = node.get("$ref")
    if isinstance(reference, str):
        head, fragment = bundle.split_ref(reference)
        target = document if head == "" else bundle.document_for(head, known)
        if target is not None:
            try:
                at: object | None = bundle.node_at(read(bundle_dir, target), fragment)
            except (KeyError, IndexError, TypeError, ValueError):
                at = None
            if at is not None:
                sub_properties, sub_required = resolved(bundle_dir, target, known, at, hops + 1)
                properties.update(sub_properties)
                required |= sub_required
    return properties, frozenset(required)


def _one_value(schema: object) -> bool:
    """Whether a property schema admits exactly one value: a ``const`` or a 1-long ``enum``.

    The two spellings of the same fact.  ``asset-union.json``'s arms key on
    ``asset_type``, and the bundle spells that selector both ways across its documents, so
    a reader of one spelling would answer "no discriminator" for the other half.
    """
    if not isinstance(schema, Mapping):
        return False
    if "const" in schema:
        return True
    stated = schema.get("enum")
    return isinstance(stated, list) and len(stated) == 1


def const_keyed(bundle_dir: Path, document: str, known: frozenset[str], branches: list) -> str:
    """The property EVERY object-ish branch pins to one value, or ``""``.

    This is the document's own answer to "is there a key a caller can read to learn which
    arm they hold", asked independently of whether we emitted a ``_BRANCH_DISCRIMINATOR``
    from it -- which is the comparison the census is for: a row with a const-keyed property
    and an empty ``_BRANCH_DISCRIMINATOR`` is a key the document states and we dropped.

    Over the OBJECT-ISH branches and not all of them, because a ``{"type": "null"}`` arm
    beside five objects keys on nothing and would veto every candidate.  Several keys
    qualifying is possible and the answer is then all of them, pipe-joined, in sorted
    order: naming one would be picking, and this column is read by a human.
    """
    candidates: list[frozenset[str]] = []
    for branch in branches:
        if not object_ish(branch):
            continue
        properties, _ = resolved(bundle_dir, document, known, branch)
        candidates.append(
            frozenset(name for name, schema in properties.items() if _one_value(schema))
        )
    if not candidates:
        return ""
    return "|".join(sorted(frozenset.intersection(*candidates)))


def schema_discriminator(node: Mapping) -> str:
    """OpenAPI's ``discriminator`` keyword, as the node spells it, or ``""``.

    draft-07 has no such keyword, so a node carrying one is carrying an OpenAPI
    annotation; the column exists so that "the document named the selector outright" is
    distinguishable in the table from "the branches happen to share a const-keyed
    property" (:func:`const_keyed`).  **Measured over bundle 3.2: 82 of the 656 nodes
    carry one**, including 26 in bucket ``C`` -- the document names the selector by name
    and we emit no class at the pointer at all -- so this is not the dead column it would
    be in a bundle that stuck to draft-07.

    Both spellings are read: ``{"propertyName": "x"}`` is OpenAPI's object form and a bare
    string is the shorthand some generators write.  An object form with no ``propertyName``
    comes back as the literal ``"discriminator"``, which says "the keyword is here and
    names no property" rather than silently reading as absent.
    """
    held = node.get("discriminator")
    if isinstance(held, Mapping):
        return str(held.get("propertyName", "")) or "discriminator"
    return str(held) if held else ""


# --------------------------------------------------------------------------- #
# our side
# --------------------------------------------------------------------------- #
def emitted() -> list[type[BaseModel]]:
    """Every class DECLARED by the emitted tree, in module order.

    DECLARATIONS and not names: the screen is ``value.__module__ == name``, which is
    ``tests/_imports_a_tree.py``'s, and it drops a re-export without dropping a class.
    ``__adcp_schema__`` is then read out of ``__dict__`` and never off the class, because
    a branch class INHERITS its base's and a ``getattr`` would key every arm of a union on
    the union's own pointer.

    ``walk_packages`` and no ``ispkg`` screen, for ``_imports_a_tree.py``'s recorded
    reason: a package ``__init__`` is a DOCUMENT's module under the layout rule, and
    screening those out loses the document's own classes.
    """
    import adcp.types._schemas as package

    out: list[type[BaseModel]] = []
    for name in sorted(i.name for i in pkgutil.walk_packages(package.__path__, package.__name__ + ".")):
        module = importlib.import_module(name)
        out.extend(
            value
            for value in vars(module).values()
            if isinstance(value, type) and issubclass(value, BaseModel) and value.__module__ == name
        )
    return out


def at_pointer(classes: list[type[BaseModel]]) -> dict[tuple[str, str], list[type[BaseModel]]]:
    """``(document, pointer)`` -> the classes DECLARING that ``__adcp_schema__``.

    A LIST and not one class, because the tree holds 17 pointers carrying two declarations
    and one carrying three (``creative/preview-render.json#/oneOf/0/properties/dimensions``).
    Collapsing them would make the census's own answer depend on module order, and
    ``perturb_two_classes_at_one_node.sh`` is the check that cares.
    """
    out: dict[tuple[str, str], list[type[BaseModel]]] = collections.defaultdict(list)
    for cls in classes:
        reference = cls.__dict__.get("__adcp_schema__")
        if isinstance(reference, SchemaRef):
            out[(reference.document, reference.pointer)].append(cls)
    return dict(out)


def children_of(classes: list[type[BaseModel]]) -> dict[type, list[type[BaseModel]]]:
    """Each class -> the classes NAMING IT as a direct base.

    ``__bases__`` and not ``__subclasses__``: the question is which classes name it, so a
    grandchild is the child's row and not this one's.
    """
    out: dict[type, list[type[BaseModel]]] = collections.defaultdict(list)
    for cls in classes:
        for base in cls.__bases__:
            out[base].append(cls)
    return dict(out)


def branch_pointers(pointer: str, keyword: str, count: int) -> frozenset[str]:
    """The pointers of one occurrence's branches: ``<pointer>/<keyword>/<i>``.

    The root's pointer is ``#`` and a nested one is ``#/properties/x``, so the join is a
    plain concatenation in both cases -- ``#`` + ``/oneOf/0`` is ``#/oneOf/0``, which is
    what ``core/assets/asset-union.json``'s arms carry.
    """
    return frozenset(f"{pointer}/{keyword}/{index}" for index in range(count))


# --------------------------------------------------------------------------- #
# the join and the buckets
# --------------------------------------------------------------------------- #
def bucket_of(
    keyword: str, object_ish_branches: int, *, has_class: bool, has_branch_child: bool
) -> str:
    """The one bucket a row is in.  The seven PARTITION every occurrence.

    Read in this order, which is the order the definitions nest: object-ish first (``G``
    is everything else and is decided before any class is looked at), then whether we
    emitted anything at the pointer at all, then whether what we emitted has ARMS.  Every
    row therefore gets exactly one bucket and no row gets none, which is the property the
    table is checked for (:func:`partitions`).
    """
    if object_ish_branches < OBJECT_ISH_BRANCHES:
        return "G"
    one_of = keyword == "oneOf"
    if not has_class:
        return "C" if one_of else "F"
    if has_branch_child:
        return "A" if one_of else "D"
    return "B" if one_of else "E"


def census(bundle_dir: Path) -> list[Row]:
    """The whole table, in ``(document, pointer, keyword)`` order."""
    known = frozenset(bundle.portable(bundle_dir))
    classes = emitted()
    index, children = at_pointer(classes), children_of(classes)
    rows: list[Row] = []
    for document in documents(bundle_dir):
        for pointer, node, keyword, branches, position in occurrences(bundle_dir, document):
            here = index.get((document, pointer), [])
            arms = branch_pointers(pointer, keyword, len(branches))
            #: THE ARMS, asked of the pointer index and not of the base's subclasses, which
            #: is how a bucket name stops being the whole answer: 37 of ``C``'s 54 and 17 of
            #: ``F``'s 287 emit a class AT A BRANCH POINTER while emitting nothing at the
            #: union's own.  Those are arms with no base -- nothing dispatches to them and
            #: nothing of ours states that they are alternatives -- and keying the column on
            #: ``__bases__`` alone would have reported them as "no class at that pointer"
            #: full stop, which is true of the pointer and false of the union.
            arm_classes = [cls.__name__ for arm in sorted(arms) for cls in index.get((document, arm), [])]
            branch_children, other_children = [], []
            for cls in here:
                for child in children.get(cls, []):
                    reference = child.__dict__.get("__adcp_schema__")
                    named = (
                        isinstance(reference, SchemaRef)
                        and reference.document == document
                        and reference.pointer in arms
                    )
                    (branch_children if named else other_children).append(child.__name__)
            count = sum(object_ish(branch) for branch in branches)
            rows.append(
                Row(
                    bucket=bucket_of(
                        keyword, count, has_class=bool(here), has_branch_child=bool(branch_children)
                    ),
                    document=document,
                    pointer=pointer,
                    keyword=keyword,
                    position=str(position),
                    branches=len(branches),
                    object_ish_branches=count,
                    titled_branches=sum(
                        1 for branch in branches if isinstance(branch, Mapping) and branch.get("title")
                    ),
                    schema_discriminator=schema_discriminator(node),
                    const_keyed_property=const_keyed(bundle_dir, document, known, branches),
                    classes="|".join(cls.__name__ for cls in here),
                    branch_discriminator="|".join(
                        cls.__dict__.get("_BRANCH_DISCRIMINATOR", "") or "-" for cls in here
                    ),
                    dispatch_mixin="|".join(
                        "yes" if issubclass(cls, BranchDispatchMixin) else "no" for cls in here
                    ),
                    fields="|".join(str(len(cls.model_fields)) for cls in here),
                    branch_children="|".join(sorted(branch_children)),
                    other_children="|".join(sorted(other_children)),
                    arm_classes="|".join(arm_classes),
                )
            )
    return sorted(rows, key=lambda row: (row.document, row.pointer, row.keyword))


def partitions(rows: list[Row]) -> dict[str, int]:
    """The bucket sizes, with every one of the seven present even at zero.

    Raises on a row in no bucket, which is the property the bucket set is for: a reader
    who adds an eighth name and forgets a row would otherwise get a table whose columns
    sum to less than its length and no complaint.
    """
    sizes = dict.fromkeys("ABCDEFG", 0)
    for row in rows:
        if row.bucket not in sizes:
            raise ValueError(f"{row.node()}: bucket {row.bucket!r} is not one of the seven")
        sizes[row.bucket] += 1
    if sum(sizes.values()) != len(rows):
        raise ValueError(f"the buckets hold {sum(sizes.values())} of {len(rows)} rows")
    return sizes


def summary(bundle_dir: Path, rows: list[Row]) -> dict[str, Any]:
    """The counts a reader of this census asks for, and the excluded population.

    The projection figure is MEASURED and not asserted: the exclusion's whole argument is
    that those nodes are a re-cut of these, so the table has to be able to say how many
    rows it would have gained and that none of them carries a class of ours.
    """
    projection_documents, projection_occurrences = 0, 0
    for path in sorted(bundle_dir.rglob("*.json")):
        relative = str(path.relative_to(bundle_dir))
        if relative.split("/", 1)[0] not in bundle.PROJECTIONS:
            continue
        projection_documents += 1
        projection_occurrences += sum(1 for _ in occurrences(bundle_dir, relative))
    emitting = frozenset(bundle.portable(bundle_dir))
    return {
        "buckets": partitions(rows),
        "total": len(rows),
        "nodes": len({(row.document, row.pointer) for row in rows}),
        "documents_walked": len(documents(bundle_dir)),
        "from_documents": sum(1 for row in rows if row.document in emitting),
        "from_registry": sum(1 for row in rows if row.document not in emitting),
        "by_keyword": dict(collections.Counter(row.keyword for row in rows)),
        "by_position": dict(sorted(collections.Counter(row.position for row in rows).items())),
        #: ``F`` and ``C`` by position, which is what keeps "no class at that pointer" from
        #: reading as "a class is missing": at ``RULE`` and ``CONJ`` the union compiles to
        #: a cross-field rule and a class there would be the defect.
        "C_and_F_by_position": {
            name: dict(
                sorted(collections.Counter(row.position for row in rows if row.bucket == name).items())
            )
            for name in ("C", "F")
        },
        "object_ish": sum(1 for row in rows if row.object_ish_branches >= OBJECT_ISH_BRANCHES),
        "at_least_one_object_ish": sum(1 for row in rows if row.object_ish_branches >= 1),
        "all_branches_object_ish": sum(
            1 for row in rows if row.object_ish_branches == row.branches
        ),
        "excluded_projection_documents": projection_documents,
        "excluded_projection_occurrences": projection_occurrences,
        "A_with_a_discriminator": sum(
            1 for row in rows if row.bucket == "A" and row.branch_discriminator not in ("", "-")
        ),
        "A_without_a_discriminator": sum(
            1 for row in rows if row.bucket == "A" and row.branch_discriminator in ("", "-")
        ),
        "C_and_F_with_arms_and_no_base": {
            name: sum(1 for row in rows if row.bucket == name and row.arm_classes)
            for name in ("C", "F")
        },
        "titled_branch_occurrences": sum(1 for row in rows if row.titled_branches),
        "schema_discriminator_occurrences": sum(1 for row in rows if row.schema_discriminator),
        "const_keyed_occurrences": sum(1 for row in rows if row.const_keyed_property),
        #: The document states a selector -- by the ``discriminator`` keyword or by a
        #: property every object-ish branch pins to one value -- and our class at the
        #: pointer carries no ``_BRANCH_DISCRIMINATOR``, or there is no class.  This is the
        #: one cell of the table that is a CLAIM about us rather than a description, so it
        #: is counted rather than left to a reader to join two columns.
        "document_states_a_selector_and_we_do_not": {
            name: sum(
                1
                for row in rows
                if row.bucket == name
                and (row.schema_discriminator or row.const_keyed_property)
                and row.branch_discriminator in ("", "-")
            )
            for name in "ABCDEFG"
        },
        "nodes_in": {
            name: [row.node() for row in rows if row.bucket == name] for name in "BCEF"
        },
    }


def table(rows: list[Row]) -> str:
    """The TSV: the header, then one line per row, newline-terminated."""
    lines = ["\t".join(COLUMNS)]
    lines += ["\t".join(str(value) for value in row) for row in rows]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True, help="the bundle directory")
    parser.add_argument("--tsv", type=Path, required=True, help="where the table is written")
    parser.add_argument(
        "--check", action="store_true", help="write nothing; fail if the table is stale"
    )
    parser.add_argument("--summary", type=Path, help="write the counts as JSON here too")
    arguments = parser.parse_args(argv)

    rows = census(arguments.bundle)
    counts = summary(arguments.bundle, rows)
    written = table(rows)
    if arguments.check:
        held = arguments.tsv.read_text(encoding="utf-8") if arguments.tsv.exists() else ""
        if held != written:
            sys.stderr.write(f"{arguments.tsv}: stale -- the bundle and the tree say otherwise\n")
            return 1
    else:
        arguments.tsv.write_text(written, encoding="utf-8")
    if arguments.summary:
        arguments.summary.write_text(json.dumps(counts, indent=2, sort_keys=True), encoding="utf-8")
    # ``sys.stdout`` and not ``print``, which is ``T201``: ``pyproject.toml`` admits a
    # ``print`` only in ``codegen/__main__.py`` and calls one anywhere else a finding, and
    # this file is new -- the exemption is not ours to widen.  ``nodes_in`` is left out of
    # the terminal and kept in ``--summary``, because four bucket listings is a page.
    sys.stdout.write(
        json.dumps({k: v for k, v in counts.items() if k != "nodes_in"}, indent=2, sort_keys=True) + "\n"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - the entry point
    raise SystemExit(main())
