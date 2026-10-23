"""An ``allOf`` node: the reference conjuncts become BASES, and the rest becomes
fields of the node itself.

D2's product row.  **The node need not be a root**, and the lowering never asked
that it be one: it takes ``(node, name, pointer, module)`` like every other
lowering (D13), reads the pointer it is handed, and ``declare_object`` names
whatever node that is.  A document ROOT reaches it through ``emit.ROWS``; a
composition at a property or deeper reaches it through ``emit._decide``'s own branch,
because ``ROWS`` dispatches on ROOT KIND and a node that is not a root has no row
to be and no selector to select it.  Measured over the 3.2 bundle: of the 67
documents whose composition this step was deferring, 41 carry it at a root -- all
41 claimed by ``union_root``, not by this step's selector -- 10 at a property and
16 deeper.

Two things come out of one conjunct list, and a third is deliberately absent:

* a conjunct that is a ``$ref`` and nothing else is a BASE CLASS.  D7: a base is
  DERIVED from what the document composes, so there is no marker policy and no
  filename to classify.  Anything a caller wants to ``isinstance`` against is a
  schema the document composes, which is also how ``AdcpRequest``/``AdcpResponse``
  reach a task message -- through ``index.json``'s task registry naming the
  document, never through its path;
* a conjunct carrying ``properties`` declares fields of THIS node, because a
  draft-07 ``allOf`` conjunct applies to the same instance -- it is not a separate
  object and gets no class of its own;
* a ``required``-only conjunct is the plan's third output here and is NOT built:
  there are **0** of them at a root over the whole bundle (measured, asserted in
  the suite), so the arm would be a derivation matching nothing, which is green
  for free and says nothing.

Anything else refuses by name, pointer and keyword.

**A subclass never restates an inherited field's TYPE.**  That is this module's one
merge rule: a restatement states the field only when it NARROWS, meaning it keeps
every keyword the inherited declaration states, with the same value, and adds at
least one more.  A restatement that says something DIFFERENT about the instance is a
conflict and the document is refused.  A restatement that says the same thing or
nothing is the subclass's field by its ANNOTATIONS alone, over the base's own type:
the node where the two agree, the base's decided field where the restatement states
no constraint at all.  :func:`_restatement` is the whole of that decision, and it is
SYMMETRIC, so there is no order-dependent "last wins" to come back to -- a generator
that let the later conjunct win made its accepted set a function of member order.

MEASURED over this step's 287 documents, 100 sites restate an inherited property:
51 restate it identically, 31 state nothing but ``default`` and ``description``,
16 point a ``$ref`` at a fragment of the base's own node, and 2 add a keyword.
**The 31 are this step's highest-value defect** -- in the previous generated tree
they were 31 of 42 ``Any`` fields, each one shadowing a typed base field across 15
classes.  ``formats/canonical/responsive_creative.json`` is the control shape:
it restates ``experimental``, ``v1_translatable`` and ``slots`` with nothing but a
default and a description, while ``formats/canonical/_base.json`` types them
``boolean``, ``boolean`` and ``array``, so a restatement lowered on its own is
``Any | None`` shadowing a typed base field.  **Re-using the base's decided field
makes the shadow unspellable AND carries the document's own annotation**, which
inheriting the field entirely did not: that left the class stating the BASE's
``default`` and ``description`` at a pointer its own document declares, the 28
``differs`` of ``salesagent-j3k2l.36`` and two of them inversions.

The same rule closes the inventory's "41 subclass fields optional where their base
requires them" by construction: a field the subclass does not declare keeps the
base's requiredness, because there is nothing of the subclass's to override it.  A
field it DOES narrow keeps it too -- the inherited required set is unioned in.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from codegen.compiler import (
    ANNOTATIONS,
    Module,
    Property,
    Shape,
    Target,
    Type,
    check_keywords,
    conditional_only,
    declare_object,
    fields,
    rules_at,
)
from codegen.refusal import Kind, Refusal

#: What a conjunct may carry and still be an inline object declaring fields.
#: ``additionalProperties`` is absent on purpose: D8 derives ``extra`` from the
#: ROOT's, and a conjunct carrying a second one would be a second source for one
#: class attribute.  There are 0 such conjuncts over the population, so this
#: refuses rather than choosing between them.
INLINE = frozenset({"type", "properties", "required"})

#: What the composing node itself may carry beside its conjunct list.
#:
#: D6's rule families are NOT listed here and are added per node by
#: ``compiler.rules_at``, because the admissible set is a function of the node: a
#: ``oneOf``/``anyOf`` is a rule only where every branch is ``required``-only, and a
#: combinator of shapes admitted here would emit a class that drops it silently.
COMPOSING = frozenset({"type", "allOf", "properties", "required", "additionalProperties"})

#: The two combinators, asked about by name because a composing node can carry one.
_COMBINATORS = ("oneOf", "anyOf")


def _refuse_a_combinator_of_shapes(doc: dict, pointer: str, screen: frozenset[str]) -> None:
    """A node that COMPOSES and also carries a combinator of SHAPES.

    Both halves are conjunctions with the same instance in draft-07 -- that is D7's own
    wording for ``allOf`` -- and a class can carry the conjuncts, as bases and as fields,
    while nothing on a class carries the combinator: the branches are satisfied by SOME
    instance, so neither a base nor a field states one.  So this is ``union.ROOT_CONJUNCTS``
    read from the other side, and the refusal is the same shape: emitting it needs a row
    that can NAME the conjunction of a conjunct list with a branch list, and there is no
    JSON pointer to that conjunction for the class to name.

    **Asked of ``rules_at``'s own screen and not of a second predicate.**  A
    ``oneOf``/``anyOf`` is a RULE where every branch states only which keys are present
    and a union of shapes otherwise; ``rules.presence_only`` is that one test and
    ``compiler.rules_at`` subtracts the two combinators from the screen when it fails.
    Reading the screen is how this row asks the question without importing a sibling
    lowering (D13), and it is why there is no second reading to drift from.

    **What this changes is the REASON and not the accepted set.**  A combinator the screen
    subtracted was already refused by ``check_keywords`` below -- with
    ``DEFERRED_TO_A_LATER_ROW``, which promises a row for a position that needs a
    pointer no document has.  Measured: ``creative/list-creatives-response.json``
    ``#/properties/creatives/items`` is the one document of the deferred population here,
    and its two branches are ``{"required": [...], "not": {...}}`` -- every one of which
    constrains only which keys are present, so what sends it down this path is
    ``rules._required_only`` admitting ``{"required"}`` ALONE.  Widening that predicate
    moves ``rules.presence_only``, which ``bundle.states_an_object_rule`` is BUILT ON as a
    row's selector, so it is a change to a population and not to this row.
    """
    for keyword in _COMBINATORS:
        if isinstance(doc.get(keyword), list) and keyword not in screen:
            raise Refusal(
                keyword,
                pointer,
                f"this node composes AND carries a {keyword} whose branches are shapes "
                "rather than presence groups (rules.presence_only), and both are "
                "conjunctions with the same instance: a class carries the conjuncts as "
                "bases and fields, and nothing on a class carries a branch list, because "
                "a branch is satisfied by SOME instance.  There is no pointer to the "
                "conjunction of the two for the class to name, which is what "
                "union.ROOT_CONJUNCTS refuses a root union's own conjuncts for",
                kind=Kind.VERDICT,
            )


def lower_composition(doc: dict, name: str, pointer: str, mod: Module) -> str:
    """Append the class for an ``allOf`` node and return its name.

    **The node's own D6 rules reach the class through** ``declare_object``, which
    writes the tuple for whatever node it is declaring -- so this row states nothing
    about rules beyond admitting the keywords.  Documents refused here on ``not``,
    ``dependencies`` or ``minProperties`` at a composing node whose mechanism was
    complete three modules away: the rule kinds, the emitter's tuple and the one
    after-validator all existed, and only the object row consulted them.

    A property the node declares only inside a conditional is merged in for the
    reason ``compiler.Rules`` states: a rule naming a key the class has no field for
    refuses a payload the document admits.
    """
    # **The TYPE first, BEFORE the keyword screen**, and the order is measured rather
    # than preferred: a node stating a non-object ``type`` composes no object whatever
    # else it states, so the type is the reason and a keyword it carries is not.  It sat
    # after the screen, and ``compiler.check_keywords`` walks ``sorted(node)`` -- so
    # ``media-buy/legacy-purchase-continuation-input.json#/properties/accepted_losses``,
    # a composing ARRAY, was reported on ``items`` with "a later D2 row does", which
    # promises a row for an array keyword at a node no array row will ever see.  The same
    # misattribution ``union.ROOT_HANDLED`` measured at 55 of 156 and fixed the same way.
    # Measured over every node of every portable document: **4 composing nodes state a
    # non-object type and all 4 state ``array``**; all 4 already refused here, so the
    # order moves no document and changes the reported keyword for one.
    if doc.get("type") not in (None, "object"):
        raise Refusal(
            "type",
            pointer,
            f"an allOf of type {doc['type']!r} composes no object",
            kind=Kind.VERDICT,
        )
    stated = rules_at(doc)
    _refuse_a_combinator_of_shapes(doc, pointer, stated.screen)
    check_keywords(doc, pointer, COMPOSING | stated.screen)

    bases: list[str] = []
    inherited: dict[str, dict] = {}
    inherited_required: set[str] = set()
    #: The FIELD each inherited key came out as on the base that declares it, and the
    #: base it came from.  Read only by the annotation-only arm below, which re-uses
    #: the field rather than re-deciding the node; ``compiler.Shape.decided`` says why.
    inherited_fields: dict[str, Property] = {}
    inherited_from: dict[str, Target] = {}
    #: Every LOCAL declaration that won its key, and where it was declared.  The
    #: root's own properties and an inline conjunct's land in the SAME map,
    #: because draft-07 applies both to the same instance.
    local: dict[str, dict] = {}
    at: dict[str, str] = {}
    required: set[str] = set(_required(doc, pointer))
    #: The conjuncts that state a RULE of this node rather than a base or fields.
    conjunct_rules: list[dict] = []

    def declare(key: str, node: Any, where: str) -> None:
        prior = local.get(key)
        if prior is None:
            local[key], at[key] = node, where
            return
        # Two local declarations of one key: the root's own and a conjunct's, or
        # two conjuncts'.  Decided by the SAME rule as a restatement of an
        # inherited field, and that rule is symmetric, so which was read first
        # cannot change the answer.  The narrower declaration wins; neither
        # narrowing the other refuses.  One site over the population:
        # ``formats/canonical/image.json`` states ``motion_level`` as a ``$ref``
        # at the root and as an ``enum`` in a conjunct, which is the enum
        # narrowing and refuses here -- the intersection needs step 3's enum
        # lowering and cannot be stated from this row.
        if _restatement(node, prior):
            local[key], at[key] = node, where
        elif _restatement(prior, node) is None:
            raise Refusal(
                _disagreeing(node, prior),
                where,
                f"{key!r} is declared at {at[key]} and again here, and neither "
                "declaration narrows the other",
                kind=Kind.VERDICT,
            )

    for key, sub in (doc.get("properties") or {}).items():
        declare(key, sub, f"{pointer}/properties/{key}")

    for i, conjunct in enumerate(doc["allOf"]):
        where = f"{pointer}/allOf/{i}"
        if not isinstance(conjunct, dict):
            raise Refusal("allOf", where, "a conjunct that is not a schema", kind=Kind.VERDICT)
        keys = {k for k in conjunct if k not in ANNOTATIONS and not k.startswith("x-")}
        if keys == {"$ref"}:
            target = mod.bind(conjunct["$ref"], where)
            if target.shape is None:
                raise Refusal(
                    "allOf",
                    where,
                    f"{target.symbol} is not a class, so it cannot be a base "
                    "(D2 makes a scalar root an Annotated alias, and subclassing "
                    "one is a TypeError at import)",
                    kind=Kind.VERDICT,
                )
            mod.imports.add((target.module, target.symbol))
            bases.append(target.symbol)
            inherited.update(target.shape.properties)
            inherited_fields.update(target.shape.decided)
            inherited_from.update(dict.fromkeys(target.shape.properties, target))
            inherited_required |= target.shape.required
            continue
        if "properties" in keys and keys <= INLINE:
            check_keywords(conjunct, where, set(INLINE))
            if conjunct.get("type") not in (None, "object"):
                raise Refusal(
                    "type",
                    where,
                    f"a conjunct of type {conjunct['type']!r} is not one",
                    kind=Kind.VERDICT,
                )
            if not isinstance(conjunct["properties"], dict) or not conjunct["properties"]:
                raise Refusal(
                    "properties",
                    where,
                    "a conjunct declaring no property",
                    kind=Kind.VERDICT,
                )
            for key, sub in conjunct["properties"].items():
                declare(key, sub, f"{where}/properties/{key}")
            required |= set(_required(conjunct, where))
            continue
        if keys and keys <= rules_at(conjunct).screen:
            # **A conjunct that states only a RULE is a rule of THIS node**, by the
            # same draft-07 fact the arm above rests on: a conjunct applies to the
            # same instance, so it is not a separate object and gets no class of its
            # own.  The arm above reads a conjunct's ``properties`` as this node's
            # fields; this reads its ``not``, ``if``/``then``/``else``,
            # ``dependencies`` or ``min``/``maxProperties`` as this node's rule.
            #
            # Measured, and it is why this arm exists rather than the root arm alone:
            # all 20 documents whose ROOT carries a rule keyword ALSO carry a
            # rule-bearing conjunct, so admitting the root's keyword on its own moved
            # every one of them from a refusal on ``not``/``dependencies`` to a
            # refusal on ``not``/``if`` one pointer deeper and emitted none.  The two
            # positions are one unit.
            #
            # Screened by the conjunct's OWN ``screen`` at its OWN pointer, so a
            # conjunct carrying a combinator of SHAPES still refuses here (step 4's
            # deferral, ``salesagent-j3k2l.18``) rather than being emitted with the
            # combinator dropped.
            conjunct_rules.append(conjunct)
            continue
        if "$ref" in keys:
            # A conjunct that is a ``$ref`` AND something else: refused on the
            # SIBLING, which is the cause, and never on ``$ref``, which is only
            # the position.  The same reading ``emit.decide_type`` applies to a
            # reference used as an annotation -- draft-07 says a ``$ref`` IGNORES
            # its siblings, while the resolver the harness grades through MERGES
            # them, so a document with one would be graded against a schema it
            # does not mean whichever way the base was bound.
            raise Refusal(
                min(keys - {"$ref"}),
                where,
                "a sibling of $ref, which draft-07 ignores",
                kind=Kind.VERDICT,
            )
        raise Refusal(
            min(keys) if keys else "allOf",
            where,
            "this step lowers a $ref conjunct (a base) or an inline conjunct with "
            "properties; a later D2 row lowers this one",
            kind=Kind.DEFERRED,
        )

    # A property only a conditional names, read over the rule-bearing conjuncts as well
    # because most of this population states its conditional there and not at the root.
    # A key NOTHING else declares refuses: it has no field to be and no fact to state,
    # and ``compiler.conditional_only`` carries both halves of why.  A key that IS
    # declared somewhere -- the root's own ``properties``, an inline conjunct's, or an
    # inherited base's -- needs nothing here: the conditional is then a restatement of a
    # declaration the document has, and that declaration is the one that stands.
    stated = rules_at(doc, *conjunct_rules)
    conditional_only(stated, {*local, *inherited}, pointer)

    own: dict[str, dict] = {}
    #: The keys whose field is the inherited one wearing this document's annotations.
    reuse: dict[str, Property] = {}
    for key, node in local.items():
        if key not in inherited:
            own[key] = node
            continue
        verdict = _restatement(node, inherited[key])
        if verdict is None:
            raise Refusal(
                _disagreeing(node, inherited[key]),
                at[key],
                f"the restatement of {key!r} neither matches nor narrows the "
                f"inherited declaration: inherited states {sorted(_constraining(inherited[key]))}, "
                f"this states {sorted(_constraining(node))}",
                kind=Kind.VERDICT,
            )
        if verdict or (key in required and key not in inherited_required):
            # It narrows, so the subclass is the one that states it -- and **a
            # REQUIREDNESS the base does not have is a narrowing too**, which is the
            # half this read for as long as requiredness lived in ``required`` rather
            # than in the declaration ``_restatement`` compares.  Left inherited, the
            # field keeps the base's optionality while the composing document's own
            # ``required`` names it, so the class ACCEPTS A PAYLOAD THE DOCUMENT
            # REFUSES and renders a ``default: None`` the document does not state.
            # Measured on this tree: 2 documents and 2 pairs --
            # ``core/tasks-get-response.json`` and
            # ``protocol/get-task-status-response.json``, whose ``task_id`` is optional
            # on ``core/protocol-envelope.json`` and required at their own root -- and
            # they were the last 2 ``added`` facts of the symmetric comparison.
            own[key] = node
        elif _annotates_differently(node, inherited[key]):
            # **It states the same thing about the INSTANCE and a different thing to the
            # READER**, so the subclass states the field: a document's own declaration
            # governs the annotation at its own pointer (the description-authority rule,
            # ``docs/plan/rebuild-plan.md`` §6), and a base's must not stand where the
            # document declares one itself.
            #
            # ``_restatement`` returned False here, so the restatement's own
            # constraining content is either EQUAL to the base's or EMPTY, and the two
            # reach the base's content by different routes:
            #
            # * **EQUAL** -- the node says what the base says about the instance, so
            #   ``decide_type`` reading the node decides the base's own type and there
            #   is no shadow to be had.  15 pairs and 15 documents, every one a response
            #   root composing ``core/protocol-envelope.json`` and declaring ``context``
            #   itself as a bare ``$ref`` to ``core/context.json``: the envelope states
            #   the long "Relationship to per-task body-level ``context`` declarations"
            #   text as a SIBLING of its own ``$ref``, the 15 documents state the
            #   target's own short text at the pointer the comparison grades, and they
            #   were 15 of the 43 ``differs``.
            # * **EMPTY** -- the node says nothing about the instance, so it is the
            #   inherited FIELD that stands and only the annotations are this
            #   document's.  A previous reading left this shape inherited entirely, on
            #   the ground that lowering the restatement ALONE types it ``Any`` and
            #   drops every fact the base states.  That is true of the restatement
            #   alone, and the answer is to not lower it alone: the base's decided
            #   field is re-used (``compiler.Shape.decided``, and ``fields``' ``reuse``
            #   says why the node cannot simply be merged and re-decided).  Measured as
            #   the whole of ``salesagent-j3k2l.22``'s residue: 28 ``differs`` over 7
            #   ``formats/canonical/*.json`` at ``experimental``, ``v1_translatable``
            #   and ``slots``, two of them INVERSIONS where the base defaults a boolean
            #   the opposite way from the document's own declaration.
            #
            # **The two also differ about SILENCE**, and each takes the reading under
            # which the model states what the COMPOSED DOCUMENT states at that pointer.
            # An EQUAL restatement's node resolves to something of its own -- all 15 are
            # a bare ``$ref``, and the resolved document carries the target's
            # annotations inline there -- so the document's conjunction gap-fills
            # nothing and the base's annotation must not stand
            # (:func:`_annotates_differently`).  An EMPTY one resolves to nothing of its
            # own, so under ``allOf`` the base's declaration is the one that applies
            # where the restatement is silent, and the composed document states it:
            # measured on ``formats/canonical/responsive_creative.json``, whose
            # ``slots`` restates a ``default`` and no ``description``, where reading the
            # restatement's silence as an answer left the base's description reported
            # ``missing`` instead of zero facts.
            own[key] = node
            if not _constraining(node):
                reuse[key] = _reused(key, inherited_fields, inherited_from, at[key], mod)
                own[key] = {
                    **{k: v for k, v in inherited[key].items() if k in RENDERED},
                    **node,
                }
        # Otherwise it adds nothing and the field is INHERITED: no line, no shadow.

    decided = fields(
        own,
        required | (inherited_required & set(own)),
        pointer,
        name,
        mod,
        inherited=set(inherited),
        declared_at=at,
        # D6 has claimed the ``uniqueItems`` of these keys, whether the node stating
        # it is this one or a rule-bearing conjunct: the rule tuple and the strip are
        # two halves of one claim, so the row that writes the tuple passes the keys.
        distinct=stated.distinct,
        reuse=reuse,
    )
    return declare_object(
        doc,
        name,
        pointer,
        mod,
        decided,
        # ``decided`` is what this class INHERITS; ``declare_object`` overlays the
        # fields it is handed, which are this class's own.  Passing the inherited ones
        # is what makes :attr:`Shape.decided` transitive the way ``properties`` is, so
        # a sub-subclass restating a key its grandparent declares reads one map.
        Shape(
            {**inherited, **own},
            frozenset(required | inherited_required),
            decided=inherited_fields,
        ),
        bases=tuple(bases),
        rule_nodes=conjunct_rules,
    )


def _required(node: dict, pointer: str) -> list[str]:
    req = node.get("required", [])
    if not isinstance(req, list) or not all(isinstance(r, str) for r in req):
        raise Refusal(
            "required",
            pointer,
            f"required is {req!r}, not a list of names",
            kind=Kind.VERDICT,
        )
    return req


def _reused(
    key: str,
    inherited_fields: Mapping[str, Property],
    inherited_from: Mapping[str, Target],
    pointer: str,
    mod: Module,
) -> Property:
    """The inherited field an annotation-only restatement re-states, importable here.

    A re-used type names symbols, and each one has to be IMPORTABLE from this module
    or the class is an undefined name at import.  The only module this row knows for
    the key is the one its ``$ref`` conjunct bound, so a symbol that module DECLARES
    is imported from it and anything else refuses by name.  The second case is a
    re-export -- the base merely imported the symbol itself -- and section 2's import
    rule is an import of a symbol the target declares; ``emit.emit``'s binder refuses
    the same shape for a fragment ``$ref``, with the same reasoning.

    Measured over this step's population: 3 keys re-use a field, all 3 on
    ``formats/canonical/_base.json`` -- ``experimental`` and ``v1_translatable`` name
    no symbol at all (``bool``), and ``slots`` names ``CanonicalFormatBaseSlotsItem``,
    which ``_base`` declares.  **0** re-use a type naming a re-exported symbol, so the
    refusal below fires on nothing today and is the loud answer when a document first
    reaches one.
    """
    held, source = inherited_fields.get(key), inherited_from.get(key)
    if held is None or source is None:
        raise Refusal(
            "properties",
            pointer,
            f"{key!r} restates an inherited declaration with nothing but annotations, "
            f"and the base declaring it recorded no decided field for it, so there is "
            f"no type to re-use and lowering the restatement alone would type it Any",
            kind=Kind.VERDICT,
        )
    wanted = _symbols(held.type)
    unplaceable = sorted(wanted - source.shape.declares) if source.shape else sorted(wanted)
    if unplaceable:
        raise Refusal(
            "properties",
            pointer,
            f"{key!r} re-uses the field of {source.symbol}, whose type names "
            f"{unplaceable} -- symbols that module imports rather than declares, so "
            f"importing them from it would be a re-export",
            kind=Kind.VERDICT,
        )
    mod.imports |= {(source.module, symbol) for symbol in wanted}
    return held


def _symbols(decided: Type) -> set[str]:
    """Every symbol a decided type names in the module that decided it.

    Read off the :class:`compiler.Type` TREE rather than off its rendered text: a
    local arm is marked ``local`` where it is decided, so this enumerates the symbols
    instead of matching identifiers in an annotation and guessing which are types.
    """
    found = {decided.path} if decided.local and decided.path else set()
    for inner in (*decided.of, *([decided.key] if decided.key is not None else [])):
        found |= _symbols(inner)
    return found


def _constraining(node: dict) -> dict:
    """What a declaration says about the INSTANCE.

    ``default``, ``description`` and the rest of ``ANNOTATIONS`` annotate the node
    without constraining anything, so a declaration holding only those says
    nothing and cannot narrow.  That is precisely the shadow: the three
    ``responsive_creative.json`` restatements are a ``default`` plus a
    ``description`` and nothing else.
    """
    return {k: v for k, v in node.items() if k not in ANNOTATIONS and not k.startswith("x-")}


#: The annotations a FIELD renders, so the two a restatement can differ about in a way
#: the comparison sees.  ``compiler.fields`` reads exactly these off the declaration --
#: ``description`` into ``Field(description=...)`` and ``default`` into the field's
#: default -- and the rest of ``ANNOTATIONS`` (``title``, ``$comment``, ``$id``,
#: ``$schema``) reach nothing on a field, so a restatement differing only in one of
#: those renders the same field and states nothing to anyone.
RENDERED = ("default", "description")


def _annotates_differently(child: dict, base: dict) -> bool:
    """Would the two declarations render a different FIELD?

    Asked only of a restatement that says the same thing about the instance, where it
    is the whole of the difference.  An annotation the child does not state counts as
    a difference, because the child's silence is itself an answer: the field then
    carries whatever its own node resolves -- for a bare ``$ref``, the target's --
    and not the base's.
    """
    return any(child.get(k) != base.get(k) for k in RENDERED)


def _restatement(child: dict, base: dict) -> bool | None:
    """The merge rule as one decision about one restated property.

    ``True`` -- it NARROWS: it keeps every keyword ``base`` states, with the same
    value, and adds at least one more.  The subclass states it.

    ``False`` -- it says nothing, or says exactly the same thing.  The field is
    inherited and the subclass declares no field at all.

    ``None`` -- it is INCOMPATIBLE: it drops a keyword the base states, or gives
    one a different value.  Under ``allOf`` BOTH declarations apply, so the
    effective accepted set is their intersection and a Python annotation carrying
    only the restatement would be WIDER than the document.  The caller refuses.
    """
    c, b = _constraining(child), _constraining(base)
    if not c or c == b:
        return False
    if set(b) <= set(c) and all(b[k] == c[k] for k in b):
        return True
    return None


def _disagreeing(child: dict, base: dict) -> str:
    """The keyword a refusal is reported on: the first the two do not agree about."""
    c, b = _constraining(child), _constraining(base)
    return min({k for k in set(c) | set(b) if c.get(k) != b.get(k)} or {"allOf"})
