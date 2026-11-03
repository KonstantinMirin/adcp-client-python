"""The hand-written pieces every emitted schema module imports.

Hand-written, and small on purpose: everything else in ``_schemas/`` is a
function of a bundle document.

**Every emitted class carries a reference to the schema that generated it.**
``__adcp_schema__`` is a ``SchemaRef`` -- the document's bundle-relative path
plus a JSON pointer -- and that one fact is what makes everything below generic.
``strict_validate`` reads it off ``cls``; the test harness reads it off the same
class; neither consults a table, a module header, a filename convention or a
name-keyed lookup.  The previous arrangement had all four, through a
``_bindings.json`` the emitter wrote and a ``codegen/adapter.py`` that aimed the
harness at a tree -- and an adapter that can be aimed at a tree can be aimed at
the WRONG tree, which is how a previous attempt came to grade 1,602 documents
green while generating nothing.  A class that carries its own schema cannot be
aimed at someone else's output.

The pointer is there because a nested class is a SUBSCHEMA of its document and
has to grade against its own node rather than against the whole file.  A root
class names ``"#"``.

``AdCPBaseModel`` carries the config a document says nothing about.  D8 derives
``extra`` from ``additionalProperties`` alone: ``false`` -> ``forbid``, ``true``
-> ``allow``, and a document that declares neither gets this base's ``ignore``.

**Absent and ``true`` are different statements.**  ``true`` says an additional
property is part of the document, so it is retained; silence says only that one
is permitted, so it is accepted and dropped.  Retaining a property the document
never mentions would be this SDK adding a claim the schema does not make.  Both
answers accept the same payloads, so the choice is about retention and not about
the accepted set.

**Nothing here reads an environment and no generated class carries a policy its
document does not state.**  A consumer wanting stricter or looser behaviour than
the schema sets it on a subclass.  In this step's population exactly ONE object
node is silent on ``additionalProperties`` (23 declare ``true``, 15 declare
``false``), so this default decides one class and the other 43 decide
themselves.

Acceptance is decided by ``strict_validate``, which validates a payload against
the DOCUMENT'S OWN JSON Schema and only then constructs through
``model_validate``.  One call, both answers: the verdict is the schema's and the
value is pydantic's.

``model_validate`` stays public, because pydantic exposes it and it cannot be
removed.  It constructs **without** consulting the schema.  Everything the
schema states and the annotation does not -- an explicit ``null`` for a property
declared ``{"type": "string"}``, a key the document forbids -- is invisible to
it.  A caller that wants the document's accepted set calls ``strict_validate``;
a caller that already knows its payload conforms, or that is rebuilding a value
this library produced, calls ``model_validate`` and takes the constructor.

So an optional property renders plain ``T | None``, with its own default (D4),
and there is no per-field validator refusing the null.  ``required`` governs
presence and ``type`` governs value, which is the distinction the schema already
draws and the schema half already enforces: a validator re-stating it in Python
would re-implement a fact the document states exactly, on every one of the
bundle's ~7,000 property annotations, and would cost pydantic's serialization
fast path to do it.  The ``None`` branch of the annotation is live either way,
because the attribute holds ``None`` for an omitted key, so ``x.field is None``
means "not supplied".

``strict_alias`` is the same two halves for a node that has no class to put them
on: D2 makes a scalar ROOT a module-level ``Annotated`` alias, so the emitted
module binds ``strict_validate`` as a function instead of a classmethod.  Both
reach the document through ``schema_at`` and refuse through ``_refuse``, which
is what keeps a class and an alias from answering differently about what their
document accepts.

``docs/plan/rebuild-plan.md`` §2 and D4 carry the decisions and the reasoning.
"""

from __future__ import annotations

import functools
import json
import re
from collections.abc import Callable, Mapping
from importlib import resources
from typing import (
    Annotated,
    Any,
    ClassVar,
    Literal,
    NamedTuple,
    TypeVar,
    Union,
    get_args,
    get_origin,
)

import jsonschema
from pydantic import BaseModel, ConfigDict, Field, RootModel, TypeAdapter
from pydantic_core import InitErrorDetails, PydanticCustomError, ValidationError, core_schema

from adcp.types._runtime import RuleBound, refuse

#: The package the emitter writes both the modules and the documents into.  One
#: JSON file per document, at the document's own bundle-relative path, so
#: ``SchemaRef.document`` is simultaneously the identity of the schema and the
#: resource that holds it.  The bundle itself (124 MB, with a version in its
#: path) is a build-time input and cannot be the runtime source.
PACKAGE = "adcp.types._schemas"

ModelT = TypeVar("ModelT", bound="SchemaBound")

#: The engine every ``pattern`` in this package is compiled with, named once
#: because a class reads it off ``AdCPBaseModel`` and an alias has to be handed
#: it (see ``strict_alias``), and two spellings of one engine is one place for
#: them to come apart -- which is exactly how the defect below shipped.
#:
#: **``python-re`` is the engine whose accepted set is the DOCUMENT'S.**  The
#: document's own validator is ``jsonschema``, which compiles every pattern with
#: Python ``re``, so any other engine is this package deciding that a string the
#: schema admits is unrepresentable.
#:
#: pydantic's default is the Rust engine, which is faster and which refuses to
#: build a pattern it cannot honour rather than mis-matching one, so it is the
#: one to want -- and it was adopted here and then measured.  **The two engines
#: do not agree, and look-around is not the reason.**  Python's ``$`` matches at
#: the end of the string OR just before a trailing newline; Rust's ``$`` matches
#: only at the end of the haystack.  So for every ``$``-anchored pattern the
#: document admits a value ending in ``\n`` that a Rust-engine model refuses.
#: Measured over the 1,054 portable documents of the 3.2 bundle: 105 of 110
#: distinct patterns contain ``$``, at 768 of 830 sites, against 4 distinct
#: look-around patterns at 18 sites.  The Rust engine's accepted set is the
#: document's for **5 of 110** distinct patterns, not 102.
#:
#: Scoping it per class therefore buys 5 patterns and costs a narrowing at 105,
#: and no rewrite of the pattern is available either: ``pattern`` is a constraint
#: the document states, so translating ``$`` would change which payloads the class
#: accepts.
REGEX_ENGINE: Literal["python-re"] = "python-re"


class SchemaRef(NamedTuple):
    """The schema a generated class was generated from.

    ``document`` is bundle-relative (``"core/pagination-request.json"``) and is
    also the resource path inside :data:`PACKAGE`.  ``pointer`` is a JSON
    pointer into it: ``"#"`` for a root class, ``"#/properties/x"`` for the
    nested class a property declares inline.

    A ``NamedTuple`` for three reasons: it is hashable, so the read below can be
    memoized per document instead of per table; it is immutable, so a class
    cannot be re-pointed at another document after import; and its ``repr`` is a
    valid Python expression naming this type, which is how the emitter writes
    the ``ClassVar`` line without any template of its own.
    """

    document: str
    pointer: str = "#"


class Approximation(NamedTuple):
    """One fact a generated annotation does NOT carry, declared on the artifact.

    ``docs/plan/rebuild-plan.md`` section 2, "An approximation is declared, and it is
    local": "Every one carries its document, its pointer, the keyword whose fact the
    annotation does not carry, the rung it took, that fact in the document's own
    spelling, and an **attribution**.  Nothing is approximated by silence: an undeclared
    widening is a defect and section 8 reports it as one."

    **It lives HERE, beside :class:`SchemaRef`, because it is part of the ARTIFACT's own
    vocabulary and not of the compiler's.**  ``docs/plan/architecture.md`` section 7:
    "An approximation is a DECLARATION and not a report, and it is written into the
    emitted module ... ``render.py`` writes ``__adcp_approximations__`` onto the class,
    the root model or the enumeration, and beside the module for an alias -- exactly the
    split section 4 of the semantics document already makes for ``strict_validate`` --
    and ``verify/`` reads it as a consumer reads any other class attribute."  The other
    class attribute a consumer reads is ``__adcp_schema__``, and it is a ``NamedTuple``
    declared in this module; this is the same thing for the same reason, so there is ONE
    declaration of what an approximation is and the verifier does not restate its field
    names.  ``codegen.ir`` binds the name section 7's table puts in the IR, the way it
    already binds ``SchemaRef`` and ``Rule``.

    A ``NamedTuple`` for :class:`SchemaRef`'s third reason above: its ``repr`` is a valid
    Python expression naming this type, so the emitter writes the declaration with no
    template of its own and the field names in the emitted module are read off this
    declaration rather than spelled again.

    **``kind``, ``rung`` and ``attribution`` are ``str`` and not enums**, because what
    the emitted module carries is text a consumer reads: a ``StrEnum`` member's ``repr``
    is ``<Rung.KEYWORD: 'KEYWORD'>``, which is not a constructor expression, so the
    minting function writes the member's VALUE.  ``codegen.keywords.Rung`` is still the
    one declaration of which rungs exist, and ``tests/test_approximation.py`` asserts
    every declared rung is one of its members.

    **It is NOT a ``Field(json_schema_extra=...)``**, and section 7 says why: that would
    put the approximation into ``model_json_schema()``.  A declaration is a record of
    what the model DROPPED, so writing it there would put it into the very payload
    contract it is a note about.  It is a class attribute: the verifier reads it, and
    nothing a consumer validates against carries it.
    """

    #: The bundle-relative document the widened node belongs to.
    document: str
    #: The JSON pointer of the node whose annotation does not carry the fact.
    pointer: str
    #: The keyword whose fact is dropped.  It is a keyword the DOCUMENT states, by
    #: section 9's "Never approximate on a keyword the walk itself inserted".
    keyword: str
    #: ``WIDENED`` or ``UNDERDETERMINED`` (section 2's two kinds, never summed).
    kind: str
    #: The ``codegen.keywords.Rung`` this drop took, by value.
    rung: str
    #: The dropped fact in the DOCUMENT'S OWN SPELLING, as the document states it, so
    #: section 8 can look for it in the document and find it.
    fact: Any
    #: Section 2's attribution, a choice of two: the cell's own address
    #: (``"<section>/<keyword>"``) where the design decided the widening, or an upstream
    #: issue reference where the document could state the fact and does not.
    attribution: str


