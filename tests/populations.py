"""The document-set predicates each step's result was stated over.

``docs/plan/architecture.md`` §5 puts them here: "Root and non-root are one path.
There is no second table of root selectors. ... **The document-set predicates a step's
result was stated over are the tests' business and live under ``tests/``.**"

They were in ``codegen/bundle.py``, six of them doubling as the selectors of
``emit.ROWS``, and §14 step 5 deletes both halves of that arrangement:

* as SELECTORS they were the second reading of a node's kind -- §11's repetition table
  names them in one row with the walk's own dispatch ("the kind read in ``_decide``, in
  the root selectors, in ``union.keyword``, in ``rules.presence_only`` | ``parse``'s
  classification") -- and the walk now reads a root's kind exactly once, at ROOT, in
  ``emit._decide``;
* as POPULATIONS they are measurements a test states its claim over, and a measurement
  is not a decision the compiler makes.

**Two of them were also the only reason ``codegen/bundle.py`` imported a LOWERING**:
``union_root`` reads ``lower.union.keyword`` and ``states_an_object_rule`` reads
``lower.rules.presence_only``, so ``import codegen.bundle`` reached eight ``codegen``
modules.  With them here it reaches two, which is what let the JSON Pointer speller move
into ``bundle.py`` and ``codegen.compiler`` leave §9's permitted set for the verifier
(``tests/test_import_rule.py``).

**These are predicates over a DOCUMENT and nothing here is a dispatch.**  A root is
still exactly one kind -- that is draft-07's own fact and the walk's arms read it -- but
nothing claims a document any more, so two predicates answering yes for one document is
an overlap in two measurements and not a build failure.  What used to keep them
disjoint, ``declares_its_own_root_kind``, is kept for the same reason the predicates are:
the populations each step's numbers were stated over are the ones with the clause in
them, so a test re-stating one of those numbers must count the same set.
"""

from __future__ import annotations

from codegen import bundle, compiler
from codegen.lower import rules, union


def declares_its_own_root_kind(doc: dict) -> bool:
    """Does the root declare a kind of its OWN, which one of the specific predicates
    below counts?

    A root is exactly ONE kind, and each keyword here decides it whatever else the root
    declares: an ``enum`` at the root makes the document an enumeration though its
    ``type`` names a scalar; an ``allOf`` at the root makes it a composition though it
    declares ``properties`` as well -- a draft-07 root ``allOf`` applies to the whole
    instance, so reading the properties without the conjuncts would drop the bases; and
    a ``oneOf``/``anyOf`` at the root makes it a union whatever else it declares, for
    the same reason read the other way round.

    Measured, so each clause is known to be load-bearing rather than defensive: without
    the union clause :func:`is_object_root` and :func:`union_root` both answer yes for
    35 documents and :func:`is_scalar_root` and :func:`union_root` both for 1; without
    the ``allOf`` clause the object predicate overlaps step 4's.
    """
    return is_enum_root(doc) or isinstance(doc.get("allOf"), list) or union_root(doc)


def is_object_root(doc: dict) -> bool:
    """A plain object root -- ``properties``, and no kind of its own."""
    return (
        "properties" in doc
        and doc.get("type") in (None, "object")
        and not declares_its_own_root_kind(doc)
    )


def is_scalar_root(doc: dict) -> bool:
    """A root whose ``type`` names one scalar, and NOT an enumeration.

    ``"enum" not in doc`` arrives through :func:`declares_its_own_root_kind` and is the
    load-bearing clause rather than a belt: all 214 of the bundle's root enums declare
    ``type: "string"``, so without it this and :func:`is_enum_root` count the same 214
    documents.
    """
    return (
        isinstance(doc.get("type"), str)
        and doc["type"] in compiler.SCALAR
        and not declares_its_own_root_kind(doc)
    )


def is_enum_root(doc: dict) -> bool:
    """The root itself carries an ``enum``.

    A DIFFERENT predicate from ``bundle.carries_an_enum``, and it IMPLIES it -- the root
    carrying an enum is a node carrying an enum -- and the two are not interchangeable:
    535 documents carry an enum somewhere and only 214 carry one at the root.
    """
    return "enum" in doc


