"""§2's intersection asked of ONE PROPERTY KEY: an own declaration against an inherited one.

This is the deepest clause of §5's ``allOf`` row and ``adcp-client-python-g4z`` is the row
that gave it a module.  §5's test of a boundary is "what a reader opens": a reader asking
*what happens to a property the composing node restates* has one file to open, and the four
answers that question has are the four arms of :func:`merge` below --

* the key is the composing node's ALONE, so its declaration is the field's;
* the restatement NARROWS (or makes the inherited field required, which is a narrowing
  too), so the subclass states the INTERSECTION;
* it says the same about the instance and something different to the READER, so the
  subclass states the field for its annotation and takes the intersection's content;
* it adds nothing, and the field is inherited with no line written.

**And the fifth answer is a REFUSAL**, which is the one §5(b) decides and this compiler
does not yet write: a restatement that neither matches nor narrows.  The sentence it
returns names the keyword the two declarations SHARE and disagree at, read through
``$ref``, which is the reading :func:`codegen.intersect._disagreeing` exists for.

**Why a module and not a region.**  §5: "a module states one subject; a function answers
one question about it."  The subject here is one property key under one composition, and
every line is about that key: the merge is total over the four shapes, the refusal is the
fifth, and :func:`_reused` -- the only other resident -- answers the one question the
second and third arms both ask, which is how a subclass states a field whose TYPE is the
base's.  Nothing else of the composing row reaches this file: it is handed the two views
and the base's decided fields and returns a value.

**It is GRADEABLE alone, which is the property that made the separation worth making**:
``tests/test_inherited_merge.py`` builds the two declarations by hand and asserts which
arm each pair takes, with no bundle, no module and no walk.
"""

from __future__ import annotations

from collections.abc import Mapping, Set as AbstractSet
from dataclasses import dataclass, field

from codegen import compiler, intersect, ir
from codegen.keywords import Position
from codegen.refusal import Kind, Refusal


@dataclass
class Merged:
    """What :func:`merge` decided for every key the composing node declares.

    Three maps and not a tuple, because each is read by a different part of the class the
    composing row then declares: ``own`` is what the field builder is handed, ``reuse`` is
    what :attr:`codegen.compiler.Shape.decided` carries, and ``distinct`` is a rule the
    class states rather than a field.  Mutable, because the composing row's requiredness
    overlay adds to ``own`` and ``reuse`` after this answer and before the class is
    declared -- one more arm of the same decision, over the keys NO view declares.
    """

    #: §2's intersection of the two declarations, per key -- and the composing node's
    #: own declaration where no base states the key.  This is what the field builder is
    #: handed.
    own: dict[str, dict] = field(default_factory=dict)
    #: The keys whose field is the inherited one wearing this document's annotations.
    reuse: dict[str, ir.Field] = field(default_factory=dict)
    #: The keys whose INTERSECTION took its ``uniqueItems`` from the base, so the rule
    #: families have already claimed the keyword on the class that decided the base's field and this
    #: subclass inherits that rule.  ``fields`` strips the keyword and renders the fact
    #: onto the field, exactly as it does for a REUSED key and for the reason its
    #: docstring gives there: the array row carries no ``uniqueItems`` and refuses one by
    #: name, which is what keeps an array NO class holds refused rather than widened.
    #:
    #: Measured on ``core/product-execution-requirement.json`` at
    #: ``/oneOf/2/properties/connection/allOf/1/properties/required_for``, whose
    #: restatement is a bare ``{"contains": {...}}``: the intersection merges the base's
    #: ``type``, ``items`` and ``uniqueItems`` back in, and the merged declaration was
    #: then decided FRESH -- so the keyword reached the array row and refused the
    #: document on a fact its base already states as a rule.
    distinct: set[str] = field(default_factory=set)