#: The two kinds of approximation section 2 names, which are NEVER summed: "WIDENED --
#: the annotation admits a value the document refuses ... UNDERDETERMINED -- the
#: annotation admits exactly what the document admits, and the VALUE it constructs is
#: not determined by the document."  Declared beside :class:`Approximation` because the
#: artifact carries the word and both halves read it.
WIDENED, UNDERDETERMINED = "WIDENED", "UNDERDETERMINED"
KINDS = (WIDENED, UNDERDETERMINED)

#: **The attribute the emitted artifact carries its declarations under**, named here for
#: the reason :class:`Approximation` is declared here: three writers spell it -- a class
#: body line, a root model's body line, the module-level line a root alias or enumeration
#: takes -- and one reader grades it, and a second spelling is how a declaration comes to
#: be written where nothing looks for it.  ``codegen/render.py`` writes under this name and
#: ``codegen/harness.py`` reads it, each by importing this.
APPROXIMATIONS = "__adcp_approximations__"


@functools.lru_cache(maxsize=None)
def _document(document: str) -> dict:
    """One document, read from the package and held.

    Per DOCUMENT, which is the fix the previous whole-table cache's own docstring
    named: that one parsed every row to validate against one of them, so its
    cost grew with the size of the population rather than with the number of
    documents a process actually validates against.  This one is bounded by the
    number of distinct documents the caller touches, and a process that
    validates against one reads one.
    """
    resource = resources.files(PACKAGE)
    for part in document.split("/"):
        resource = resource.joinpath(part)
    return json.loads(resource.read_text())


#: The pointer segments through which a subschema applies to the SAME INSTANCE its
#: parent does, so an assertion the parent makes about that instance binds the child
#: too.  ``allOf``/``anyOf``/``oneOf`` hold a LIST, so the hop spans two segments.
#:
#: ``if`` and ``not`` are excluded ON PURPOSE, and the exclusion is where this rule's
#: correctness lives: both apply at the same instance location, but a ``type`` under
#: ``if`` is a CONDITION the instance may fail without the document refusing it, and a
#: ``type`` under ``not`` is a type the instance must NOT have.  Neither asserts what
#: the instance IS.
#:
#: Declared here, in the package, rather than in ``codegen``: the emitter decides
#: whether a node can become a class from exactly this rule and the runtime decides
#: what that class's schema is, so two spellings would be a lowering admitting a node
#: the runtime does not constrain -- a model narrower than the schema it names, which
#: is the defect :func:`applied_schema` exists to prevent.  ``codegen.bundle`` reads
#: this function; it does not restate the rule.
SAME_INSTANCE_LIST = ("allOf", "anyOf", "oneOf")
SAME_INSTANCE_ONE = ("then", "else")

#: THE SECTION A CARRIED DOCUMENT STORES A REPEATED SUBTREE UNDER, and the entry name it
#: stores it as.
#:
#: ``docs/plan/architecture.md``, "THE RECORD'S TEXT IS A DAG; ITS POINTERS ARE NOT": "The
#: record stores each distinct subtree once under its own ``definitions`` with a local
#: reference at each occurrence.  **Every pointer any reader SPELLS keeps the spelling it
#: has today.**  The hoisting is a storage representation and the readers dereference
#: through it; it is not a renaming."
#:
#: **It is declared HERE, in the artifact's own vocabulary, for :class:`SchemaRef`'s
#: reason.**  The package carries the document, so the package is what has to read its
#: storage; ``codegen.bundle`` WRITES it and imports these two names rather than spelling
#: them a second time.  Two spellings of the storage section is how a writer and a reader
#: come to disagree about which pointers resolve.
#:
#: **No document of the bundle names an entry under this prefix**, which is what keeps the
#: predicate below exact rather than approximate: ``codegen.bundle.stored`` refuses to
#: write a record whose own section already holds one, so a reference matching it is one
#: the storage wrote.
STORE_SECTION = "definitions"
STORE_PREFIX = "Shared"

#: The reference a stored subtree is named by, and the one place its SPELLING is written.
_STORE_REF = re.compile(rf"^#/{STORE_SECTION}/({STORE_PREFIX}\d+)$")


def store_entry(index: int) -> str:
    """The entry name the ``index``-th stored subtree is held under."""
    return f"{STORE_PREFIX}{index}"


def store_ref(entry: str) -> str:
    """The local reference naming the stored subtree held under ``entry``."""
    return f"#/{STORE_SECTION}/{entry}"


def through_the_store(node: Any, root: Any) -> Any:
    """``node`` with a STORAGE reference followed, or ``node`` itself.

    **The one dereference of the record's own storage, and it is TRANSPARENT.**  The
    architecture section above makes the hoisting invisible to every pointer a reader
    spells, so a pointer that named a node of the inlined text must name the same node of
    the stored text -- and between the two sits exactly this hop.  It carries nothing and
    answers nothing: a ``definitions/Shared<N>`` segment is not an instance-bearing hop,
    so :func:`applied_schema` neither resets the ``type`` it is carrying nor drops a
    sibling conjunct across it, which is what the section requires of it.

    **A DOCUMENT'S OWN local reference is left exactly as written**, which is the whole
    reason the predicate is this narrow.  ``bundle.record`` leaves one in and 1,158 of them
    carry a ``description`` beside the ``$ref``; following those would change what
    :func:`schema_at` hands a grader at every one of them, for a storage decision that
    touches none.  So the hop is taken only for a node whose ONE key is a ``$ref`` naming
    a storage entry, which is the only node the hoisting writes.

    One hop suffices and the loop is bounded for the reason it suffices: a stored subtree
    is never itself a bare reference (``bundle.stored`` stores no node that already is
    one), so a storage reference resolves to a node that is not another.  The bound is
    written anyway, and raises, because a cycle here is a defect of the writer and the
    alternative to raising is a hang.
    """
    for _ in range(_STORE_HOPS):
        if not isinstance(node, dict) or len(node) != 1:
            return node
        uri = node.get("$ref")
        if not isinstance(uri, str) or (named := _STORE_REF.match(uri)) is None:
            return node
        section = root.get(STORE_SECTION) if isinstance(root, dict) else None
        if not isinstance(section, dict) or named[1] not in section:
            return node
        node = section[named[1]]
    raise LookupError(
        f"{node} is reached through more than {_STORE_HOPS} storage references, so the "
        "record's own store holds a reference cycle"
    )


#: How many storage hops one dereference takes before it is a defect.  One is enough; see
#: :func:`through_the_store`.
_STORE_HOPS = 4

#: The keywords an enclosing node states ABOUT THE SAME INSTANCE beside its ``type``
#: word, conjoined into the node below it by :func:`_conjunction`.
#:
#: **These four and no others, because §5's union row compiles exactly these onto a
#: union base** -- "every keyword beside the combinator compiles onto the base, and
#: every branch inherits it.  Draft-07 applies a root's ``properties``, ``required``,
#: ``additionalProperties``, ``allOf`` and rule keywords to the same instance a branch
#: describes" -- and §8 grades a branch class "against its branch node read under the
#: root's siblings".  ``allOf`` is not in this tuple because it is already a conjunct
#: LIST and is spliced rather than wrapped; the three here are the node's own
#: assertions and become ONE conjunct.
#:
#: A rule keyword (``not``, ``dependencies``, ``minProperties``, ``if``/``then``) is
#: NOT here, and the reason is the one ``if`` and ``not`` are excluded from
#: :data:`SAME_INSTANCE_LIST` for: §5 compiles it to a RULE, which renders nothing in a
#: model's JSON schema, so there is nothing at the branch's pointer for a reader to
#: find, and conjoining it would state a fact the model cannot carry.  The rule itself
#: reaches every branch the way the fields do -- it is written on the base and
#: inherited -- which is class inheritance and needs no reading here.
SAME_INSTANCE_FACTS = ("properties", "required", "additionalProperties")

#: What a node says to a READER rather than about an instance, dropped from an
#: enclosing node's conjunct before :func:`_conjunction` splices it into a node below.
#:
#: **§6's description-authority rule answers an annotation AT THE POINTER THAT STATES
#: IT**, and the enclosing node is that pointer: a root composing
#: ``core/version-envelope.json`` states its own ``description`` beside the conjunct,
#: so the root's wins at the root -- which is what both halves already do, the
#: verifier by starting from the node and the emitter by
#: ``compiler.lower_composition``'s ``inherited_description``.  Spliced into a BRANCH
#: with its annotations intact, the conjunct's description arrives at a pointer the
#: root has already answered it at, and a branch class that is silent -- as a subclass
#: with no docstring of its own is -- reads as dropping a fact 14 pairs over 7
#: documents reported, every one the envelope's own root description.
#:
#: The keys are the two §6's rule is about.  A CONSTRAINING key is never dropped, which
#: is the whole point of the splice; ``title`` rides with ``description`` because §6
#: gives the pair one row and §8 compares neither a title nor anything derived from one.
_ANNOTATES_THE_POINTER_THAT_STATES_IT = ("title", "description")