def is_container_root(doc: dict) -> bool:
    """The root is a container: an array, a mapping (an object declaring no property),
    or a multi-type node.

    **The exclusion is load-bearing and step 6's own count was over the predicate
    WITHOUT it.**  Measured both ways on the 3.2 bundle: the bare shape test selects 37
    documents (32 mappings, 5 arrays, 0 multi-type), and 28 of those 32 mappings declare
    a union at the root as well.  The union owns them for the reason
    :func:`declares_its_own_root_kind` states.  With it, this population is 9 (5 arrays,
    4 mappings), overlapping neither ``bundle.is_leaf_object`` nor
    ``bundle.references_a_property`` in a single document.
    """
    kind = doc.get("type")
    if declares_its_own_root_kind(doc):
        return False
    if isinstance(kind, list):
        return True
    return kind == "array" or (kind == "object" and "properties" not in doc)


def composes_at_the_root(doc: dict) -> bool:
    """A root carrying ``allOf`` with NO union beside it.

    **301 documents**, and the definition is what lands on that number: the other
    readings give 342 (any root ``allOf``, union or not), 401 (``allOf`` anywhere in the
    document) and 257 (``allOf`` at the root and nowhere else).  A verdict read off a
    population nobody counted is a verdict over however many documents there turned out
    to be.

    The union clause is not a convenience: a ``oneOf``/``anyOf`` root is step 5's
    whatever ELSE it carries, because the root ``allOf`` of a draft-07 document applies
    to the whole instance and therefore to every branch -- which is what §5's ``allOf``
    row states as "beside a union → the same, onto the base", and what
    ``nodes.Union.siblings`` carries.  ``emit._decide`` reads the union arm BEFORE the
    ``allOf`` arm for exactly that reason.

    **"A union beside it" IS :func:`union_root`**, which asks the lowering
    (``union.keyword`` plus ``rules.presence_only``) and answers no for a combinator of
    ``required`` GROUPS -- a rule on one class, not a union of shapes.  Reading it as
    "the key is present" instead left a 14-document hole: such a root was excluded here
    for having a union and excluded from step 5 for not having one.
    """
    return isinstance(doc.get("allOf"), list) and not union_root(doc)


def union_root(doc: dict) -> bool:
    """A document whose root carries ``oneOf`` or ``anyOf`` over SHAPES.

    156 of the 3.2 bundle's 1,054 portable documents carry one of the keywords, and 0 of
    them carry both.

    ONE implementation of the keyword read, and it is the LOWERING'S:
    ``lower.union.keyword`` is what ``emit._decide``'s union arm reads the keyword with,
    so this measurement and the walk cannot disagree about what a union is.

    A combinator of ``required`` GROUPS is not a union: a branch declaring no property
    has no shape to subclass -- ``lower.union._plan`` refuses exactly that -- so such a
    root is a rule on one class (D6) and ``compiler.lower_object`` reads it.  Both
    readings are each step's own and they meet here.
    """
    kw = union.keyword(doc)
    return kw is not None and not rules.presence_only({kw: doc[kw]})


def states_an_object_rule(doc: dict) -> bool:
    """Step 7's population: an object root whose composition is a rule about PRESENCE.

    The three clauses:

    * no ``$ref``, ``allOf``, ``definitions`` or ``$defs`` anywhere.  That is steps 2
      and 4, and it is also what keeps this out of ``bundle.references_a_property``,
      which selects on a reference EXISTING.
    * at least one ``if``/``then``/``else``/``not``/``oneOf``/``anyOf``.  Those six are
      exactly the keywords ``bundle.is_leaf_object`` excludes, so a document satisfying
      this clause is not step 1's.  ``dependencies``, ``min``/``maxProperties`` and
      ``uniqueItems`` do NOT appear in that clause on purpose: ``is_leaf_object``
      already counts a document carrying only those.  ``core/format-id.json`` is such a
      document -- step 1's population, refused there until step 7, emitted now.
    * every combinator in it is ``required``-only (``rules.presence_only``).  That is
      the step-5 boundary: a combinator of SHAPES is a union root and step 5's, a
      combinator of ``required`` groups has no shape to subclass and is a rule.  The
      test is the lowering's own reading, so this cannot count a document the walk
      cannot lower.
    """
    if "properties" not in doc or doc.get("type") not in (None, "object"):
        return False
    kw = bundle.schema_keywords(doc)
    if kw & {"$ref", "allOf", *bundle.DEFINITIONS}:
        return False
    if not kw & {*bundle.CONDITIONAL, "oneOf", "anyOf"}:
        return False
    return all(rules.presence_only(n) for _, n in bundle.nodes(doc))
