"""§5's object row: ``type: object`` (stated or applied) with ``properties`` -> a class.

**The field builder and the class declarer are HERE**, with the row whose primary subject
they are: ``docs/plan/architecture.md`` §5, "a collaborator several rows share lives with
its PRIMARY subject and is imported by the others.  The field builder and the class
declarer are the object row's -- every class with fields passes through them, and the
composing row and a union branch are callers."  §14 step 5 named the move and
``adcp-client-python-g4z`` is the row that made it; the three callers outside this module
are ``lower/composition.py``, ``lower/union.py`` and ``lower/references.py``.

**WHAT THE FUNNEL IS A FUNNEL OF, measured rather than asserted** (``adcp-client-python-fhi``).
This docstring used to call :func:`declare_object` "the one funnel every class with fields
passes through", and that sentence is imprecise in a way a reader can act on wrongly.
:class:`codegen.ir.ClassDecl` is constructed in exactly **two** places tree-wide --
:func:`declare_object` below, with ``ref=schema_ref(...)``, and
``codegen.lower.envelope.base``, with ``ref=None``.  The third apparent site,
``codegen.lower.names``' rebinding of symbol slots, is a ``dataclasses.replace`` on a
declaration that already came through here and not a construction.  So the funnel IS a
funnel, and its subject is **a class the walk declares for a DOCUMENT NODE** (``ref is not
None``) rather than "a class with fields": the two differ by exactly the envelope base,
which has no document node to pass through.  The count of callers passing ``fields=`` is a
true count of CALLERS and says nothing about how many places build a declaration.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import replace
from typing import Any

from codegen import compiler, ir
from codegen.ir import MISSING
from codegen.keywords import Position
from codegen.lower import names
from codegen.refusal import Kind, Refusal
from codegen.schema import nodes


def lower(node: nodes.Object, mod: compiler.Module) -> ir.Decided | Refusal:
    """The class, declared at this node's POINTER, as a local type.

    The refusal the class declarer returns comes back out UNCHANGED (§6: "a handler that
    receives a ``Refusal`` from a child returns it, unchanged, immediately"), so the
    document is refused at the innermost node that carried the keyword and this row adds
    no sentence of its own to it.
    """
    # **§3a's CATALOGUE, layer L2, is asked in ``compiler.lower_node`` and NOT here**
    # (reading 4, 2026-11-04).  It was asked here, at this row's own entry, and measured
    # over this bundle 7 of the object layer's 167 restating positions never reach this
    # row at all -- a node holding a combinator beside its ``properties`` goes to the
    # composing row, a conjunct's property is declared by the node holding the ``allOf``,
    # and §4's dedup runs before the dispatch.  Each of those emitted a second definition
    # of a structure the catalogue had collected, so the question belongs to the walk's
    # per-node entry, where it is asked of every arm alike; that function's docstring
    # carries the measurement and the ordering argument.
    #
    # The positions the table never holds are ``catalogue.ShapeEntry.restating``'s and
    # each is a standing rule rather than a precaution: a document ROOT declares because
    # §1 says every portable document contributes a symbol; a position in the home's own
    # document is §4's content dedup's and not this layer's; the home declares; and a
    # position that declares no class has nothing to stop minting.  A home whose document
    # REFUSED is absent for the reason ``emit.objects`` gives -- there is no symbol to
    # import, and refusing this document would charge it for a defect in another.
    declared = lower_object(node, mod)
    if isinstance(declared, Refusal):
        return declared
    return ir.Decided(ir.TypeRef(declared, local=True))


# --------------------------------------------------------------------------- #
# the field builder and the class declarer
# --------------------------------------------------------------------------- #
def fields(
    props: Mapping[str, nodes.Node],
    required: Collection[str],
    pointer: str,
    mod: compiler.Module,
    *,
    inherited: Collection[str] = (),
    declared_at: Mapping[str, str] | None = None,
    distinct: Collection[str] = (),
    reuse: Mapping[str, ir.Field] | None = None,
    pinned: Mapping[str, ir.TypeRef] | None = None,
    carried: Collection[str] = (),
) -> list[ir.Field] | Refusal:
    """The decided properties for one property map, children declared first.

    Shared with a composing row, which builds ONE property map out of a root's
    own ``properties`` and an inline ``allOf`` conjunct's.  How a property is
    decided is the same question wherever it was declared, and a second copy of
    this loop is how two declarations of one field come to disagree about the
    answer.

    **``required`` is read IN ORDER, so the caller owns that order** (P7): the names no
    declaration declares come out of a comprehension over it, and each one becomes a
    FIELD below, so the argument's order is the emitted class's field order and
    therefore part of the artifact.  A caller passing the document's own ``required``
    tuple passes document order; a caller holding a ``set`` -- the composing row, which
    unions the node's own names with a base's ``frozenset`` -- sorts before it passes,
    because a set of strings iterates in hash order and the emitted tree must be a
    function of the bundle.  It was the REFUSAL SENTENCE's order before those names
    became fields; the same argument now decides a line of rendered Python, which is a
    stronger reason for the same rule.

    ``inherited`` names the keys a BASE CLASS already declares.  They are not
    decided here -- the field is inherited, and a subclass that restated it would
    shadow the base's type with whatever its own restatement happens to say --
    but they do satisfy ``required``, because an inherited field is present on
    the class.  The row decides what goes in it (the narrowing rule); this
    function only honours it.  ``declared_at`` gives the pointer a key was
    declared at where that is not ``<pointer>/properties/<key>``, which it is not
    for a key that came from a conjunct.

    ``reuse`` names the keys whose FIELD is one an enclosing class already decided,
    and hands it over: its type, its constraints, its format and its ``uniqueItems``.
    Everything else about the field is still read off ``props`` here -- the default,
    the description, the requiredness, the attribute spelling -- so a reused key is a
    field of this class stating the DOCUMENT's own annotations over an inherited type.

    **This is not the ``decided`` argument that was removed, and the reason it was
    removed does not reach it.**  That one carried a per-property type the caller had
    already decided so the union row could turn a branch's ``const`` into a
    ``Literal``; it went because :func:`lower_node` reaches ``codegen.lower.const`` for
    every node, so the type WAS derivable here and two lowerings had to agree about
    one keyword.  A reused type is the other case: it is not derivable here, because
    deciding it declares the nested classes AGAIN and in this module, at a pointer
    **this document does not have** -- measured on
    ``formats/canonical/image_carousel.json``, whose merged ``slots`` emits a second
    ``...SlotsItem`` stamped ``#/properties/slots/items`` where that document's own
    ``properties/slots`` carries a ``default`` and a ``description`` and nothing else,
    and ``schema_at`` raises ``KeyError: 'items'``.  There is still exactly one
    lowering of the node: the base's.

    ``pinned`` is §3a's PASS B, and it is the SAME "one position, not everywhere" shape
    ``distinct`` has rather than a second ``decided``: it names the keys whose pin
    ``codegen.lower.normalise.pins_a_member`` decided names a MEMBER of the enumeration an
    enclosing class already declared for the property, and carries the narrowed type.  The
    node is still lowered here -- ``codegen.lower.const`` runs, and every refusal it owes
    the pin is still reported, which is what keeps ONE lowering of the node -- and the
    decided type is replaced afterwards.  Replacing it instead of skipping the lowering is
    the whole difference between this and the ``decided`` argument that was removed: that
    one carried a type the caller decided *instead* of this loop deciding it, and the
    keyword then had two lowerings to agree about.

    ``distinct`` is the same "one position, not everywhere" shape that ``decided``
    had, and it survives because its keyword has no such row: it names the keys whose
    array D6's rule lowering has CLAIMED the ``uniqueItems`` of
    (``lower.rules._distinct``).  The keyword is stripped off the declaration here so
    the array row never sees it -- which is what leaves that row's screen refusing an
    array no class holds rather than widening it -- and :attr:`codegen.ir.Field.distinct`
    carries the fact onto the field, where ``_field`` renders it.  A key named here
    whose declaration is not an array with ``uniqueItems: true`` is a caller defect,
    so nothing is silently stripped: the strip is read off the declaration and the
    flag off this set, and the two agreeing is asserted by the rules lowering's own
    gate.  A REUSED key takes the flag off the field it reuses instead: the
    ``uniqueItems`` was claimed by the rule on the class that decided it, which a
    subclass inherits, so the subclass's own rules do not name the key.

    ``carried`` names the required keys whose presence the CLASS enforces by something
    that is NOT a field of its own, so they are not undeclared and get no field here --
    which is the one thing that keeps the ``Any``-field answer below off a union base.
    **One caller passes a non-empty one and §5's ``required`` row is the whole of why**:
    at a ROOT beside a union the row reads "required on the base's fields, and the names
    recorded in ``_ROOT_REQUIRED``, so a refusal can separate a field the root requires
    from one that SELECTS A BRANCH" -- which presupposes that a name selecting a branch
    is not a field of the base.  ``core/product-format-declaration.json`` is that
    sentence's own shape: its root requires ``format_kind`` (the discriminator §4
    derives) and ``params``, its 15 root properties declare neither, and each of its 16
    branches declares AND requires both -- so the branch classes are what hold the
    fields, the branches' own requiredness is what enforces the presence, and
    :attr:`adcp.types._base.BranchDispatchMixin._ROOT_REQUIRED` is what names the two in
    the DOCUMENT's vocabulary when no branch admits a payload
    (``_base.BranchDispatchMixin._no_branch``, which reads the raw mapping and not the
    model).  Measured over every node of the 1,054 portable documents: **2 union nodes
    state a ``required`` naming a key their own ``properties`` do not declare** --
    ``core/product-format-declaration.json`` at ``/`` and
    ``creative/validate-input-request.json`` at ``/properties/targets/items`` -- and in
    BOTH every branch declares and requires every such name.

    **``position`` is GONE with the refusal it was here for.**  It existed so the
    undeclared-``required`` refusal could read its kind off the ``required`` cell at the
    node's own position (:func:`kind_for`) rather than name one; that refusal is now a
    field, and nothing else in this function asked the question.  Every position a class
    can sit at reads the same ``TYPE`` cell, so the answer never moved anyway, which is
    why removing it changes no caller's meaning.
    """
    held = (*inherited, *carried)
    undeclared = [r for r in required if r not in props and r not in held]

    built: list[ir.Field] = []
    spelled: dict[str, str] = {}
    where = declared_at or {}
    reuse = reuse or {}
    # **The loop returns on the FIRST refusal, in the property map's own order**, which
    # is the document's own key order because the parser built the map by walking it
    # (``schema.parse``).  That is :func:`codegen.refusal.first_refusal` fused with the
    # map that would have produced the sequence, and §6's "earliest refusal in document
    # order" is what the fusion preserves: the loop cannot reach a later property's
    # refusal before an earlier property's.  Fused rather than separate because the body
    # is SEQUENCED -- a dropped default is recorded on the module as the field is built --
    # so a batch of results would record drops for properties after the refusing one.
    for key, child in props.items():
        at = where.get(key, f"{pointer}/properties/{key}")
        fname = names.field_name(key, mod.reserved)
        if fname in spelled:
            return Refusal(
                "properties", at, f"{key!r} and {spelled[fname]!r} both spell the field {fname!r}"
            , kind=Kind.VERDICT)
        spelled[fname] = key
        is_distinct = key in distinct
        if key in reuse:
            # Bound under its own name and not onto ``held``: ``held`` above is the NAMES
            # nothing declares (``undeclared``'s reading) and this is a decided
            # :class:`codegen.ir.Field`.  One name for two types made the checker read
            # ``.type`` off a ``tuple[str, ...]`` -- three of §14 step 6's six errors --
            # and the comment at ``undeclared``'s own site still means the outer one.
            reused = reuse[key]
            # The REUSED field's type ALREADY states its bound and its format (§2, and
            # :attr:`codegen.ir.TypeRef.facts`), so it is taken whole: splitting the
            # three back out and recombining them is what two carriers of one fact
            # invites, and the base decided this type at its own pointer.
            field_type = reused.type
            is_distinct = reused.distinct
        else:
            # **§4's nested name rule as a HOP and not as a name** (§7): what this
            # records is the structural fact -- this child hangs off the class at
            # ``pointer`` through the property ``key`` -- and ``lower/names.py`` is what
            # turns it into ``<Parent><Property>``.  The child's own pointer is the key,
            # which for a key that came from an ``allOf`` conjunct is the conjunct's
            # (``declared_at``) and never this node's.
            mod.hops[child.pointer] = names.Property(pointer, key)
            decided_type = compiler.lower_node(child, mod)
            if isinstance(decided_type, Refusal):
                return decided_type
            # §2: **constraints bind to the TYPE, not the field.**  A :class:`codegen.ir.Decided`
            # carries the three apart because a format is either IN the type or beside
            # it and never in both; the field carries one type that states all of them,
            # so the same bound reached through a list, a mapping value or a union
            # branch is the same value.
            field_type = replace(
                decided_type.type,
                facts=decided_type.constraints,
                format=decided_type.format,
            )
            # **§3a's PASS B, applied to the DECIDED type and not instead of deciding
            # it.**  The pin was lowered by ``codegen.lower.const`` on the line above, so
            # every refusal that row owes it has already been reported; what this replaces
            # is the RENDERING of a value set the base already named -- ``Literal[v]``
            # becomes ``Literal[Enum.MEMBER]`` over the enumeration the base declared, so
            # the branch's narrowing is one a type checker reads as a narrowing and not as
            # an incompatible override.  The decision is ``lower.normalise``'s and was
            # made where the DECLARATIONS were in hand; this site applies it.
            #
            # Guarded on the lowered type still BEING the pin, which is the one thing this
            # site can check that the decider could not: a pin whose row answered with
            # anything else is not a pin this narrowing is about.
            narrowed = (pinned or {}).get(key)
            if narrowed is not None and len(field_type.literals) == 1:
                field_type = narrowed
        is_required = key in required
        default = MISSING
        # **Through a LOCAL ``$ref`` the target's ``default`` is this field's**, which is
        # draft-07 replacing the node with its target read by §5's ``default`` row:
        # :attr:`Module.referred` is where :func:`local_reference` put it, and the node's
        # OWN sibling wins where it states one -- the same precedence §5's ``$ref`` row
        # gives a ``description`` sibling.
        stated = child.annotations.get("default", mod.referred.get(child.pointer, MISSING))
        # **And through a CHAINED remote ``$ref`` the hop's ``description`` is this
        # field's** (:attr:`Module.described`), by the same precedence and for the same
        # reason: §5's ``$ref`` row makes a sibling's ``description`` authoritative, and
        # ``bundle.record`` inlines the hop's text at this very pointer -- so the node's
        # OWN sibling wins and the chain's stands where the node is silent.
        described = (
            child.description
            if child.description is not None
            else mod.described.get(child.pointer)
        )
        if stated is not MISSING:
            if is_required:
                # Section 5's ``default`` row: **on a REQUIRED property, dropped and
                # reported, because no rendering makes a field both required and
                # defaulted.**  A pydantic field with a default is not required, so
                # transcribing one here would widen the model's accepted set to admit
                # an instance omitting a key the document demands -- and the schema
                # half of ``strict_validate`` would hide that in both acceptance
                # directions.
                #
                # Dropping it changes NO accepted set, which is why the row drops it
                # rather than refusing the document: the key is present in every
                # instance the document admits, so the default can never be applied
                # and a model that omits it accepts and rejects exactly what the
                # document does.
                #
                # REPORTED, and that half is not optional: a fact the document states
                # and the emitter silently discards is the one failure this pipeline
                # has no other guard against.  :attr:`Module.drops` carries it out to
                # ``emit.emit``, which prints it and hands it to the suite.  5 of the
                # bundle's 339 property defaults sit on a required property.
                mod.drops[at] = stated
            else:
                default = stated
        built.append(
            ir.Field(
                name=fname,
                wire=key,
                type=field_type,
                required=is_required,
                default=default,
                description=described,
                distinct=is_distinct,
            )
        )
    # **A required name NO declaration declares is a required field of type ``Any``**,
    # which §5's ``required`` row decides and which is EXACT rather than wide:
    # ``required: ["x"]`` with no entry for ``x`` admits an object carrying ``x`` with
    # any value, and ``Any`` is what §5's ``type`` row already gives an absent type
    # word.  Nothing is widened, nothing is dropped and no declaration is owed, so this
    # appends a field and declares no approximation.
    #
    # **It was a refusal, and the refusal was a conflict between two of this compiler's
    # own decisions rather than anything a document got wrong.**  §5's ``required`` row
    # called such a name "a presence rule with no field": a rule enforces the key's
    # presence on the constructor and declares nothing to hold its value, so the class
    # had no place for a key every instance the document admits carries.  The field half
    # has one, demands exactly what ``required`` demands, and dumps the key back where
    # the document states it -- which is the faithful half.  27 of the 95 refusals, 5 of
    # them primary.
    #
    # ``held`` is why this fires only where NOTHING holds the name: a key an INHERITED
    # field declares is the base's, and a CARRIED one is the union row's -- at a ROOT
    # beside a union the branches declare and require the name and
    # ``_ROOT_REQUIRED`` enforces it, which
    # ``test_a_root_required_the_branches_declare_is_root_required_and_not_a_field``
    # asserts a field would get wrong.
    #
    # In ``required``'s own order, which is the CALLER's (see the note above on P7):
    # these keys have no ``properties`` entry, so the document states no key order for
    # them and ``required`` is the only order it states.  That order is now the emitted
    # class's FIELD order and not just a sentence's, which is why the composing caller
    # sorts before it passes.
    for key in undeclared:
        fname = names.field_name(key, mod.reserved)
        if fname in spelled:
            return Refusal(
                "required",
                pointer,
                f"{key!r} is required with no declaration and {spelled[fname]!r} is "
                f"declared, and both spell the field {fname!r}",
                kind=Kind.VERDICT,
            )
        spelled[fname] = key
        built.append(ir.Field(name=fname, wire=key, type=ir.TypeRef("typing.Any"), required=True))
    return built


def _a_property_count_rides(
    node: nodes.Base, rule_nodes: Sequence[Mapping[str, Any]]
) -> bool:
    """Does ``min``/``maxProperties`` ride on this class, from the node or a rule source?

    The keyword set is ``lower.containers.KEY_BOUNDS`` -- the one declaration of which
    keywords count an object's keys, read rather than restated, so a third family of them
    cannot come to disagree with the mapping arm that renders the same two as
    ``min_length``/``max_length``.

    Imported on use because ``codegen.lower.containers`` imports THIS module, which is the
    direction the lazy import at the ``dropped`` funnel below already resolves.
    """
    from codegen.lower.containers import KEY_BOUNDS  # see above

    return any(
        key in node.rules or any(key in one for one in rule_nodes) for key in KEY_BOUNDS
    )


#: The scalar words whose pydantic type ADMITS A VALUE OF ANOTHER JSON TYPE, so that a
#: class carrying the word is still wider than the document that states it.  Each is
#: measured rather than read off a doc page, and each measurement is in the pair below:
#:
#: * ``boolean`` -> ``bool`` admits ``1`` and ``"true"``, which ``{"type": "boolean"}``
#:   refuses.  3 extras stores of this bundle state it.
#: * ``integer`` -> ``int`` admits ``True``, which ``{"type": "integer"}`` refuses.
#: * ``number`` -> ``float`` admits ``True`` and ``"1.5"``, which ``{"type": "number"}``
#:   refuses.
#:
#: ``string`` is NOT here, and that is the measurement that makes this a derivation rather
#: than a list: pydantic's lax ``str`` refuses every non-string, so ``dict[str, str]`` is
#: EXACT and the bundle's 8 such stores declare nothing.  ``object`` and ``array`` are not
#: here either -- the store's value is then a class or a list and the type carries itself.
#:
#: **AND WHY THIS IS A DECLARATION AND NOT A CARRY, which is the sentence
#: ``docs/plan/rebuild-plan.md`` §5's ``type`` row owns and this module does not.**  The
#: exact carrier is a STRICT scalar, and strict is exact for exactly one of these three:
#: ``StrictBool`` admits what ``{"type": "boolean"}`` admits and nothing else, while
#: ``StrictInt`` refuses ``1.0`` and ``StrictFloat`` refuses ``1`` -- both of which
#: draft-07 ADMITS for ``integer`` and ``number``, so making the scalar strict there is
#: the one direction reading 1 forbids outright.  "Make the scalar strict" is therefore
#: not one rule but a per-word one, and §5's row reads "a scalar word -> ``str`` / ``int``
#: / ``float`` / ``bool``" for all four.  Changing that row is the owner's; declaring the
#: difference meanwhile is §2's own instruction for a widening the design has not closed.
_LAX_ACROSS_A_TYPE = frozenset({"boolean", "integer", "number"})


def _lax_across_a_type(extra: Any) -> bool:
    """Does this ``additionalProperties`` state a value type the class carries LOOSELY?

    True only for a SCHEMA-valued ``additionalProperties`` whose value is one scalar word
    in :data:`_LAX_ACROSS_A_TYPE`.  A list of words, a word with an ``enum`` or a ``const``
    beside it, and every non-scalar word are all False: the first two are a different fact
    with a different carrier, and the §8 witness that would prove either is not the
    undeclared-key one this declaration answers for.
    """
    if not isinstance(extra, Mapping):
        return False
    return extra.get("type") in _LAX_ACROSS_A_TYPE


def declare_object(
    node: nodes.Base,
    pointer: str,
    mod: compiler.Module,
    props: Sequence[ir.Field],
    shape: compiler.Shape,
    position: Position = Position.ROOT,
    *,
    extras: nodes.Node | None = None,
    bases: tuple[ir.TypeRef, ...] = (),
    branches: tuple[ir.TypeRef, ...] | None = None,
    rule_nodes: Sequence[Mapping[str, Any]] = (),
    rule_sites: Sequence[str] = (),
    description: str | None = None,
    root_required: tuple[str, ...] | None = None,
    discriminator: str | None = None,
    combinator: str | None = None,
) -> str | Refusal:
    """Assemble one class out of decided properties, and record what it declares.

    The other half shared with a composing row: D8's ``extra``, the description,
    the ``__adcp_schema__`` the renderer writes, and the :class:`Shape` a later
    subclass reads.  ``bases`` is empty for a node that composes nothing, and
    then the base is ``AdCPBaseModel``; a composing row passes the symbols its
    ``$ref`` conjuncts bound (D7 -- a base is DERIVED from what the document
    composes, never classified by hand), and ``AdCPBaseModel`` arrives through
    them.

    **D6's rule tuple is written HERE**, for the node being declared, and that is what
    makes "a rule attaches to the nearest class" true of every row rather than of the
    one that remembered.  This is the one funnel a class WITH FIELDS passes through --
    the object row, the ``allOf`` row and a union BRANCH all arrive here -- so the
    ``allOf`` row gets its root's ``not``/``dependencies``/``minProperties`` by passing
    through rather than by repeating the object row's call.  A rule renders nothing in a
    model's JSON schema, so the only instrument that observes one is a direct
    ``model_validate``, which is what ``src/adcp/types/_runtime.py`` records.

    ``rule_nodes`` are the OTHER nodes whose rules are this class's -- an ``allOf``
    conjunct, which draft-07 applies to the same instance.  Empty for every row but
    the composing one.  ``rule_sites`` is where the document STATES each of them, one
    pointer per node in the same order, and it exists for the DECLARATION and nothing
    else: a fact a conjunct states and this class does not carry is declared at the
    conjunct's own pointer, because that is where ``harness.check_widening`` will go
    looking for the fact to draw against.

    ``extras`` is the extras STORE as a parsed node -- the ``dict[K, V]`` §5 says a typed
    ``additionalProperties`` on a class is -- or ``None`` where the document states
    ``false``, ``true``, the empty schema or nothing.  The parser builds it
    (``schema.parse.extras_store``) and the three callers that can meet one pass it.

    ``root_required``, ``discriminator`` and ``combinator`` are §4's three facts a UNION
    BASE carries and no other class does, so all three are ``None`` for every row but
    the union row.  They are declared on the class rather than formatted into a body
    line, which is §7's gate at this seam: ``render._union_base_lines`` writes the four
    statements and nothing before it holds one.

    ``description`` is §6's description-authority rule clause 3, handed DOWN by the two
    rows that compose: a class whose own node states none states the one its base does,
    which the composed document states at this pointer.  Passed rather than merged into a
    declaration, because the node is a node now and §6 makes silence the enclosing
    reading rather than a rewritten mapping (``lower_composition`` and the union's
    ``$ref`` branch, which is a composition of the union base and the target).
    """
    # D8's typed row: a property the class does not DECLARE is validated against
    # the document's own value schema, through pydantic's ``__pydantic_extra__``.
    # The TYPE is the same ``dict[K, V]`` a mapping node lowers to, decided by the
    # same row -- the node is handed to :func:`decide` as the mapping it is, with
    # whatever the node says about its KEYS carried across (D5 types the key too),
    # so an extras store and a mapping cannot come to read ``additionalProperties``
    # two different ways.  :func:`decide` rather than an import of the container row,
    # because the per-node dispatch is one function and a second entrance to the
    # container row would be a second reading of which row a node belongs to.
    ap = node.extra
    # **§2's SECOND node rewrite, retired.**  This built a synthetic
    # ``{"type": "object", "additionalProperties": ap, "propertyNames": ...}`` and handed
    # it to the dispatch -- a node the document does not have.  The extras STORE is now a
    # ``nodes.Mapping_`` the PARSER builds, at the class's own pointer, with its value at
    # MAPV and its key at KEY (``schema.parse.extras_store``), so the extras store and a
    # mapping cannot come to read ``additionalProperties`` two different ways because
    # there is one reading of it and the parser makes it.
    extra_type = None
    if extras is not None:
        # No hop: the parser builds the extras store at the CLASS's own pointer, because
        # it is the same instance re-read (§4), so it inherits the class's own name entry
        # and its VALUE hangs off that pointer like any mapping's.
        #
        # **THE DISPATCH AND NOT THE WALK WRAPPER, and §4's shared pointer is the whole
        # reason.**  :func:`lower_node` is the dispatch plus
        # three statements about THE NODE AT A POINTER -- adopt the class an earlier
        # node of identical content declared at it, name the node where the bundle's
        # ``$ref``\\ s name its pointer, and seed the content memo at it.  A pointer
        # names ONE node, and the store is the one node in the tree that does not own
        # the pointer it carries: §4 hands it the CLASS's, so all three of those
        # statements are about the class standing here and none is about the store.
        # Routed through the wrapper they fire on the store, which declares an alias at
        # the class's own pointer moments before this function declares the class --
        # ``Module.declare``'s collision, measured on ``brand.json`` at
        # ``/definitions/colors``, a bundle-named class whose twelve properties and
        # whose typed ``additionalProperties`` are all one local ``$ref``.  The alias
        # would also be WRONG where it did not collide: a ``$ref`` to
        # ``#/definitions/colors`` names the object, so the symbol at that pointer is
        # the class and never the ``dict[K, V]`` its extras store comes to.
        #
        # The store's own CHILDREN keep the wrapper: its value sits at MAPV under
        # ``<pointer>/additionalProperties`` and its key at KEY, each at a pointer it
        # owns, and ``containers.mapping`` reaches both through ``lower_node`` as any
        # mapping's children are reached.  So a named or collapsed node inside the
        # store is named and collapsed exactly as it would be anywhere else.
        #
        # Imported on use, for the reason :func:`rules_at` is: ``codegen.lower.decide``
        # imports this module, and D13 fixes the direction, so this side is the lazy one.
        from codegen.lower.decide import decide as dispatch

        store = dispatch(extras, mod)
        if isinstance(store, Refusal):
            return store
        extra_type = store.type
        if _lax_across_a_type(ap):
            # **§2's declared widening for the one thing the store's TYPE does not
            # carry: the document's refusal of every OTHER JSON type**
            # (``adcp-client-python-szfx``, sub-cause A1).  ``dict[str, bool]`` states
            # the word the document states and pydantic's lax mode still admits a
            # value of another type for it, so the class is wider than
            # ``additionalProperties: {"type": "boolean"}`` at the one position §8 can
            # witness: an extra key has no FIELD, so the undeclared-key witness lands
            # on it directly.  Measured at ``core/media-buy-features.json#``:
            # ``MediaBuyFeatures.model_validate({"<an undeclared key>": 1})`` returns
            # ``{"<an undeclared key>": True}`` and the document refuses that value at
            # ``additionalProperties/type``.
            #
            # Rung CONTAINER, the cell's own answer, and the KEYWORD is
            # ``additionalProperties`` because that is the keyword the document writes
            # at this pointer -- the same pair ``lower.containers`` already mints for a
            # typed value beside a ``patternProperties``.
            from codegen.lower import approximate

            approximate.declare(mod, pointer, "additionalProperties", position, ap)
    #: What the DOCUMENT gives this class for ``extra``, read where the document-side
    #: fold puts the fact: this node's own ``additionalProperties`` first, and the value
    #: its BASES resolved where the node states none (:attr:`Shape.extra`, which carries the
    #: whole reason).  Written onto the class unconditionally below, so pydantic's
    #: ``model_config`` merge along the MRO cannot decide it.
    #:
    #: ``None`` only where neither the node nor anything it composes states one, and then
    #: ``AdCPBaseModel``'s own ``extra="ignore"`` is the answer -- one value, fixed by the
    #: model base rather than by which base happened to arrive second, so there is
    #: nothing for an MRO order to decide and nothing for this class to state.  That is
    #: the one case the row's "never inherits" does not reach, and it is written here
    #: rather than left implicit: the clobber is a disagreement between two bases, and
    #: silence everywhere is not one.
    resolved_extra = (
        "allow"
        if extra_type is not None
        else {False: "forbid", True: "allow"}.get(ap, shape.extra)
    )
    # **A COUNT KEYWORD MAKES THE CLASS KEEP THE KEYS IT COUNTS** (§8 sentence 4's second
    # consequence, decided 2026-11-03): *"a count keyword withheld from a class whose
    # extra policy drops the keys it counts is not answered by declaring the count -- it
    # is answered by the class KEEPING the keys the document counts.  Declaring it would
    # be declaring a difference the walk created.  That reverses the ``absent -> ignore``
    # reading at exactly those nodes and nowhere else."*
    #
    # So this is that reversal, and its scope is the condition: a node over which
    # ``min``/``maxProperties`` rides AND which states no extra policy anywhere.  With
    # ``allow`` the class retains every undeclared key, ``_runtime.supplied`` reads the
    # extras, and the rule counts what the document counts -- the two bounds then agree
    # and nothing is dropped in either direction, so no declaration is owed and none is
    # minted.  Without it ``lower.rules._count``'s gate withholds the MINIMUM, because a
    # rule counting the keys that survived ``ignore`` would refuse an instance the
    # document accepts, which is the narrowing §2 forbids outright.
    #
    # **WHAT RULED THIS OUT WAS A FIGURE OFF BY THREE ORDERS OF MAGNITUDE**, which is why
    # the measurement is here and not a paragraph of reasoning.  ``lower.rules._count``
    # carried "the gate withholds the minimum at 5,220 pointers in 209 documents" and
    # concluded a declaration set of that size was forbidden and the keeping-the-keys fix
    # too broad to take.  **Both halves rested on a count over the INLINED record and the
    # walk does not inline** -- it compiles each shared node once and imports the symbol.
    # Measured over the 1,054 portable documents by recording every call at which the gate
    # fires: **5 calls at 4 distinct (document, pointer)**, of which the minimum arm
    # reaches three and ONE class loses a rule by it --
    # ``core/provenance.json#/properties/disclosure/properties/jurisdictions/items/properties/render_guidance``.
    # The other two are ``maxProperties`` at ``/properties/ext`` in
    # ``core/account-change.json`` and its webhook twin, where the node is a MAPPING and
    # the drop is recorded and then discarded by this function's caller
    # (``adcp-client-python-gbo``'s sibling defect, filed and not fixed here).
    #
    # The read is over this node AND its rule sources, because the keyword and the extra
    # policy routinely sit on different conjuncts: ``core/positive-postal-area-support.json``
    # states the count on a conjunct that says nothing about extras while the base says
    # everything, which is the pair ``adcp-client-python-6oe`` was filed on.
    if resolved_extra is None and _a_property_count_rides(node, rule_nodes):
        resolved_extra = "allow"
    # **D6's reading runs AFTER the extra policy is resolved, because one of its gates IS
    # that policy** (``adcp-client-python-6oe``).  ``min``/``maxProperties`` are counted
    # over the keys the class RETAINED, so the gate ``lower.rules._count`` asks is "does
    # this class keep every key the document would count" -- ``forbid`` admits only
    # declared fields and ``allow`` keeps the extras, while a class with no policy at all
    # takes ``AdCPBaseModel``'s ``ignore`` and drops them.  Read off each VIEW's own
    # ``additionalProperties`` the gate answered about a different object: a conjunct
    # stating ``true`` passed it while the composed class it wrote the rule onto kept no
    # key, and ``PositivePostalAreaSupport`` lost its ``minProperties`` entirely because
    # the conjunct that states it says nothing about extras and the BASE says everything.
    # Nothing moves but the order; ``resolved_extra`` reads no rule.
    stated = compiler.rules_at(
        node,
        *rule_nodes,
        position=position,
        resolve=mod.resolve_node,
        at=tuple(rule_sites),
        keeps_every_key=resolved_extra is not None,
        root=mod.record,
    )
    # **Every fact a rule source states and this class does not carry is DECLARED here**
    # (``docs/plan/final-state.md`` reading 2; ``adcp-client-python-3bb``, ``-6oe``).  §5
    # decides what the ANNOTATION is -- an unreadable ``if`` compiles to "nothing, and the
    # schema half answers" -- and reading 2 decides what the MODULE says: a
    # ``model_validate`` that builds a payload the document refuses is reading 1 failing,
    # and §2 permits it only as a declared widening at its own pointer.  This is the one
    # funnel a class with fields passes through, which is what makes "a dropped fact is
    # declared" true of every row rather than of the one that remembered -- the same
    # sentence the rule TUPLE above is written here for.
    #
    # Imported on use, for the reason the rules module is: ``lower.approximate`` imports
    # this module for :class:`Module` and :func:`schema_ref`, so this side is the lazy one.
    if stated.dropped:
        from codegen.lower.approximate import declare as _declare_widening

        for drop in stated.dropped:
            _declare_widening(mod, drop.pointer, drop.keyword, drop.position, drop.fact)
    described = node.description if node.description is not None else description
    declaration = ir.ClassDecl(
        # **The POINTER in the name slot, until the pass runs** (§7, and
        # ``lower/names.py``'s own docstring): the walk computes no symbol, so what a
        # declaration carries is where it sits and ``names.assign`` binds the name §4
        # derives for it.
        name=pointer,
        ref=compiler.schema_ref(mod.document, pointer),
        fields=tuple(props),
        description=described,
        # D8, and §5's ``additionalProperties`` row: **a class DECLARES the ``extra``
        # the document gives it and never inherits it** (:attr:`Shape.extra`, which
        # carries the measurement).  It read the node's own value alone and left
        # ``None`` -- "absent leaves the base's default in place" -- and that sentence
        # is the defect: pydantic merges ``model_config`` along the MRO, so a class
        # composing TWO bases took whichever value the later one carried and a default
        # ``ignore`` silently overrode an ``allow`` the document states.  A TYPED
        # ``additionalProperties`` is ``allow`` with the type beside it: the properties
        # are part of the document, so they are retained, and ``__pydantic_extra__`` is
        # what validates them.
        extra=resolved_extra,
        extras=extra_type,
        bases=bases,
        rules=stated.rules,
        root_required=root_required,
        discriminator=discriminator,
        combinator=combinator,
        branches=branches,
    )
    # :attr:`Shape.decided` is written HERE and by no caller, for the reason the rule
    # tuple above is: this is the one funnel a class with fields passes through, so a
    # row cannot forget to record what it decided.
    # The caller's own ``decided`` is what the class INHERITS (a composing row passes
    # its bases'), and the props it is handed are this class's own and win the key.
    #
    # **It recorded the module's declared POINTERS here too and no longer does.**  That
    # set was read in one place -- a reuser asking whether a symbol was importable from
    # the base -- and the answer it gave was a snapshot of one moment in another
    # module's walk.  Where a symbol is importable from is a fact about two DOCUMENTS,
    # so ``emit.resolve`` answers it off the target's finished symbol table and its
    # :attr:`Module.imported` record (:attr:`Target.imports`).
    #
    # **A UNION BASE records one too, and what it is NOT allowed to do is CROSS A
    # MODULE BOUNDARY.**  §5's ``$ref`` row at CONJ decides a union root by name --
    # "where it is not a class declaring fields -- a scalar, an enum, a container, or a
    # UNION ROOT, whose instance is one of its branches -- it is not a class a model can
    # extend" -- and that is a statement about a REUSER in another document.  Inside the
    # declaring module the base's shape is exactly what §4's "a branch composes its own
    # with them" needs: a branch class subclasses the base, so the base's declarations
    # and decided fields are what it inherits.  So the record is written here for every
    # class and ``emit.resolve`` is what declines to hand a union base's across, keyed
    # on :attr:`codegen.ir.ClassDecl.branches` -- the fact that says the instance is one
    # of the branches, read where the :class:`Target` is built.
    mod.shapes[pointer] = replace(
        shape,
        decided={**shape.decided, **{p.wire: p for p in props}},
        description=described,
        # TRANSITIVE for :attr:`Shape.decided`'s reason: a subclass of THIS class reads
        # one value rather than walking a chain of base documents to find who last
        # stated an ``additionalProperties``.
        extra=resolved_extra,
    )
    collision = mod.declare(pointer, declaration)
    if collision is not None:
        return collision
    return pointer


def lower_object(
    node: nodes.Object,
    mod: compiler.Module,
    *,
    bases: tuple[ir.TypeRef, ...] = (),
    inherits: compiler.Shape | None = None,
) -> str | Refusal:
    """Append the class for an object NODE, children first, and return its POINTER.

    **Converted to node fields** for everything structural: the properties are the child
    nodes the parser built at PROP, in the document's own key order; the extras store is
    :attr:`nodes.Object.extras`; ``propertyNames`` is :attr:`nodes.Object.key`; the type
    word is :attr:`nodes.Object.word` and the word an enclosing node applies to the same
    instance is :attr:`nodes.Base.applied`, which is what ``mod.object_constrained`` was
    read as per node.  The ADMISSION SCREEN is :attr:`nodes.Base.declares` at the node's
    own position and the ``required`` shape is :attr:`nodes.Base.faults`, which §4 makes
    the parser's; :class:`Shape` takes :attr:`nodes.Base.declared`, the property
    DECLARATIONS, because that is what §2's intersection rule merges.

    ``bases`` is what a COMPOSITION and a union BRANCH need and a leaf object does not,
    and it defaults to the leaf's answer -- no base, so the base is ``AdCPBaseModel`` --
    so the object row's call sites are unchanged and so is every module they emit.  It is
    :class:`codegen.ir.ClassDecl`'s own.  Two others are gone: ``decided``, with the union
    row's private ``const`` lowering (:func:`fields` says why), and ``body_lines``, with
    the text itself (§7) -- a rule is :attr:`Rules.rules` and a union base's facts are
    :func:`declare_object`'s own three arguments.
    """
    # D6's six families are handled HERE and not refused: a rule attaches to the
    # nearest class, so a node with fields is the only node that can carry one.  The
    # reading is :func:`rules_at`'s, which is also where the TUPLE is written
    # (:func:`declare_object`) -- so this row and the ``allOf`` row and a union branch
    # all admit the same keywords and all write the same rule.
    pointer, position = node.pointer, node.position
    stated = compiler.rules_at(node, position=position, resolve=mod.resolve_node, root=mod.record)
    refused = compiler.check_keywords(
        node,
        # The cells an OBJECT node consumes, which is what is left of a ``handled``
        # set once the table admits everything it used to carry for admission alone.
        {
            "type",
            "properties",
            "required",
            "additionalProperties",
            "propertyNames",
            *stated.screen,
        },
        mod=mod,
    )
    if refused is not None:
        return refused
    declared = node.word
    if declared != "object" and not (declared is None and node.applied == "object"):
        # A node carrying ``properties`` and no ``type`` ADMITS A NON-OBJECT: JSON
        # Schema applies ``properties`` only to objects and asserts nothing about
        # anything else, so ``{"properties": {"a": {"type": "string"}}, "required":
        # ["a"]}`` admits ``"hello"`` and ``42`` -- measured with ``jsonschema`` on
        # exactly that node.  No class can, so the model is NARROWER than its
        # document, which is the defect P3 removes.
        #
        # This condition read ``in (None, "object")`` and 0 of the 43 documents
        # emitted before step 5 exercise the ``None`` arm -- every one of them
        # declares ``type: object`` -- so the tolerance was latent rather than
        # relied on.  Step 5's union BRANCHES are the first population to reach it,
        # and they reach it in the worst way: the accepts check reports
        # ``model_type`` on a valid instance, which is the model refusing a payload
        # the document admits.
        #
        # **``mod.object_constrained`` is what keeps it from reading the node in
        # ISOLATION, which was the other half of the defect.**  draft-07 applies a
        # root's assertions and its combinator branch's to the SAME instance, so
        # ``{"type": "object", "oneOf": [{"properties": ...}]}`` admits only objects
        # and the branch at ``/oneOf/0`` restates nothing: there is no non-object for
        # the class to be narrower than.  This refusal fired for 11 documents whose
        # own root declares ``type: object`` three lines above the branch, and for 33
        # whose node is a PROPERTY's own schema -- where nothing constrains the value
        # and the refusal is right.  ``bundle.constrained_to_object`` is the one
        # reading of which is which.
        #
        # A node declaring a type that is NOT ``object`` is still refused whatever
        # encloses it: a conjunction of ``object`` and ``string`` admits nothing, and
        # a class for it would accept what the document refuses.
        return Refusal(
            "type",
            pointer,
            f"an object node must declare type: object; this one declares "
            f"{node.word if node.word is not None else '<absent>'!r} and nothing enclosing it constrains the "
            "instance to an object, so the document admits a non-object that no class can",
            kind=Kind.VERDICT,
        )
    if not node.properties and not node.declared:
        # **``declared`` and not ``properties`` alone, because the two came apart**:
        # §5's ``properties`` row drops a property whose declaration ADMITS NOTHING from
        # the FIELDS (``schema.parse._object``) and leaves it in
        # :attr:`nodes.Base.declared`, which is the document's own map.  A node whose
        # every declaration admits nothing then has no field and this refusal's own
        # sentence would be false of it: the document declares a property, and what it
        # says about the key is that it may not appear.  Such a node is a class with no
        # fields carrying the ``ForbiddenGroups`` the presence half lowers to -- which is
        # the shape §5 already emits for a presence-only union branch -- and its accepted
        # set is every object not carrying the key, which is not nothing and must not be
        # refused.  The bundle states no such node (all three of its forbidding nodes
        # declare other properties beside the forbidden key), so this moves no document;
        # it is written this way so that the first one to arrive is read by what it
        # declares rather than by a sentence that is no longer about it.
        return Refusal(
            "properties",
            pointer,
            "an object node with no property declared",
            kind=Kind.VERDICT,
        )
    if "required" in node.faults:
        return Refusal("required", pointer, node.faults["required"], kind=Kind.VERDICT)
    required = node.required
    built = fields(node.properties, required, pointer, mod, distinct=stated.distinct)
    if isinstance(built, Refusal):
        return built
    return declare_object(
        node,
        pointer,
        mod,
        built,
        # :attr:`nodes.Base.declared` is the property DECLARATIONS, which is what a
        # :class:`Shape` is: §2's intersection rule merges declarations of one property
        # and §4 "Names" reads a branch's own ``const`` pin off one.
        # **``extra`` is the one thing this row INHERITS, and §5's
        # ``additionalProperties`` row is why it has to** (2026-10-29): the branch arm of
        # ``lower.union`` reaches this row for a branch whose base declares no property,
        # and a base declaring none can still have resolved an ``allow`` -- a root
        # stating ``additionalProperties: true`` beside its combinator and no
        # ``properties``.  Left out, the class states nothing and pydantic's
        # ``model_config`` merge decides, which is the clobber :attr:`Shape.extra`
        # records.  Nothing else of a base is read here, because a base that declares a
        # property sends the branch to ``lower_composition`` instead.
        compiler.Shape(
            node.declared,
            frozenset(required),
            extra=None if inherits is None else inherits.extra,
        ),
        position,
        extras=node.extras,
        bases=bases,
    )