#: The keywords draft-07 asserts about an OBJECT and IGNORES for every other instance,
#: so a subschema stating nothing else admits every non-object vacuously.
#:
#: Read by :func:`entailed_types`' second clause, and it is read as a CEILING on a
#: branch's whole key set rather than as a list of keys to look for: a branch stating
#: one key outside it -- an ``allOf``, an ``if``, a ``not`` -- may refuse a non-object,
#: and then the vacuity the clause reasons from does not hold.
#:
#: **Four keys and not seven, which makes the clause fire LESS often and never
#: wrongly.** ``minProperties``, ``patternProperties`` and ``dependencies`` are also
#: ignored for a non-object and are deliberately absent: a branch carrying one is
#: screened out, the entailment does not fire, and the node is read exactly as it is
#: read today.  Measured over the 1,054 portable documents, no site turns on them --
#: the three ``oneOf`` nodes the clause fires at state these four keys and nothing
#: else, and admitting ``title``/``description`` beside them adds no site at all.
#:
#: It equals ``codegen.keywords.ARM["object"]`` today and is NOT that table: ARM
#: answers which keyword a ``type`` word carries on one arm of a type LIST, for a cut
#: and its inverse fold, and omits the other three because no row of the cut decides
#: them.  This answers which keyword says nothing about a non-object.  Same four keys,
#: two readings, and the direction each one is conservative in is different -- so it is
#: declared here, where the rule it serves is, rather than imported into the package
#: from the compiler that may not be installed beside it.
IGNORED_BY_A_NON_OBJECT = frozenset(
    {"properties", "required", "additionalProperties", "propertyNames"}
)


def _as_a_member(word: Any) -> Any:
    """A ``type`` value as a SET MEMBER: draft-07's LIST form becomes a tuple.

    draft-07's ``type`` is a word or a list of them, and both are assertions about the
    same instance -- so :func:`entailed_types` answers about both, and a set is what it
    answers with, which a list cannot be a member of.  The tuple keeps the document's
    own order, so two spellings of one list are two members and neither is read as the
    other.
    """
    return tuple(word) if isinstance(word, list) else word


#: What ``root`` says when there is no stored document behind a node, which is what every
#: reader holding a bare schema has.  :func:`through_the_store` answers ``node`` itself for
#: it, so a caller grading a literal or a RAW document passes nothing and reads what it
#: always read; a caller walking a RECORD passes the record, because that is where the
#: storage lives.  Written as a name so the three statement readers below say the same
#: thing in their signatures.
NO_STORE: Any = None


def entails_type(node: Mapping[str, Any], value: Any, root: Any = NO_STORE) -> bool:
    """Does this node's COMBINATOR force exactly ``value`` on its own instance?

    :func:`entailed_types` asked of one candidate, for the reader that holds a ``type``
    value and not a word: ``codegen.harness`` is handed whatever the MODEL renders,
    which draft-07 lets be a list, and a list is no set member.  So the one
    normalisation is applied to both sides here rather than at the call, which is what
    keeps the two readers of the derivation from disagreeing about the list form.
    """
    return _as_a_member(value) in entailed_types(node, root)


def entailed_types(node: Mapping[str, Any], root: Any = NO_STORE) -> frozenset[Any]:
    """The ``type`` words a node's COMBINATORS force on the instance it describes.

    draft-07 holds a ``oneOf``/``anyOf`` against the same instance the node describes,
    so a node stating no ``type`` of its own can still admit instances of one type
    only -- and then the word is the document's statement about that instance, as much
    as a stated one is.  Two clauses, and each is a property of the branch list:

    * **every branch states the SAME word.**  An instance must satisfy a branch, and
      every branch demands that type, so no other type is admitted.
    * **a ``oneOf`` of two or more branches that each admit every non-object
      vacuously** -- every key inside :data:`IGNORED_BY_A_NON_OBJECT` -- admits no
      non-object at all.  A non-object satisfies ALL of them, ``oneOf`` demands
      exactly one, so ``oneOf`` refuses it; an object may satisfy exactly one and is
      admitted.  **This clause is ``oneOf``'s and not a combinator's**: under
      ``anyOf`` the same branch list admits every non-object, because satisfying all
      is satisfying at least one.  Stated as a property of the branch list rather than
      of exclusivity it would be a NARROWING at an ``anyOf``.  A branch with no key at
      all is excluded for the same reason read the other way: the empty schema admits
      the objects too, so every instance satisfies every branch and the node admits
      nothing -- a shape this says nothing about rather than one it calls ``object``.

    A :class:`frozenset` and not one word, because the two combinators are independent
    assertions and a node may state both; the clauses themselves cannot collide, since
    the second requires a branch list that states no ``type`` word.

    The members are ``type`` VALUES read through :func:`_as_a_member`, so draft-07's
    list form is a tuple here -- a branch list whose every member states
    ``["string", "null"]`` forces that list, which no single word expresses, and
    :func:`entails_type` is the reader that normalises the other side.
    :func:`applied_schema` takes an answer only where it is one ``str``, because what it
    does with one is conjoin ``type: <word>`` into the node below and a list admits more
    than one type -- the same reading its own clause already gives a STATED list.

    **Declared in the package, beside :data:`SAME_INSTANCE_LIST`, for that data's own
    reason**: the emitter decides whether a node can become a class from this answer,
    the runtime decides what that class's schema is from :func:`applied_schema`, and
    the verifier decides whether a model's ``type`` word is one its document states.
    Three readers, one derivation.  A second spelling in any of them is a model
    narrower than the schema it names, or the same disagreement showing up as the
    verifier reporting a fact the emitter read off the document.
    """
    out: set[Any] = set()
    for combinator in SAME_INSTANCE_LIST[1:]:  # anyOf, oneOf -- not the conjunct list
        branches = node.get(combinator)
        if not isinstance(branches, list) or not branches:
            continue
        if not all(isinstance(b, dict) for b in branches):
            continue
        # Each branch READ THROUGH THE RECORD'S OWN STORAGE, because both clauses below
        # read the branch's keys: a branch stored once and referenced here states its
        # ``type`` at the entry, and read as the reference it is a branch stating no word
        # -- so the entailment the document makes would go unseen and the clause would
        # answer about a node the document does not have.
        branches = [through_the_store(b, root) for b in branches]
        stated = {_as_a_member(b.get("type")) for b in branches}
        if len(stated) == 1 and (word := next(iter(stated))) is not None:
            out.add(word)
        elif (
            combinator == "oneOf"
            and len(branches) >= 2
            and all(b and set(b) <= IGNORED_BY_A_NON_OBJECT for b in branches)
        ):
            out.add("object")
    return frozenset(out)


def _conjunction(node: dict, through: str, root: Any = NO_STORE) -> list:
    """What ``node`` asserts about the same instance, as draft-07's own conjunct list.

    **A conjunction is spelled the way draft-07 spells one -- an ``allOf`` member --
    and not merged keyword by keyword.**  Merging needs a rule per keyword (which
    ``properties`` map wins a shared key, which ``required`` list, what a second
    ``additionalProperties`` means) and every one of those rules would be a second copy
    of §2's intersection, living in the runtime where no cell can reach it.  As a
    conjunct the statement is exact: ``jsonschema`` applies it as draft-07 does, and
    §8's reading already folds a document's conjuncts into the node
    (``codegen.harness._composed``), which is the same reading the model's own
    inheritance makes.

    ``through`` is the keyword the walk is descending BY, and it is why an ``allOf``
    is not conjoined into one of its own members: at an ``allOf`` hop the list the
    walk is entering is this node's own, and splicing it in would state every
    sibling conjunct at a pointer inside one of them.  The two union keywords are
    never spliced at all -- a branch is satisfied by SOME instance, so the other
    branches assert nothing about this one -- which is why only ``allOf`` is read
    here.

    ``properties: {}`` and ``required: []`` are left out, because §4 says a root
    ``properties: {}`` beside a union "declares no field and contributes nothing" and
    §5's ``required`` row says ``required: []`` compiles to nothing.  A node asserting
    none of the four contributes no conjunct at all, which is what keeps the node
    returned UNCHANGED at the 7,987 pointers that reach nothing.
    """
    own: dict = {}
    for keyword in SAME_INSTANCE_FACTS:
        if keyword not in node:
            continue
        if keyword in ("properties", "required") and not node[keyword]:
            continue
        own[keyword] = node[keyword]
    # The node's OWN statement first and its conjuncts after, which is the order the
    # node itself is read in: ``harness._composed`` starts from the node and folds each
    # conjunct into it, so a fact the node states wins a gap-fill over a conjunct's.
    # Reproducing that order here is what keeps one reading of the enclosing node at the
    # enclosing pointer and at a pointer below it.
    out: list = [own] if own else []
    if through != "allOf" and isinstance(node.get("allOf"), list):
        # Each conjunct READ THROUGH THE RECORD'S OWN STORAGE: the strip below reads the
        # conjunct's keys, and a conjunct stored once and referenced here has one key that
        # is not a statement at all, so the conjunction would carry a reference where the
        # document states facts.
        out.extend(
            {k: v for k, v in c.items() if k not in _ANNOTATES_THE_POINTER_THAT_STATES_IT}
            for c in (through_the_store(c, root) for c in node["allOf"])
            if isinstance(c, dict)
        )
    return out