def merge(
    local: Mapping[str, dict],
    inherited: Mapping[str, dict],
    *,
    at: Mapping[str, str],
    pointer: str,
    required: AbstractSet[str],
    inherited_required: AbstractSet[str],
    inherited_fields: Mapping[str, ir.Field],
    inherited_from: Mapping[str, "compiler.Target"],
    mod: "compiler.Module",
) -> Merged | Refusal:
    """§2's intersection per key: what each of ``local``'s declarations makes of the field.

    ``local`` is every property declaration the composing node and its INLINE conjuncts
    state, keyed by property name and with ``at`` giving each one's pointer; ``inherited``
    is what the ``$ref`` conjuncts' targets state about the same keys.  Both are
    DECLARATIONS and not nodes, which is §6's reason for the whole rule: the merge hands
    its result back to ``parse``, so the result has to be one declaration and not two
    decided types.

    The arms are the four in this module's docstring, in the order the predicates settle
    them, and the first is the cheap one: a key no base declares has nothing to merge.
    """
    out = Merged()
    for key, stating in local.items():
        if key not in inherited:
            out.own[key] = stating
            continue
        verdict = intersect._restatement(stating, inherited[key], mod.resolve_node)
        if verdict is None:
            # **THE KIND IS THE CELL'S AND NOT THIS SITE'S** (architecture §3, "a
            # refusal's kind is derived from the cell and never chosen at a raise
            # site"), and the hand-written ``Kind.VERDICT`` that stood here was §9's
            # first mistake: ``docs/plan/rebuild-plan.md`` §5(b) DECIDES this row --
            # "an ``allOf`` restatement that neither matches nor narrows ... rung
            # KEYWORD: the field takes the base's declaration and the restatement's
            # extra facts are dropped" -- so what is missing is a written case and not
            # an obstruction belonging to the document.  A verdict minted for unwritten
            # code reports clearable work as finished, which is exactly what the pinned
            # verdict set recorded: eleven of the fourteen documents that JOINED it at
            # this row's third instalment resolve here.
            #
            # :func:`kind_for` answers DEFERRED for every keyword this arm reports on,
            # and it answers that off the cell: ``properties``, ``items``,
            # ``additionalProperties`` and ``$ref`` all compile to a TYPE at PROP, and a
            # lowering effect whose handler claims nothing is a deferral.  An UNROWED
            # key still answers VERDICT through the same lookup, so the one arm that
            # really is the document's keeps its kind without a second reading.
            #
            # PROP and not ``position``: a restatement is a PROPERTY's declaration
            # against the base's, which is the same reason :func:`_constraining` reads
            # every declaration this arm compares at PROP.  The position is the restated
            # node's own and is taken from the structure, not recovered from the pointer.
            #
            # **WHY §5(b)'S RUNG IS NOT YET WRITTEN, measured rather than asserted**
            # (``adcp-client-python-10l.21``, fourth instalment).  The widening itself
            # is sound and lands: implemented over the 1,054 portable documents it takes
            # emitted 885 -> 910 and refused 169 -> 144.  What it cannot do is be
            # DECLARED.  §2 defines the one declarable kind as "WIDENED -- ... the
            # document states a fact the model does not", and §8's *approximated*
            # outcome is the same direction: "the document states the fact, the model
            # does not".  The facts this row drops are NESTED facts the base's own
            # declaration states a WIDER value for, so 21 of the 25 freed documents
            # carry a fact no declaration can absorb, and the three that carry NONE are
            # wider than their documents invisibly.  A rung is written when a
            # declaration has a form for the direction it drops in.
            disagreeing = intersect._disagreeing(stating, inherited[key], mod.resolve_node)
            # **The sentence states its own obstruction, which means the DEREFERENCED
            # reading and the two values at the keyword that failed** (``10l.92``).  It
            # printed ``sorted(_constraining(...))`` of the RAW declarations, so a base
            # whose whole content is a bare reference read as "inherited states
            # ['$ref']" -- true of the text and not of what was compared, since
            # :func:`_restatement` resolves such a base before it compares anything.
            # Three refusals here said that, and the keyword they named was the
            # reference they had already resolved past.
            inherited_read = intersect._constraining(intersect._dereferenced(inherited[key], mod.resolve_node))
            stating_read = intersect._constraining(intersect._dereferenced(stating, mod.resolve_node))
            return Refusal(
                disagreeing,
                at[key],
                f"the restatement of {key!r} neither matches nor narrows the "
                f"inherited declaration at {disagreeing!r}: inherited says "
                f"{inherited_read.get(disagreeing)!r}, this says "
                f"{stating_read.get(disagreeing)!r}.  inherited states "
                f"{sorted(inherited_read)}, this states {sorted(stating_read)}, and the "
                "keyword above is the first the two SHARE that this one does not say at "
                "least as much at -- a keyword only the inherited declaration states is "
                "never the obstruction, because under allOf the base's statement applies "
                "wherever the restatement is quiet.  "
                "docs/plan/rebuild-plan.md section 5(b) decides this row at rung "
                "KEYWORD -- the field takes the base's declaration and the "
                "restatement's extra facts are dropped -- and the facts it drops are "
                "nested ones the base states a WIDER value for, which section 8's "
                "approximated outcome has no direction for: it reads 'the document "
                "states the fact, the model does not'",
                kind=compiler.kind_for(disagreeing, Position.PROP),
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
            # on ``core/protocol-envelope.json`` and required at their own root.
            #
            # The INTERSECTION, in BOTH halves (``adcp-client-python-10l.103``).
            #
            # **This read the node ITSELF where only the requiredness moved, on the
            # ground that "the content is the base's already, so there is nothing of the
            # base's to merge back in" -- and that is true of an EQUAL restatement and
            # false of one stating LESS.**  Once silence stopped being a loosening
            # (:func:`_restatement`), a restatement that does not narrow can state
            # strictly less than the base, and lowering THAT node alone drops every fact
            # the base states.  The arm below already carries the sentence, for the same
            # shape reached without a requiredness move: "a restatement can reach this
            # arm stating LESS than the base ... and lowering THAT node alone drops the
            # base's bound, which is the shadow this whole rule exists to make
            # unspellable."
            #
            # Measured on ``adagents.json``, where its four union branches state
            # ``{"properties": {"formats": {"minItems": 1}}, "required": ["formats"]}``
            # over a base declaring ``formats`` as an array of
            # ``ProductFormatDeclaration`` with ``minItems: 1`` already: the restatement
            # matches, so ``verdict`` is false, the requiredness moved, and the field was
            # redeclared from ``{"minItems": 1}`` alone -- emitting ``formats: Any`` over
            # the base's ``list[FormatsItem]``.  Three defects in one line: a
            # TYPE-changing redeclaration of an inherited field, which this module's own
            # rule calls a build failure; the base's ``type`` and ``items`` dropped with
            # no declaration at all; and the ``minItems`` that WAS declared declared at
            # rung KEYWORD -- "drop the one keyword, keep the type" -- while the output
            # took ``Any``.  The asymmetry is the proof: the two sibling branches that
            # state no ``required`` reached the arm below and kept the base's type and
            # bound.
            out.own[key] = intersect._intersection(stating, inherited[key], mod.resolve_node)
            if not intersect._constraining(stating) or intersect._constraining(out.own[key]) == intersect._constraining(
                intersect._dereferenced(inherited[key], mod.resolve_node)
            ):
                # **The restatement says nothing about the instance the base does not,
                # so this is section 2's REQUIREDNESS OVERLAY and takes its answer**:
                # "Where composition makes an inherited field required, the subclass
                # redeclares it with the base's type and no default."  The overlay loop
                # below implements exactly that and reaches only a key NO view declares;
                # a key that is both restated and newly required falls between the two,
                # and this is the half that was missing.
                #
                # Reusing the base's DECIDED field rather than re-deciding the
                # intersection is what keeps the KNOWN CEILING below unreached: the
                # intersection takes the base's ``items`` with it, and re-deciding
                # declares that nested class again at a pointer this document does not
                # have, which is what ``schema_at`` raises on when the pair is graded.
                held = _reused(
                    key, inherited_fields, inherited_from, f"{pointer}/properties/{key}", mod
                )
                if isinstance(held, Refusal):
                    return held
                out.reuse[key] = held
                out.own[key] = dict(inherited[key])
            if intersect._constraining(out.own[key]).get("uniqueItems") is True and not intersect._constraining(
                stating
            ).get("uniqueItems"):
                out.distinct.add(key)
        elif intersect._annotates_differently(stating, inherited[key]):
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
            #   :func:`lower_node` reading the node decides the base's own type and there
            #   is no shadow to be had.  15 pairs and 15 documents, every one a response
            #   root composing ``core/protocol-envelope.json`` and declaring ``context``
            #   itself as a bare ``$ref`` to ``core/context.json``: the envelope states
            #   the long "Relationship to per-task body-level ``context`` declarations"
            #   text as a SIBLING of its own ``$ref``, and the 15 documents state the
            #   target's own short text at that pointer.
            # * **EMPTY** -- the node says nothing about the instance, so it is the
            #   inherited FIELD that stands and only the annotations are this
            #   document's.  A previous reading left this shape inherited entirely, on
            #   the ground that lowering the restatement ALONE types it ``Any`` and
            #   drops every fact the base states.  That is true of the restatement
            #   alone, and the answer is to not lower it alone: the base's decided
            #   field is re-used (:attr:`Shape.decided`, and ``fields``' ``reuse``
            #   says why the node cannot simply be merged and re-decided).  Measured as
            #   the whole of ``salesagent-j3k2l.22``'s residue: 28 annotations over 7
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
            # restatement's silence as an answer dropped the base's description, which
            # the composed document states at that pointer.
            # **The INTERSECTION here too, and the arm below is no longer "the node
            # states nothing" but "the intersection is the base's".**  Once silence
            # stopped being a loosening (:func:`_restatement`), a restatement can reach
            # this arm stating LESS than the base -- ``{"type": "integer"}`` over
            # ``{"type": "integer", "minimum": 3}`` says the same thing about every
            # instance and differs only in its annotations -- and lowering THAT node
            # alone drops the base's bound, which is the shadow this whole rule exists
            # to make unspellable.  The intersection is the base's content wearing this
            # document's annotations, and it is the same expression the EMPTY case used,
            # so there is one answer for both.
            out.own[key] = intersect._intersection(stating, inherited[key], mod.resolve_node)
            if not intersect._constraining(stating):
                # The node has no type of ITS OWN, so the field is the base's DECIDED
                # field: re-deciding declares the nested classes again, in this module,
                # at a pointer this document does not have (:attr:`Shape.decided`).
                #
                # The condition is "the NODE constrains nothing" and deliberately not
                # "the INTERSECTION is the base's", which is the same thing for this
                # shape and NOT the same thing for an EQUAL restatement: an equal one
                # intersects to the base's content too, and §6's clause 2 says its own
                # node is what the field is decided from -- all 15 of them are a bare
                # ``$ref`` whose resolved target carries its own annotations, and
                # reusing there put the base's annotation back at a pointer the document
                # declares itself.  Measured: 17 documents stopped emitting.
                #
                # KNOWN CEILING for the PARTIAL shape between the two -- a restatement
                # stating less than the base and the same -- whose intersection is
                # lowered as a node: a subschema-valued keyword it takes from the base
                # (an ``items``, a nested ``properties``) is declared at a pointer this
                # document does not have, and ``schema_at`` raises when the pair is
                # graded.  0 such sites in the emitted population, and the failure is
                # loud rather than silent, which is why this is named rather than coded.
                held = _reused(key, inherited_fields, inherited_from, at[key], mod)
                if isinstance(held, Refusal):
                    return held
                out.reuse[key] = held
        # Otherwise it adds nothing and the field is INHERITED: no line, no shadow.


    # **SECTION 2's REQUIREDNESS OVERLAY: the composition makes an inherited field
    # required and nothing else, so the subclass redeclares that field with the base's
    # type and no default.**  Section 2 calls this the only permitted redeclaration and
    # the sentence is verbatim; the loop above reaches only a key some view DECLARES,
    # and an overlay declares none -- ``core/collection-selection.json`` at
    # ``/oneOf/0/properties/collections/items/allOf/1`` is ``{"required":
    # ["collection_ids"]}`` and nothing more.
    #
    # Left out, the requiredness went into ``required`` where the inherited field
    # SATISFIED it (``fields``' ``inherited`` argument) and no line was written, so the
    # class kept the base's OPTIONAL field and rendered ``= None`` -- a default the
    # document does not state at
    # ``/properties/collection_ids/default``, and a class that ACCEPTS A PAYLOAD THE
    # DOCUMENT REFUSES.  That is the same defect the ``key in required and key not in
    # inherited_required`` branch above fixes for a key that IS declared locally; this
    # is its other half.
    #
    # The TYPE is the base's decided field (``reuse``) rather than a second decision of
    # the base's node: re-deciding declares the nested classes again, in this module, at
    # a pointer this document does not have (:func:`fields`' ``reuse`` says why).
    #
    # **Section 2 also says "and no default", and that half is NOT written here**, because it
    # has no population: measured over every node of every one of the 1,054 portable
    # documents, 25 nodes carry a ``required``-only conjunct and **0 of them compose a
    # base that declares a ``default`` for a name the conjunct requires**.  An arm for it
    # would be a derivation matching nothing, which is green for free (the same ground
    # this row's own docstring refuses a ``required``-only conjunct arm AT A ROOT on, and
    # a stripped ``default`` was measured as unobservable: the perturbation that kept it
    # left the suite green).  If such a base ever appears, ``fields`` refuses the
    # document BY NAME -- "a default on a REQUIRED property has no rendering that does
    # not also make the property optional" -- which is the accurate answer and already
    # written.
    for key in sorted(required - inherited_required - set(out.own)):
        if key not in inherited:
            continue  # ``fields`` refuses a required name no view declares, by name
        # **The pointer names the PROPERTY and not the composing node.**  An overlay's
        # key is not in ``at`` -- no view of this document declares it, which is what
        # makes it an overlay -- so the pointer has to be built, and this passed
        # ``pointer`` itself.  At a ROOT that is ``""``, which ``Refusal`` renders
        # ``/``, so a refusal :func:`_reused` raises for one property was reported
        # against the whole document: measured on
        # ``core/product-signal-targeting-option.json``, whose ``signal_ref`` re-uses a
        # field whose type the base module imports rather than declares, and which
        # ``tests/test_emit_product.py`` caught as the one refusal left at ``/`` after
        # every other one had moved inside its document.
        overlaid = _reused(
            key, inherited_fields, inherited_from, f"{pointer}/properties/{key}", mod
        )
        if isinstance(overlaid, Refusal):
            return overlaid
        out.reuse[key] = overlaid
        out.own[key] = dict(inherited[key])
    return out


def _reused(
    key: str,
    inherited_fields: Mapping[str, ir.Field],
    inherited_from: Mapping[str, compiler.Target],
    pointer: str,
    mod: compiler.Module,
) -> ir.Field | Refusal:
    """The inherited field an annotation-only restatement re-states, importable here.

    A re-used type names symbols, and each one has to be IMPORTABLE from this module or
    the class is an undefined name at import.  **Each is taken from the module that
    DECLARES it** -- :attr:`Target.imports` is the base's whole offer, its own
    declarations beside the declarers of everything it imported -- which is §1's "one
    import path per class, and never a second way to reach the same class": the base's
    import of a symbol and this module's import of the same symbol name one module, so
    there is one path to the class and no re-export anywhere.

    **It read ``Shape.declares`` and refused the rest as a re-export, and that refusal
    is what ``adcp-client-python-81c`` answers.**  The sentence was right about what it
    refused -- importing a symbol FROM the base, which the base only imported, is the
    second path §1 forbids -- and wrong that there was nothing else to do.  The base's
    own import names the declaring module, the run holds it
    (:attr:`Module.imported`), and taking the symbol from there is one import path and
    not a relaxation of anything.

    **Its population was NOT 0, which is this row's own finding.**  The sentence it
    replaced read "0 re-use a type naming a re-exported symbol, so the refusal below
    fires on nothing today", and that figure is stale at ``18474e55``: the PUBLISHED
    bundle reaches it in two documents -- ``core/media-buy-frequency-cap-capability.json``
    at ``/properties/max_impressions_constraints``
    (``FrequencyCapImpressionConstraints``) and ``core/product-signal-targeting-option``
    ``.json`` at ``/properties/signal_ref`` (``SignalRef``).  The patch set for upstream
    #8525 adds the third: ``core/domain-name.json`` is extracted,
    ``core/placement-ref.json``'s ``publisher_domain`` becomes a ``$ref`` to it,
    ``core/placement-selection.json`` composes that base under ``{required:
    [publisher_domain]}``, and the subclass restates the key with the base's type.

    **Measured at this row, both bundles, over the portable set.**  70 keys reach this
    function.  9 take the arm below (the base is this module's own).  61 cross a module
    boundary, and of those 17 re-use a type naming a symbol -- 18 over the patched
    bundle.  The symbols resolve to 5 declaring documents: 13 to
    ``formats/canonical/_base.json``, which is the base itself, and 4 to a document the
    base IMPORTED -- ``core/frequency-cap-impression-constraints.json``,
    ``core/frequency-cap-interval-constraints.json``, ``enums/reach-unit.json`` and
    ``core/signal-ref.json`` -- with ``core/domain-name.json`` the fifth over the patched
    bundle.  0 refuse, over either.

    What is left to refuse is a symbol the base's module neither declares nor imported
    from a document of this bundle -- nothing of the run can name it, so there is no
    module to import it from and no judgement to make about which one.  Population 0
    over both bundles.
    """
    held, source = inherited_fields.get(key), inherited_from.get(key)
    if held is None:
        return Refusal(
            "properties",
            pointer,
            f"{key!r} restates an inherited declaration with nothing but annotations, "
            f"and the base declaring it recorded no decided field for it, so there is "
            f"no type to re-use and lowering the restatement alone would type it Any",
            kind=Kind.VERDICT,
        )
    if source is None or not source.crosses_a_module:
        # **The base is declared in THIS module**, which is §4's union base: a branch
        # composes with it and the base is not a ``$ref`` conjunct, so there is no
        # :class:`Target` for it and nothing to import -- the field's type names this
        # module's own declarations by pointer and ``lower/names.py`` binds them.  The
        # import screen below is about crossing a module boundary, and this does not
        # cross one.
        #
        # **TWO carriers, ONE question** (``adcp-client-python-10l.43``).  A base reached
        # through a LOCAL ``$ref`` conjunct is in this module too, and it arrives with a
        # :class:`Target` -- ``compiler.local_target``'s, wrapping the two records
        # ``declare_object`` wrote for a node of THIS document -- so ``source is None``
        # stopped being the whole of "the base is here".  The question is
        # :attr:`Target.crosses_a_module` and it is stated on the carrier, once.
        # Measured: ``core/registry-event.json`` composes ``#/$defs/propertyPayload`` at
        # ``/oneOf/0/properties/payload/allOf/0`` and re-uses its ``classification``,
        # whose type names ``/$defs/classification`` -- a POINTER this module declares and
        # ``lower/names.py`` binds, which the screen below reported as "symbols no
        # document this run lowered declares".
        #
        # **Re-measured at ``adcp-client-python-81c``: 9 branches reach here**, over both
        # bundles -- 6 on ``account/list-account-changes-response.json`` and 3 on
        # ``core/brand-response-authorization-result.json``.  This read "0 branches reach
        # here, so this arm is written for the first document that does rather than
        # discovered by it", which was true when it was written and is not now; the arm
        # is exercised and ``/properties/reason``'s re-used type reaches it still
        # carrying a POINTER, which is exactly the case it declines to screen.
        return held
    wanted = ir.symbols(held.type)
    unplaceable = sorted(wanted - set(source.imports))
    if unplaceable:
        return Refusal(
            "properties",
            pointer,
            f"{key!r} re-uses the field of {source.symbol}, whose type names "
            f"{unplaceable} -- symbols no document this run lowered declares, so there "
            f"is no module to import them from",
            kind=Kind.VERDICT,
        )
    for symbol in sorted(wanted):
        mod.importing(symbol, source.imports[symbol])
    return held