def _cut_to_its_own_word(node: dict) -> dict:
    """A node whose ``type`` is a LIST, read at the one word a CLASS describes.

    **§8's DUAL of the union-branch pairing rule** (added 2026-10-26): "A class cut out
    of a type list is paired with its node read at ITS OWN TYPE WORD, not at the whole
    list.  The union-branch rule adds the root's siblings because the branch describes
    the same instance the root does; this one subtracts the list's other words for the
    mirror reason -- the class describes one member of the union and the other members
    are carried by the field holding it, not by this class."

    The word is ``object``, and it is DERIVED rather than chosen: a type list lowers to
    one arm per word and ``object`` is the only word an arm can be a CLASS at -- a
    scalar arm is an annotation, an array arm is a ``list[X]``, a ``null`` arm is
    ``None`` -- so the node that declares ``properties`` is the one whose object arm is
    declared, at the node's own pointer, and that arm is what this schema is read for.
    The gate is ``properties``, because that is what §4's ``type`` row makes an object
    node a class by; a type list that declares none has no class cut out of it and is
    handed back untouched (61 of the 62 type-list nodes of this bundle).

    ``core/delivery-metrics.json#/properties/quartile_data`` is the one site and the
    measured case §8 records: it states ``type: ["object", "null"]``, the field renders
    ``DeliveryMetricsQuartileData | None``, the ROOT pair passes because
    ``harness._normalize`` folds the model's ``anyOf`` back into the document's own
    list, and the nested class reported ``differs /type`` -- ``object`` against
    ``["object", "null"]`` -- for a fact the parent already carries and the verifier
    already graded.  The model is faithful at both pointers; only the pairing was wrong.

    It subtracts WORDS and nothing else.  A keyword only another word can carry is that
    arm's and reaches no class either way (``codegen.schema.parse.ARM``), and a keyword
    the object word carries is this class's, so there is nothing else to take away.
    """
    if not isinstance(node.get("type"), list) or not node.get("properties"):
        return node
    return {**node, "type": "object"}


def _descended(statements: list, key: str, root: Any = NO_STORE) -> list:
    """Every statement in ``statements``, read at ``key``.

    One hop of a pointer, applied to the statements held against the instance the hop
    is leaving.  draft-07 holds a conjunct and the node it composes against one
    instance, so a hop to a different instance -- a ``properties`` key, an ``items``,
    a mapping value -- moves both: ``allOf/0/properties/x`` and ``properties/x``
    constrain one value.  A statement that says nothing at this key drops out, which is
    what makes this total rather than partial.

    It is deliberately blind to whether ``key`` names a KEYWORD or a property NAME,
    because the walk it mirrors is: a pointer alternates ``properties`` with a property
    name and both are a dict lookup, so one operation answers the whole descent and no
    reading of the pointer's segments is needed (``docs/plan/architecture.md`` §3, "a
    node's position is never recovered from a pointer string").
    """
    # The value at ``key`` is READ THROUGH THE RECORD'S OWN STORAGE before it is tested
    # for being a statement at all: a statement whose value at this key is stored once and
    # referenced here would be carried as the reference and then DROP OUT at the next hop,
    # where the reference holds no key -- so a conjunct the document states about an
    # instance two hops down would silently stop being conjoined.
    return [
        descended
        for s in statements
        if isinstance(s, dict)
        and isinstance(descended := through_the_store(s.get(key), root), dict)
    ]


def applied_schema(root: dict, pointer: str) -> dict:
    """The node at ``pointer``, carrying the ``type`` the document applies to it.

    A node is not validated in isolation.  draft-07 applies a root's assertions and
    its combinator branch's to the SAME instance, so in
    ``{"type": "object", "oneOf": [{"properties": {...}}]}`` every instance that
    reaches ``/oneOf/0`` is already an object and the branch restates nothing.  Read
    as the bare node that branch admits a string, which is a schema no class can be
    paired with: the class refuses the string and is narrower than the schema it
    names.  Measured on ``core/activation-key.json``: the two branch pairs reported
    ``accepts:model_refused_valid`` and ``model_adds_a_fact`` at ``/type`` with the
    bare node, and pass with this.

    **``type`` WAS the one fact conjoined, and the KNOWN CEILING this paragraph named
    is now closed** (``docs/plan/architecture.md`` §13 item 3, settled by the design
    owner).  It read: "a row whose root asserts more than a type about the same
    instance needs this extended", and ``lower.union.ROOT_CONJUNCTS`` was what kept
    the population at zero -- a union root carrying ``properties``, ``required``,
    ``additionalProperties`` or ``allOf`` refused, so ``type`` was the only assertion
    such a root could make.  §14 step 9 emitted those 61 documents, so the four
    keywords have arrived -- the READING is that no document of the portable population
    refuses, which ``python -m codegen``'s own report prints -- and §8's pairing rule is
    what they are graded by: "a branch class
    of a root union is paired with its branch node read UNDER THE ROOT'S SIBLINGS:
    draft-07 applies every keyword beside the combinator to the same instance the
    branch describes, so a field the branch inherits from the base is a fact its node
    states and not one it added."

    So the conjunction is :data:`SAME_INSTANCE_FACTS` plus the enclosing node's own
    ``allOf``, spliced into the node's conjunct list by :func:`_conjunction`, and
    ``type`` keeps the spelling it already had.  **This is draft-07's own semantics
    applied at a pointer the document HOLDS and not a view of one** (§9's "do not
    decide a position the bundle does not hold from a view of it"): the branch node is
    the document's, every conjoined statement is the document's, and the conjunction is
    written as the document's own ``allOf`` rather than as a merge this function
    invents.

    **The node's own facts always win**, which is what makes the extension safe in
    the same direction the ``type`` half already is: a node declaring ``string`` under
    a root declaring ``object`` keeps ``string`` and is refused for stating a
    contradiction, and a branch declaring a property the root also declares keeps its
    own declaration with the root's conjoined beside it, so the intersection is what
    the pair is graded against rather than either view alone.

    The node is returned UNCHANGED, as the same object, wherever nothing is
    conjoined, so every pointer that resolved to a document's own node before this
    existed still resolves to that exact node.
    """
    node: Any = root
    enclosing: str | None = None  # the type an enclosing node asserts about THIS instance
    #: What the enclosing nodes assert about THIS instance, in outer-to-inner order.
    conjoined: list = []
    #: §8's THIRD pairing rule, for a node at a CONJUNCT of an ``allOf`` (added
    #: 2026-10-27): the SIBLING conjuncts, carried down the same path the walk takes.
    #: Draft-07 holds every conjunct against the same instance, so a sibling's fact is
    #: one this instance must satisfy and not one the class added -- and where the
    #: pointer continues below the conjunct, the sibling's declaration AT THE SAME KEYS
    #: is what holds against the same instance the node describes.
    siblings: list = []
    #: The conjunct list the next index hop is cutting one member out of.
    cutting: list | None = None
    parts = [p for p in pointer.lstrip("#").lstrip("/").split("/") if p != ""]
    for part in parts:
        # **THE STORAGE HOP, taken BEFORE the part is read and carrying nothing.**  The
        # record stores a repeated subtree once and references it at each occurrence, so a
        # pointer that walked into the inlined text walks into a reference here -- and
        # :func:`through_the_store` is what makes the two the same pointer.  Taken here
        # rather than inside an arm because every arm below reads the node: the
        # ``same_instance`` arm reads its ``type``, the conjunction arm asks whether it
        # holds the key, and the hop at the foot indexes it.
        #
        # It is TRANSPARENT: nothing of ``enclosing``, ``conjoined``, ``siblings`` or
        # ``cutting`` moves across it, because the segment it crosses is not one the
        # document's own text spells and asserts nothing about any instance.
        node = through_the_store(node, root)
        if isinstance(node, list):
            # the index half of a combinator hop, whose keyword was read already
            index = int(part)
            if cutting is not None:
                # Stripped of the two keys §6 answers at the pointer that states them,
                # exactly as :func:`_conjunction` strips a spliced conjunct: a sibling's
                # ``description`` is the SIBLING's pointer's answer, and spliced here it
                # would arrive at a pointer the document has already answered.
                # Each sibling READ THROUGH THE RECORD'S OWN STORAGE, which is
                # :func:`_conjunction`'s reason at the same strip: a sibling conjunct
                # stored once and referenced here holds one key that states nothing.
                siblings = [
                    {k: v for k, v in c.items() if k not in _ANNOTATES_THE_POINTER_THAT_STATES_IT}
                    for i, c in enumerate(through_the_store(c, root) for c in cutting)
                    if i != index and isinstance(c, dict)
                ]
                cutting = None
            node = node[index]
            continue
        same_instance = part in SAME_INSTANCE_LIST or part in SAME_INSTANCE_ONE
        if same_instance:
            declared = node.get("type") if isinstance(node, dict) else None
            # **A WORD THE ENCLOSING NODE ENTAILS COUNTS AS ONE IT ASSERTS**, which is
            # :func:`entailed_types` and which the node's own stated word still beats.
            # The enclosing node's assertion about this instance is what this arm
            # carries, and draft-07 makes that assertion out of the branch list as
            # readily as out of a ``type`` key: a ``oneOf`` whose every branch admits
            # every non-object vacuously admits no non-object, so the instance below
            # the hop IS an object and the document said so.  Read here, where "what
            # encloses this instance" is already decided, rather than at the one row
            # that needs it, because the walk below and the verifier both reach this
            # answer through this function and a second derivation is the divergence
            # this function exists to prevent.
            #
            # Asked only where the node states no word of its own: a node declaring
            # ``string`` over branches that entail ``object`` states a contradiction,
            # and the clause below keeps its own word so it is refused for stating one
            # rather than quietly rewritten.  Asked for ONE word, so a node whose two
            # combinators entail two different types carries neither -- the document
            # there admits nothing, and a word picked off such a list would be this
            # function's invention rather than the document's statement.
            #
            # And for one ``str``, which is the same reading the STATED clause already
            # takes of a type LIST: a ``["object", "null"]`` admits a null, so there is
            # no single word to conjoin and nothing is carried.
            #
            # INHERITED through a chain of such hops: a node asserting nothing passes
            # its own enclosing assertion down.
            if isinstance(declared, str):
                enclosing = declared
            elif (
                isinstance(node, dict)
                and len(entailed := entailed_types(node, root)) == 1
                and isinstance(word := next(iter(entailed)), str)
            ):
                enclosing = word
            if isinstance(node, dict):
                conjoined += _conjunction(node, part, root)
            # **A second CUT drops the first one's siblings rather than guessing how
            # the two compose.**  A conjunct of a conjunct would need a reading of which
            # of the outer siblings' nodes answers the inner cut, and this rule makes
            # none.  Dropped rather than carried, so such a pair reports a fact the model
            # states and the document does not -- loud -- rather than passing for
            # nothing.
            #
            # **A BRANCH below a conjunct is NOT a second cut and keeps them**
            # (``adcp-client-python-10l.37``).  The sentence above covered it and the
            # reason does not reach it: a ``oneOf``/``anyOf``/``then``/``else`` hop moves
            # to no other instance, so a sibling conjunct's statement holds against the
            # branch's instance in the spelling it already has and there is nothing to
            # read.  This is §8's third pairing rule followed as far as the pointer goes,
            # exactly as the ``not same_instance`` arm below already follows it through a
            # KEY hop -- and without it the composition §2 writes into a branch class is
            # graded against the branch's bare text, so every fact a ``$ref`` conjunct
            # contributes reads as a fact this class ADDED, i.e. a model NARROWER
            # than its document, which §8 says is never declarable.
            #
            # Measured over the committed tree: **8 pairs**, the four branches each of
            # ``formats/canonical/display_tag.json`` and ``image.json`` at
            # ``#/allOf/1/oneOf/<i>``, whose base is ``formats/canonical/_base.json``
            # through the sibling conjunct ``#/allOf/0``.  No other pair's reading
            # moves by one fact.
            if part == "allOf":
                siblings = []
                cutting = node.get("allOf") if isinstance(node, dict) else None
            else:
                cutting = None
        else:
            enclosing = None  # the hop moves to a different instance
            cutting = None
        key = part.replace("~1", "/").replace("~0", "~")
        # **Does any conjoined statement HOLD this key?**  Read before the descent below,
        # which is what consumes it: once :func:`_descended` has run, the statement that
        # held the key has BECOME the value under it and the question can no longer be
        # asked.  The arm that uses the answer is two blocks down.
        conjoined_holds = any(
            isinstance(s, dict) and key in s for s in (*conjoined, *siblings)
        )
        if not same_instance:
            # The hop moves to a different instance, and it moves every statement held
            # against THIS instance to THAT SAME instance: draft-07 applies
            # ``allOf/0/properties/x`` and ``allOf/1/properties/x`` to one value.  A
            # statement silent at this key says nothing about it and drops out.
            #
            # **The ENCLOSING statements descend by the same operation, where they used
            # to be DROPPED**, and that is §8's union-branch pairing rule followed as
            # far as the pointer goes: "a branch class of a union is paired with its
            # branch node read under the union's siblings", and a class the branch
            # declares BELOW a property of its own is still describing an instance the
            # root's declaration of that property applies to.  Dropped at the first such
            # hop, the composition §2's intersection rule writes is graded against the
            # branch's bare overlay alone, and every fact the root contributes reads as
            # a fact this class ADDED, i.e. a model NARROWER than its document,
            # which is the one defect §2 forbids outright.  Measured on
            # ``core/assets/vast-asset.json`` and ``core/assets/daast-asset.json``: 4
            # element pairs reported 46 ``added`` facts, every one stated by the root two
            # hops up.  ``core/assets/display-tag-asset.json`` is the control -- it
            # spells the composition in its own branch text, so the ``allOf`` cut already
            # carried it and the pair grades the same either way.
            #
            # There is one operation and not two: :func:`_descended` is what the sibling
            # carrier already did, and the two lists differ in where they came from and
            # not in how they travel.
            conjoined = _descended(conjoined, key, root)
            siblings = _descended(siblings, key, root)
        if isinstance(node, dict) and key not in node and conjoined_holds:
            # **A HOP THE CONJUNCTION HAS AND THE NODE'S OWN TEXT DOES NOT.**  §8's third
            # pairing rule is "followed as far as the pointer goes", and this is one hop
            # further: §2's intersection rule composes a restatement with its base, so a
            # class can be declared from a declaration PART of which came from a sibling
            # conjunct -- and the pointer the class is stamped at is the restatement's,
            # where the document's own text is silent at this key.
            #
            # The node there is the EMPTY schema, which is exactly what the document says
            # at that key: nothing.  Every fact the pair is graded against comes from the
            # conjoined statements the two lines above have already descended, so the
            # composition is graded as the conjunction and not as either view alone.
            #
            # **Gated so it fires ONLY where the walk would otherwise raise**, which is
            # what makes it unable to move a pair that resolves today: a key the node
            # holds takes the hop below exactly as before, and a key NEITHER the node nor
            # any conjoined statement holds still raises -- a class stamped at a pointer
            # the document's conjunction does not have is a defect in the walk and stays
            # loud.
            #
            # Measured on ``core/signal-coverage-forecast.json`` at
            # ``#/properties/points/items/allOf/1/properties/metrics/properties/coverage_rate``:
            # the document restates ``metrics`` as ``{"required": ["coverage_rate"]}`` and
            # ``core/forecast-point.json``'s sibling conjunct declares the sixteen
            # properties, so §2 composes a class whose ``coverage_rate`` field is the
            # base's declaration made required -- and the pair raised ``KeyError:
            # 'properties'`` instead of being graded.
            node = {}
            continue
        node = node[key]
    # The LAST hop's storage reference, for the same reason as the one in the loop and
    # with one more consequence: draft-07 IGNORES every sibling of a ``$ref``, so a node
    # returned as a bare storage reference would silently discard the conjunction below
    # it -- the pointer would resolve and the facts it was resolved for would not.
    node = through_the_store(node, root)
    if not isinstance(node, dict):
        raise LookupError(f"{pointer} is {type(node).__name__}, not a schema")
    # A sibling conjunct is a conjunct of THIS node, so it joins the enclosing
    # statements: both are read before the node's own ``allOf`` and after the node's own
    # keys, which is the order ``harness._composed`` folds in.
    conjoined = [*conjoined, *siblings]
    # §8's DUAL, applied FIRST: it reads the node's OWN ``type``, so it is a statement
    # about this node and not about anything enclosing it, and the clause below -- which
    # conjoins an enclosing word only where the node states none -- then sees the word
    # the class describes rather than the list it was cut from.
    node = _cut_to_its_own_word(node)
    if ("type" in node or enclosing is None) and not conjoined:
        return node
    applied = node if "type" in node or enclosing is None else {**node, "type": enclosing}
    if not conjoined:
        return applied
    # The enclosing statements come FIRST and the node's own conjuncts after, so the
    # node's own are folded last and win a keyword §2's intersection cannot order --
    # the same direction as the ``type`` clause above, where the node's own word wins.
    own = applied.get("allOf")
    return {**applied, "allOf": [*conjoined, *(own if isinstance(own, list) else [])]}


def schema_at(ref: SchemaRef) -> dict:
    """The subschema ``ref`` names, as the document applies it.

    The pointer is resolved here and not at emit time, because the document is
    what the package carries: a nested class's node is part of its document's
    meaning, and writing each node out separately would put the same subschema
    in the package twice and let the two drift.

    :func:`applied_schema` is what makes "its own node" mean the node as the document
    applies it rather than the node read alone; it says which fact that adds and why
    that is the only one.
    """
    return applied_schema(_document(ref.document), ref.pointer)


def _refuse_at(ref: SchemaRef, payload: Any, name: str) -> None:
    """:func:`_refuse` for a node a :class:`SchemaRef` names: the DOCUMENT is the scope.

    **One call so the node and its resolution scope cannot be supplied separately**,
    which is the defect this closes.  ``bundle.record`` inlines a REMOTE reference
    and leaves a LOCAL one, so a node at ``#/definitions/box_decoration`` can say
    ``{"$ref": "#/definitions/rectangle"}`` -- a pointer relative to the DOCUMENT
    ROOT.  Handed the node as its own schema, ``jsonschema`` resolves ``#/`` within
    that node and raises ``PointerToNowhere``, so ``strict_validate`` refused EVERY
    payload, including the ones the document accepts: measured at 5 pairs over
    ``core/placement-presentation.json`` and ``core/bidding-policy-capability.json``,
    each reporting the raise rather than a verdict about any value
    (``salesagent-j3k2l.28``).  0 such pairs existed before, because every document
    carrying one was refused by name.

    The two production entry points -- a class's ``strict_validate`` and an alias's
    -- both reach the schema half through here, so neither can read a node without
    its document.  :func:`_refuse` stays the mechanism and takes a schema, which is
    what a caller grading a hand-written document has.
    """
    root = _document(ref.document)
    _refuse(applied_schema(root, ref.pointer), payload, name, root=root)


def _refuse(schema: dict, payload: Any, name: str, *, root: dict | None = None) -> None:
    """Raise pydantic's ``ValidationError`` for every way ``schema`` refuses ``payload``.

    The schema check runs over the WHOLE payload before anything is constructed,
    which is what covers nesting: pydantic builds children, and an inner value
    the document refuses never reaches it.

    Shared by ``AdCPBaseModel.strict_validate`` and ``strict_alias`` so there is
    one refusal and one error shape.  An alias and a class differ only in how
    they are constructed afterwards; what the document accepts is the same
    question and must not get a second answer.

    ``root`` is what a LOCAL ``$ref`` inside ``schema`` resolves against, and it
    defaults to ``schema`` -- correct for a whole document, and wrong for a NODE of
    one, which is why :func:`_refuse_at` exists and is what both production entry
    points call.  The validator is built on ``root`` and ``evolve``d onto
    ``schema``, so the resolution scope is the document's while the assertions
    applied are the node's.  Verified to refuse THROUGH the reference as well as at
    the node: a ``width: 0`` against a referenced ``rectangle``'s ``minimum: 1``, a
    ``layer`` outside a referenced enum and a ``fill_color`` against a referenced
    ``pattern`` are each reported with its own keyword and pointer.

    The DRAFT is read off ``root`` and not off ``schema``, for the same reason: a
    nested node declares no ``$schema`` and its document does.

    **``format`` IS ASSERTED, and the checker comes from the document's own
    draft.**  ``jsonschema`` treats ``format`` as a pure annotation unless it is
    handed a ``FormatChecker``, so without this the SDK accepted a ``date-time``
    with no offset -- which RFC 3339 forbids and the document therefore forbids
    -- and any Python type derived from a format was narrower than its own
    document.  D5 lets a format select a type exactly because this line exists.
    The checker is ``validator.FORMAT_CHECKER``, the one the draft the document
    DECLARES defines, so the asserted vocabulary is the document's rather than a
    set named here: a ``uuid`` is not a draft-07 format and is not asserted under
    one, and the two installed checker packages (``rfc3339-validator``,
    ``rfc3987``) are what put ``date-time`` and ``uri`` into it.  A format with
    no checker installed asserts nothing, silently, which is why
    ``codegen.emit`` gates its type selection on the same set rather than on a
    list of formats someone wrote down.

    The raise goes through ``_runtime.refuse``, which is also what the rule half
    raises through (D6).  A keyword like ``not`` or ``dependencies`` is refused by
    BOTH halves -- the schema half for a ``strict_validate`` caller, the
    after-validator for a ``model_validate`` one -- and two spellings of one
    refusal is one place for them to grow two error shapes for one keyword.
    """
    scope = schema if root is None else root
    validator = jsonschema.validators.validator_for(scope, jsonschema.Draft7Validator)
    at_the_node = validator(scope, format_checker=validator.FORMAT_CHECKER).evolve(schema=schema)
    errors = sorted(
        at_the_node.iter_errors(payload),
        key=lambda e: [str(p) for p in e.absolute_path],
    )
    refuse(
        name,
        [
            (
                e.validator if isinstance(e.validator, str) else "schema",
                tuple(e.absolute_path),
                e.message,
                e.instance,
            )
            for e in errors
        ],
    )


def strict_alias(ref: SchemaRef, symbol: str, alias: Any) -> Callable[[Any], Any]:
    """The strict entry point for a module-level ``Annotated`` alias.

    D2 makes a scalar root an alias and not a class -- the document is a string,
    and a wrapper class would be a second name for the same node (P2) and would
    put an object on the wire.  So there is no ``AdCPBaseModel`` to carry
    ``strict_validate`` and no class attribute to hold the ``SchemaRef``, and the
    emitted module binds this under its own name instead, with the ref passed in.

    The schema half is the SAME read and the same refusal a class gets; only the
    construction half differs, and for an alias that is ``TypeAdapter``, which
    is the alias's constructor and not its accepted set.  Behind the schema check
    it is the constructor, which is all it was ever meant to be.

    **The adapter is built with the config, and that closed a live narrowing.**
    ``regex_engine`` is a MODEL config, so an ``Annotated`` alias has nowhere to
    carry one: a bare ``TypeAdapter`` took pydantic's default Rust engine while
    every emitted CLASS took ``python-re`` off ``AdCPBaseModel``, and the two
    engines disagree about ``$`` (see :data:`REGEX_ENGINE`).  Measured on the
    emitted tree: ``core/brand-id.json`` states ``pattern: ^[a-z0-9_]+$``, its
    document ADMITS ``"abc\\n"``, and ``BrandID.strict_validate("abc\\n")``
    refused it with ``string_pattern_mismatch`` -- a CONSTRUCTOR refusal of a
    value the schema half had just admitted, which is a model narrower than its
    own document at 2 of this population's 5 scalar roots.  None of the three
    checks reported it: ``compare_schema`` sees the same ``pattern`` fact on both
    sides, and the accepts check did not draw a trailing newline in 25 examples.
    ``config=`` is also the only channel here, because pydantic refuses a
    ``config=`` on a ``TypeAdapter`` over a ``BaseModel`` -- which is why a class
    takes it off the class and an alias takes it here.

    **AN ALIAS WHOSE TYPE IS A MODEL TAKES NO ``config=``, AND THAT IS THE SAME
    SENTENCE READ FORWARD** (``adcp-client-python-10l.55``).  The channel exists for a
    type with nowhere to carry a config; a model carries its own, and
    ``AdCPBaseModel.model_config`` already states :data:`REGEX_ENGINE` -- so passing one
    is both meaningless and a ``PydanticUserError`` at import.  §5's ``$ref`` row at CONJ
    is the position that reaches it: ``core/localized-creative-asset.json`` composes a
    bare ``$ref`` onto a UNION root, which that row makes "this node's own TYPE", so the
    root is an ``Annotated`` alias over ``AssetVariant``.  The narrowing the config closed
    stays closed, because the engine it sets is the one the model's own config sets.
    """
    held = alias
    while get_origin(held) is Annotated:
        held = get_args(held)[0]
    carries_its_own = isinstance(held, type) and issubclass(held, BaseModel)
    adapter = (
        TypeAdapter(alias)
        if carries_its_own
        else TypeAdapter(alias, config=ConfigDict(regex_engine=REGEX_ENGINE))
    )

    def strict_validate(payload: Any) -> Any:
        _refuse_at(ref, payload, symbol)
        return adapter.validate_python(payload)

    strict_validate.__doc__ = f"Validate against {ref.document}, then construct {symbol}."
    return strict_validate


class SchemaBound(RuleBound):
    """The schema half, in ONE body, for every emitted shape that has a class.

    ``docs/plan/architecture.md`` §8: "``strict_validate`` and ``__adcp_schema__``
    factor out of ``AdCPBaseModel`` into a mixin both take -- one body, for the
    reason ``strict_alias`` exists: a second implementation of the schema half is a
    second answer to the one question."  The two takers are
    :class:`AdCPBaseModel`, the base of every emitted class, and
    :class:`AdCPRootModel`, the base of every emitted ROOT MODEL -- and §8's
    requirement is that the two cannot disagree: "each must carry
    ``__adcp_schema__``, ``strict_validate`` and a rule tuple exactly as a class
    does, or a root model and a class disagree about what their document accepts."

    ``RuleBound`` and not ``BaseModel`` directly: it carries the one
    ``model_validator(mode="after")`` that evaluates ``_adcp_rules``, so a shape the
    emitter writes a rule tuple onto needs no validator of its own and a shape with
    no rule inherits the empty tuple and pays one attribute lookup (§2's "rules are
    after-validators, written once").  Carried HERE rather than on each taker,
    because the rule tuple is the third of the three things §8 requires both to have.

    It declares no ``model_config``: ``extra`` is meaningful for a class and pydantic
    REFUSES it on a ``RootModel`` ("``RootModel`` does not support setting
    ``model_config['extra']``"), so the two takers configure themselves and share the
    part that is one question.
    """

    #: Declared and not assigned: every emitted class and every emitted root model
    #: writes its own, and a subclass that writes none has no schema to be validated
    #: against, so reading it is an ``AttributeError`` at the one call below rather
    #: than a silent fall back to ``model_validate``.
    __adcp_schema__: ClassVar[SchemaRef]

    @classmethod
    def strict_validate(cls: type[ModelT], payload: Any) -> ModelT:
        """Validate ``payload`` against this class's own document, then construct.

        The schema decides acceptance and pydantic builds the value.  A schema
        refusal raises pydantic's ``ValidationError``, with the JSON Schema
        KEYWORD that bit as the error ``type`` and the instance pointer as its
        ``loc``, so a caller reads one error shape whichever half refused.  The
        keyword is carried through ``PydanticCustomError``, which is the only way
        a name from another vocabulary reaches ``errors()[0]["type"]``.

        The schema is the one this class names.  There is no lookup to get wrong
        and no second place to read one from.

        **``model_validate`` is the construction half for BOTH takers**, which is
        what makes one body enough: a ``RootModel`` validates its own root type
        through it, so a root model's accepted set is its document's exactly as a
        class's is, and a consumer writes ``X.strict_validate(payload)`` without
        knowing which of the two shapes ``X`` turned out to be.
        """
        _refuse_at(cls.__adcp_schema__, payload, cls.__name__)
        return cls.model_validate(payload)


class AdCPBaseModel(SchemaBound):
    """The base every emitted CLASS inherits.

    What is left here is the one thing that is a class's and not a root model's: the
    ``extra`` policy §2 of the semantics document derives from
    ``additionalProperties`` ("absent -> ``ignore``").  The schema half and the rule
    tuple are :class:`SchemaBound`'s, which §8 shares between this and
    :class:`AdCPRootModel`.
    """

    model_config = ConfigDict(extra="ignore", regex_engine=REGEX_ENGINE)


class AdCPRootModel(SchemaBound, RootModel[Any]):
    """§4's third root shape: a root that is neither a class nor an alias.

    ``docs/plan/architecture.md`` §8 declares it: "The semantics document's §4 now
    gives three shapes to a root model -- an array, a union mixing a scalar branch
    with a class branch, and a document stating no schema keyword -- and each must
    carry ``__adcp_schema__``, ``strict_validate`` and a rule tuple exactly as a
    class does, or a root model and a class disagree about what their document
    accepts.  So ``class AdCPRootModel(RootModel, RuleBound)`` joins
    ``AdCPBaseModel``."

    **Why a root model and not an alias for these three.**  §4 gives a root SCALAR a
    module-level ``Annotated`` alias, which has no class and so carries
    ``strict_validate`` as a module-level function (``strict_alias``).  That answer
    does not reach these three, and each for its own reason: a root ARRAY carries
    ``uniqueItems`` and ``contains``, which §2 hangs as RULES where no class sits
    above the value and an alias has no rule tuple; a MIXED root union has a class
    branch, and an alias cannot be a base for one; and a root stating no schema
    keyword at all admits every instance, which is a value and not an annotation a
    field can hold.  A root model carries all three, and it inherits the rule
    validator through :class:`SchemaBound`.

    ``RootModel[Any]`` and not bare ``RootModel``: a generic left unparameterised
    binds ``root`` to the type variable itself, and every emitted root model
    re-annotates ``root`` with the type its own document decides, which is what the
    renderer writes.  ``Any`` is what an unannotated root would admit anyway, so the
    parameter costs no accepted set and makes the base importable on its own -- which
    is what lets a document stating no schema keyword subclass it with no annotation
    of its own at all and still admit everything (§4's permissive root model).

    **Three facts about the MRO, each measured on the pinned pydantic rather than
    reasoned about**: the linearisation resolves with :class:`SchemaBound` first, so
    ``strict_validate`` is this class's and ``RootModel``'s construction half is
    reached through ``model_validate``; the rule validator FIRES, because
    ``_runtime.supplied`` reads ``__pydantic_fields_set__`` and a root model's one
    field is ``root`` -- so a rule keyed on ``"root"`` is evaluated exactly as a
    class's rule keyed on a property is; and ``model_json_schema()`` renders the ROOT
    TYPE's own schema with no wrapper object, so §8 of the semantics document pairs a
    root model against its document's node exactly as it pairs a class.
    ``tests/test_root_model.py`` is where each of the three is asserted.

    It declares ``regex_engine`` and not ``extra``: pydantic refuses an ``extra`` on
    a ``RootModel`` subclass, and a root model has no declared properties for the
    policy to be about -- while a ``pattern`` inside its root type needs the same
    engine every class and every alias uses, or this one shape's accepted set differs
    from its document's (:data:`REGEX_ENGINE`).
    """

    model_config = ConfigDict(regex_engine=REGEX_ENGINE)


#: The two errors a DISCRIMINATED union raises about the discriminating KEY rather than
#: about a branch: the key is absent, and the key's value names no branch.  Neither is a
#: draft-07 keyword and neither is a branch's own report, so
#: ``BranchDispatchMixin._no_branch`` answers both with the combinator.
_TAG_ERRORS = frozenset({"union_tag_not_found", "union_tag_invalid"})


class BranchDispatchMixin:
    """A union root's base: receiving a payload resolves it to the branch it satisfies.

    D2 makes a ``oneOf``/``anyOf`` root a base plus one subclass per branch, and the
    ROOT'S name binds the base -- so every referrer imports one symbol, and a caller can
    ``isinstance`` a received value against the arm it came back as.  Four parts, and each
    one exists because one of the others does not reach a path.  Each claim below was
    measured on this pydantic pin; the measurement is named beside it.

    **1. :meth:`__get_pydantic_core_schema__` installs the union as the VALIDATOR.**  That
    covers every path pydantic validates *through*: a nested field, a ``TypeAdapter``,
    ``model_validate``.  Overriding ``model_validate`` reaches one of those three, and most
    union roots are nested -- which is where an override leaves a document satisfying no
    branch to parse as a loose base.

    The schema returned is the base's OWN model schema wrapped in a function-wrap
    validator that dispatches to the union, rather than the union itself.  Both validate
    identically; the difference is what the class RENDERS.  A core schema that IS the union
    renders ``{"anyOf": [...]}`` and so states none of the root's own facts -- no ``type``,
    no ``description``, no ``additionalProperties`` -- and the verifier reads those
    off ``model_json_schema()``.  Measured: the union-as-top-schema form reports
    ``missing`` for ``/type`` and ``/description`` on every union root in the bundle, which
    is a model that drops a fact its document states.  A function-wrap takes its JSON
    schema from the schema it wraps, so wrapping the model schema states the root's facts
    and dispatches to the branches, and nothing has to put the document back into the model
    by hand.

    **2. :meth:`__new__` covers ``Base(**data)``**, which no schema can reach:
    ``BaseModel.__init__`` validates with ``self_instance=self``, so the object is already
    allocated when validation runs.  Measured without this method: ``Base(kind="b")``
    returns a ``Base`` -- validation passes, the union matched, and the instance is still
    the base -- and pydantic warns ``A custom validator is returning a value other than
    self``.  ``__new__`` asks the base's own validator, which IS that union, so all four
    paths refuse and resolve identically.  Direct construction therefore validates twice
    and is idempotent, and ``model_validate`` stays single-pass.

    It dispatches only when it was given data, because ``model_construct``, ``copy`` and
    pickle all call ``cls.__new__(cls)`` with none and must keep getting an allocation.
    That costs no coverage: ``Base()`` is still refused, by ``__init__``'s own validation
    against the union.

    **3. The base is the class that DECLARES ``_branch_models``**
    (``"_branch_models" not in cls.__dict__``).  A class that inherits it gets its own
    shape back, and that is the whole of subclass support: a branch keeps its own schema,
    and so does a consumer's refinement declared elsewhere
    (``class GetProductsRequest(BuyerRequest, LibraryGetProductsRequest)``).  Membership
    (``cls in cls._branch_models``) is NOT sufficient -- it admits both "is a branch" and
    "is an unrelated subclass", and only the second matters once the schema is being
    replaced.

    **4. The union is the validator and never the serializer.**  Put it in the
    serialization slot and the class has no serializer for an instance of itself: the
    union's serializer matches no branch, falls back to inferring a model, finds the same
    union and recurses.  Measured: ``model_dump_json`` on a base instance raises
    ``PydanticSerializationError: Circular reference detected`` and ``model_dump()``
    silently returns the model INSTANCE instead of a dict.  So the slot carries a wrap
    serializer, and it is set on the schema the wrapper HOLDS -- when the base's own schema
    comes back as a ``definitions`` node the key goes on the node inside it, because a
    ``serialization`` key on a ``definitions`` node is not consulted.

    **What that serializer is, settled 2026-10-27: it dispatches on the instance's own
    class and each class serialises through its own plain model schema**
    (:meth:`_serialise_as_itself`, which carries the three measurements).  A branch
    serialises the branch's fields, a base serialises the base's, and there is no union
    in the slot at all -- no arm to fail to match and nothing to infer, which is why it
    terminates.  The two readings it replaces each lost data in one direction: the
    base's model schema alone dropped a branch's own fields through a base-typed field,
    and the branches' union with that schema last left a base instance matching no arm.

    The branches subclass the base, so they do not exist while the base is being built: the
    hook returns the base's own schema then, and the declaring module calls
    ``model_rebuild(force=True)`` after the branches are defined to install the union.

    Three facts the emitter writes onto the base because they are not recoverable at
    runtime:

    * :attr:`_ROOT_REQUIRED` -- the fields the ROOT requires, as opposed to the ones that
      select a branch.  A combinator refusal reports every absent field with the two kinds
      mixed together and no intersection over those errors separates them.
    * :attr:`_BRANCH_DISCRIMINATOR` -- the property whose ``const`` selects the branch.
      A class holds a ``Literal`` per branch and nothing at runtime says which of the
      branches' shared ``Literal`` fields the DOCUMENT discriminates on; the emitter
      derives it from the branches (§4) and writes the answer.
    * :meth:`_branch_combinator` -- ``anyOf`` or ``oneOf``.  A refusal has to name a JSON
      Schema keyword, and a document satisfying no branch fails each branch at FIELD
      validation, where pydantic reports ``missing`` -- which is not in that vocabulary.
      A method and not a field, for D7's reason: pydantic does not let a model field shadow
      an attribute of the same name, so a document with a property called
      ``_branch_combinator`` would read the wrong one.
    """

    #: The branch classes, assigned by the declaring module after they are defined.
    #: Declared here so an inheriting class does not find it in its OWN ``__dict__``.
    _branch_models: ClassVar[tuple[type[BaseModel], ...]] = ()
    #: The root's own required fields, which a branch refusal must not be blamed on.
    _ROOT_REQUIRED: ClassVar[tuple[str, ...]] = ()
    #: The property whose ``const`` selects the branch, where the branches pin one
    #: (§4's first dispatch source).  DERIVED by the emitter from the branches
    #: themselves -- ``codegen.lower.union.discriminator`` -- and never declared here,
    #: so a branch added upstream moves it.  Empty where the branches pin none, and the
    #: union is then undiscriminated: see :meth:`_branch_adapter`.
    _BRANCH_DISCRIMINATOR: ClassVar[str] = ""

    @classmethod
    def _branch_combinator(cls) -> str:
        """The document's own union keyword.  The emitter overrides this per base."""
        return "oneOf"

    @classmethod
    def _dispatching(cls) -> bool:
        """Is ``cls`` the base whose shape the union replaces?  See part 3."""
        return bool(cls.__dict__.get("_branch_models"))

    @classmethod
    def _branch_adapter(cls) -> TypeAdapter:
        """A ``TypeAdapter`` over the branches, built once and held on the base.

        Built lazily rather than as a bare ``SchemaValidator`` over the union core schema
        the hook assembles: that schema references the branch models through definitions
        held by the generator that is still running, so building a validator from it raises
        ``SchemaError: definition ... was never filled``.  A ``TypeAdapter`` generates a
        complete schema of its own, once per base.

        **:attr:`_BRANCH_DISCRIMINATOR` is what makes the KEY select the branch.**  §4's
        first dispatch source: where every branch pins one shared property to a distinct
        ``const``, the union carries ``Field(discriminator=<property>)``, so pydantic reads
        that one key and reports against the branch it names instead of reporting one
        ``missing`` per field per branch.  Empty where the branches pin none, and the union
        is then plain -- which is a statement about THIS bundle's unions and not a
        fallback policy: a root whose branches overlap and pin nothing refuses in the
        emitter (``codegen.lower.union.discriminator``) rather than reaching a plain union
        here, because a branch chosen by trying each and keeping the first that validates
        is decided by declaration order rather than by the payload.
        """
        got = cls.__dict__.get("_branch_adapter_cache")
        if got is None:
            union = Union[cls._branch_models]  # noqa: UP007 -- a runtime subscript
            got = TypeAdapter(
                Annotated[union, Field(discriminator=cls._BRANCH_DISCRIMINATOR)]
                if cls._BRANCH_DISCRIMINATOR
                else union
            )
            cls._branch_adapter_cache = got  # type: ignore[attr-defined]
        return got

    @classmethod
    def __get_pydantic_core_schema__(cls, source: Any, handler: Any) -> Any:
        own = handler(source)
        if not cls._dispatching():
            return own
        # The branches are generated through the handler so their definitions are
        # registered in the schema this hook is contributing to; the VALIDATOR is the
        # adapter above, which is complete on its own.
        for branch in cls._branch_models:
            handler.generate_schema(branch)
        held = own["schema"] if own["type"] == "definitions" else own
        wrapped = core_schema.no_info_wrap_validator_function(
            lambda value, _handler: cls._dispatch(value),
            held,
            serialization=core_schema.wrap_serializer_function_ser_schema(
                cls._serialise_as_itself, schema=held, info_arg=True
            ),
        )
        return {**own, "schema": wrapped} if own["type"] == "definitions" else wrapped

    @classmethod
    def _serialise_as_itself(cls, value: Any, nested: Any, info: Any) -> Any:
        """§4's fourth mechanic: **a value serialises as what it is.**

        The serialiser dispatches on the INSTANCE'S OWN CLASS and each class serialises
        through its own plain model schema -- settled 2026-10-27, after both of the
        readings the mechanic's old sentence admitted were measured and both lost data.
        An instance of ``cls`` goes through ``nested``, which is the base's own plain
        model schema (the one the wrap validator holds); anything else is a branch or a
        consumer's refinement, and its own class's serialiser IS its own plain model
        schema, because this hook returns ``own`` unchanged for every class that does
        not DECLARE ``_branch_models`` (part 3).

        There is no union in this slot, which is why it terminates: no arm to fail to
        match and nothing to infer.  **Both of the readings it replaces were measured on
        this tree.**  With the base's model schema ALONE in the slot, a branch reached
        through a base-typed field came back as the base's fields and the branch's own
        were dropped silently.  With the branches' union plus that schema, a base
        instance matched no arm -- ``own["type"]`` is ``definitions`` for 12 of the 13
        field-carrying bases, so the base's arm is a ``definition-ref`` the union
        serialiser does not match an instance against -- and the fallback inferred a
        model, found this same class and recursed: ``PydanticSerializationError:
        Circular reference detected``.  A base instance is a legitimate value, because
        ``__new__`` covers ``Base(**data)`` and validates it, so the slot owes it an
        answer rather than treating it as unreachable.

        The branch's serialiser is asked in the MODE and with the flags this call is
        being made in, read off ``info``: a dispatch that dropped them would make
        ``model_dump_json`` of a base-typed field disagree with ``model_dump`` of the
        same value about dates, aliases and excluded keys.  ``exclude``/``include`` are
        not among them -- they are relative to the FIELD being serialised and pydantic
        has already applied this field's own -- which is the one place this dispatch is
        narrower than the schema it replaces.
        """
        if type(value) is cls:
            return nested(value)
        return type(value).__pydantic_serializer__.to_python(
            value,
            mode="json" if info.mode_is_json() else "python",
            by_alias=info.by_alias,
            exclude_unset=info.exclude_unset,
            exclude_defaults=info.exclude_defaults,
            exclude_none=info.exclude_none,
            round_trip=info.round_trip,
            context=info.context,
            serialize_as_any=info.serialize_as_any,
        )

    @classmethod
    def _dispatch(cls, value: Any) -> Any:
        try:
            return cls._branch_adapter().validate_python(value)
        except ValidationError as err:
            raise cls._no_branch(value, err) from None

    @classmethod
    def _no_branch(cls, value: Any, err: ValidationError) -> ValidationError:
        """The refusal for a payload no branch admits, named in the DOCUMENT'S vocabulary.

        A root-required field that is absent is reported as ``required`` at its own
        location, because that is what the document refuses on and it is not the branches'
        doing.  Anything else is the combinator: the payload reached the union and no
        member took it.  ``err`` is not re-raised -- it carries one ``missing`` per field
        per branch, which names a keyword the document does not use.

        **Except where the union is DISCRIMINATED, and that exception is the whole point
        of deriving the discriminator** (§4: "the key alone selects the branch, so Pydantic
        reports against that branch rather than against all of them").  With
        :attr:`_BRANCH_DISCRIMINATOR` set, a payload whose key names a branch is validated
        against THAT branch and nothing else, so ``err`` is that branch's own report in the
        document's own vocabulary -- ``required`` for a field the branch requires, a
        ``const``'s ``literal_error`` for a value it pins -- and replacing it with
        "is not valid under any of the N branches" throws away the one thing the
        derivation bought.  The two errors pydantic raises about the KEY rather than about
        a branch (``union_tag_not_found``, ``union_tag_invalid``) are NOT a branch's
        report and are not a draft-07 keyword either, so they keep going through the
        combinator below.  Decided by the error TYPE and never by its message, for
        ``codegen.refusal.Kind``'s reason.
        """
        absent = (
            [k for k in cls._ROOT_REQUIRED if k not in value] if isinstance(value, Mapping) else []
        )
        if not absent and cls._BRANCH_DISCRIMINATOR and not any(
            e["type"] in _TAG_ERRORS for e in err.errors()
        ):
            return err
        details = [
            InitErrorDetails(
                type=PydanticCustomError(
                    "required", "{detail}", {"detail": f"{key!r} is a required property"}
                ),
                loc=(key,),
                input=value,
            )
            for key in absent
        ] or [
            InitErrorDetails(
                type=PydanticCustomError(
                    cls._branch_combinator(),
                    "{detail}",
                    {"detail": f"is not valid under any of the {len(cls._branch_models)} branches"},
                ),
                loc=(),
                input=value,
            )
        ]
        return ValidationError.from_exception_data(cls.__name__, details)

    def __new__(cls, *args: Any, **data: Any) -> Any:
        if data and cls._dispatching():
            return cls.__pydantic_validator__.validate_python(data)  # type: ignore[attr-defined]
        return super().__new__(cls)
