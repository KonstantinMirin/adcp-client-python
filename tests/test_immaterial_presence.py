"""§8 sentence 3b read in the POSITIVE direction: an IMMATERIAL clause, and a COMPLEMENT
at a property declaration.

``docs/plan/rebuild-plan.md`` §8 sentence 3b (decided 2026-11-03) derives two things and
``tests/test_negated_condition.py`` grades one of them.  That file is about the NEGATIVE
direction -- ``not: {required: [k], properties: {k: {const: v}}}``, where the De Morgan
step produces the immaterial state -- and the sentence is more general than the one
reading:

    **Presence becomes three-state -- must be present, must be absent, immaterial -- and
    the value set gains its complement.**

**Both halves have a POSITIVE-direction site in this bundle, and both declared an
approximation until this row.**  The declaration was the only instrument that saw them,
because every one of them PASSES: a model wider than its document is permitted by §2, so
a dropped conditional moves no verdict and nothing but the declaration reports it.

* **THE IMMATERIAL CLAUSE.**  ``if: {properties: {k: {const: v}}}`` with no ``required``
  is draft-07's *"k is absent, or k is present and equals v"*, because a ``properties``
  entry constrains an instance only where the key is there.  That is the IMMATERIAL state
  exactly.  ``lower.rules._clauses`` refused to mint it in the positive direction -- its
  own comment said *"a clause cannot say 'absent or one of these'"*, which was the
  two-state flag speaking -- so **35 conditions of this bundle, in 6 documents, declared
  a fact the vocabulary could already carry**; 25 of the 35 are one ``scenario`` key under
  ``compliance/comply-test-controller-request.json``.
* **THE COMPLEMENT AT A PROPERTY DECLARATION.**
  ``properties: {k: {not: {const: v}}}`` beside ``required: [k]`` is *"k is present and k
  is not v"* -- the key, presence REQUIRED, ``v`` FORBIDDEN.  ``media-buy/get-products-response.json#/allOf/2``
  is the one site the bundle states it at, and the ``Match`` field that carries it was
  already there: what was missing was the one function that reads a ``not`` at a property
  declaration (``lower.rules._excluded``).

**THE OBLIGATION THIS FILE HOLDS IS CONNECTEDNESS, AND IT IS A STRICTER ONE THAN A
DECLARATION.**  A rule that is present but unreached is worse than a declaration, because
the declaration at least says the fact is missing.  So each form is graded twice:

* by IDENTITY -- the rule the bundle's own condition reduces to is bound on a class a
  consumer imports (:func:`test_every_rule_the_two_forms_mint_is_bound_on_a_class_of_the_tree`);
* by VALUE -- a payload that violates the consequent is REFUSED by the class with this
  rule's own sentence in the refusal, and the document refuses it too; and a payload that
  breaks the condition is ADMITTED
  (:func:`test_each_form_refuses_a_payload_its_document_refuses_and_admits_one_it_admits`).

**AND THE DECISIVE VALUE IS THE ABSENT ONE.**  For the immaterial form the witness that
could not exist before is the instance with the key REMOVED: the condition holds by
ABSENCE, so the consequent applies, and a ``present=True`` clause would not fire there.
A row that quietly narrowed the immaterial state back to the two-state flag would pass
every other assertion here and fail that one.

**NO PAYLOAD IS HAND-WRITTEN.**  Every one is the committed accepts floor's own drawn
instance for the pair (``tests/accepts-corpus``, replayed through ``harness.check_accepts``)
with keys the RULE names set to values the DOCUMENT states for them -- the ``const`` or
``enum`` the condition pins, the value the complement forbids, or the key removed.  The
document is the arbiter in both directions: a candidate is asserted refused by the class
only where ``conforms`` says the document refuses it.
"""

from __future__ import annotations

import collections
from pathlib import Path
from typing import Any

import compared
import corpus
import test_emit as TE
from nodeset import claimed
from pydantic import ValidationError

from adcp.types._runtime import ConditionalRequired, Match, NegatedConditional, bound_rules
from codegen import bundle, harness
from codegen.lower import rules

BUNDLE = Path(__file__).resolve().parents[1] / "schemas" / "cache" / "3.2"

#: The two forms this row lowers, as a predicate on ONE clause.  Named rather than spelled
#: at each reader, because the population test and the value test must range over the same
#: thing or the second grades a subset of the first and nothing says so.
IMMATERIAL, COMPLEMENTED = "immaterial presence", "complemented value set"

#: The state of an immaterial clause that NO two-state flag can reach: the key did not
#: arrive, and the condition holds anyway.  Named because the value test counts it apart
#: from every other witness and a literal spelled twice is a literal that goes stale.
ABSENT = "the key ABSENT"


def form_of(clause: Match) -> str | None:
    """Which of the two forms this clause is, or ``None`` where it is neither.

    ``present is None`` is the state §8 sentence 3b adds, and ``forbidden is not None``
    beside ``present is True`` is the complement read at a property declaration.  A clause
    that is immaterial AND complemented is the NEGATIVE direction's own output
    (``_complement``, graded by ``tests/test_negated_condition.py``) and is reported as
    :data:`IMMATERIAL`, because that is the state this row has to keep reachable.
    """
    if clause.present is None:
        return IMMATERIAL
    if clause.forbidden is not None:
        return COMPLEMENTED
    return None


def _conditions(negated: bool = False) -> dict[tuple[str, str], Any]:
    """Every ``(document, pointer)`` of the bundle whose ``if`` reduces to one of the forms.

    Read off the SOURCE bundle through ``bundle.nodes_at`` -- the one walk -- and through
    ``lower.rules._clauses`` at the document's own root, so the population is a function of
    the bundle and of the reduction and not of a literal in this file.

    **The condition's own keys decide the DIRECTION, and the two are kept apart because
    one RULE VALUE cannot say which it came from.**  A condition that is exactly a ``not``
    is the NEGATIVE direction -- ``tests/test_negated_condition.py``'s population -- and
    ``_complement`` produces an immaterial clause there too, so a reader asking "is this
    bound rule one this row lowers" has to ask it of the positive population alone.
    ``negated=True`` is the other half, read by the same walk so the two cannot drift.
    """
    found: dict[tuple[str, str], Any] = {}
    for document in bundle.portable(BUNDLE):
        root = bundle.read(BUNDLE, document)
        for pointer, node, _ in bundle.nodes_at(root):
            condition = node.get("if")
            if not isinstance(condition, dict):
                continue
            if (set(rules._keys(condition)) == {"not"}) is not negated:
                continue
            read = rules._clauses(condition, root)
            if read is None:
                continue
            forms = {form_of(Match(*clause)) for clause in read} - {None}
            if forms:
                found[document, pointer] = (read, sorted(forms))
    return found


def _minted(negated: bool = False) -> set[tuple[Match, ...]]:
    """The ``when`` of every rule the reduction mints in one direction."""
    return {
        tuple(Match(*clause) for clause in read)
        for read, _ in _conditions(negated).values()
    }


def _bound() -> dict[str, list[tuple[Any, Any]]]:
    """Every conditional rule the TREE binds that carries one of the two forms.

    ``(the pair's ref, the rule)`` per form, over ``bound_rules`` -- the MRO read, not an
    attribute read -- so a rule a union root states and a branch shadows is still seen.
    The tree is the one a fresh run emits, which ``tests/fresh.py`` binds; this is the
    CONNECTEDNESS half and reading the committed artifact would grade a different tree.

    **Restricted to the POSITIVE direction**, by :func:`_minted`: the one rule the bundle
    states in the negative direction (``formats/canonical/_base.json#/properties/slots/items``)
    carries an immaterial clause as well, and it is graded by
    ``tests/test_negated_condition.py``.  Asserted to be exactly that one below, so the
    restriction cannot quietly drop a positive rule.
    """
    positive = _minted()
    out: dict[str, list[tuple[Any, Any]]] = collections.defaultdict(list)
    for paired in compared.pairs():
        if not isinstance(paired.model, type):
            continue
        for rule in bound_rules(paired.model):
            if not isinstance(rule, (ConditionalRequired, NegatedConditional)):
                continue
            if rule.when not in positive:
                continue
            for form in {form_of(clause) for clause in rule.when} - {None}:
                out[form].append((paired.ref, rule))
    return out


def test_the_population_is_the_two_forms_and_the_bundle_states_both() -> None:
    """Both forms have a positive-direction site, and the figures are the row's.

    **NEITHER A COUNT NOR A SET LITERAL, and that is the decision rather than a gap.**
    The SITES are graded by ``tests/test_the_declared_backlog.py``, whose pin is what fell
    by 36 when these started lowering, so a second literal of the same population here
    would be a second answer to one question -- and a census pinned with ``==`` is what
    ``tests/test_every_check_names_its_set.py``'s first rule forbids outright.  The
    figures are stated in this module's docstring as measurements: **53 immaterial
    conditions and 1 complemented one**, 35 and 1 of which carry a consequent that states
    a presence fact and therefore mint a rule.

    What this asserts is that neither form has an EMPTY population -- a form with no site
    is a reduction nothing exercises, and the two tests below would then pass by looping
    over nothing.
    """
    stated = _conditions()
    claimed("positive-direction conditions of the two forms", stated)
    by_form = collections.Counter(
        form for _, forms in stated.values() for form in forms
    )
    assert set(by_form) == {IMMATERIAL, COMPLEMENTED}, (
        by_form,
        sorted({document for document, _ in stated}),
    )


def test_every_rule_the_two_forms_mint_is_bound_on_a_class_of_the_tree() -> None:
    """CONNECTEDNESS by identity: each form reaches a class a consumer imports.

    **A rule that is present but unreached is worse than a declaration**, so the claim is
    not that the reduction returns a clause -- that is
    :func:`test_the_population_is_the_two_forms_and_the_bundle_states_both` -- but that
    the rule it reduces to is in some emitted class's ``_adcp_rules``, where
    ``RuleBound``'s one validator reads it.

    Not a site-by-site equality with the bundle population, and the reason is measured:
    the reduction reads a condition at every node of the bundle, and a condition whose
    ARM states no presence fact yields no rule at all (``lower.rules._branch``) -- 14 of
    the 54 immaterial conditions are such a node, every one of them a ``then`` that
    narrows a value and nothing else, which §5 compiles to nothing on the model and whose
    ceiling ``lower.rules``' own docstring names.  So the obligation is stated over the
    rules, in both directions: every bound rule of a form must be one the reduction mints
    somewhere, and every form must have bound rules.
    """
    bound = _bound()
    for form in (IMMATERIAL, COMPLEMENTED):
        rows = claimed(f"rules bound on a class carrying a {form} clause", bound[form])
        assert rows, f"{form} reaches no class of the tree: the rule is unconnected"
    # **35 + 1 = 36 DISTINCT RULES, WHICH IS THE NUMBER OF DECLARATIONS THAT LEFT**
    # ``tests/test_the_declared_backlog.py``'s pin in the same commit (128 facts in 63
    # documents -> 92 in 58).  The two figures are the same fact read from the two ends: a
    # rule arrived exactly where a declaration left, and nothing arrived in the pin.  **The
    # figure is NOT asserted here**, because that pin is the instrument that holds it and a
    # census pinned with ``==`` is ``test_every_check_names_its_set``'s first rule; what is
    # asserted is the relation that makes the two figures the same fact -- every bound rule
    # of these forms is one the bundle's own conditions reduce to, below.
    #
    # EVERY conditional rule of the tree carrying one of the forms is one of the two
    # directions' own, so the restriction in :func:`_bound` cannot hide a rule that came
    # from neither -- a clause state nothing in the bundle reduces to would be a value the
    # walk invented, which §9 forbids by name.
    directions = _minted() | _minted(negated=True)
    stray = [
        f"{paired.ref.document}{paired.ref.pointer}: {rule!r}"
        for paired in compared.pairs()
        if isinstance(paired.model, type)
        for rule in bound_rules(paired.model)
        if isinstance(rule, (ConditionalRequired, NegatedConditional))
        and {form_of(clause) for clause in rule.when} - {None}
        and rule.when not in directions
    ]
    assert stray == [], {"rules of these forms no condition of the bundle reduces to": stray}


def test_the_immaterial_state_is_the_one_the_document_states_and_no_pair_distinguishes_it() -> None:
    """The clause the reduction MINTED carries the immaterial state, asserted on the clause.

    **This is where the three-state presence is graded, and the reason it is here rather
    than at a payload is measured.**  Over the 39 bindings of the immaterial form, the
    condition's key is a REQUIRED FIELD of the class the rule lands on in **39 of 39** --
    the enclosing document requires it, through its own ``required`` or through a
    composition -- so no payload a consumer can offer ``model_validate`` reaches the arm
    where the key is absent: pydantic refuses at the field layer first.  On this bundle a
    ``present=True`` clause would therefore be observationally EQUAL to the immaterial one
    at every one of the 36 rules.

    **That does not make the state a matter of taste, and it is not asserted as one.**  The
    document's condition is *"k absent, or k present and in this set"* and the clause has to
    SAY that, because the next document to state the same condition at a position that does
    not require the key would be read wrongly by a ``present=True`` clause -- it would hold
    at fewer instances than the document's condition, the consequent would go unenforced,
    and the class would silently widen with nothing declaring it.  So the claim graded here
    is the clause's own: every immaterial clause the reduction mints admits the ABSENT
    instance, and the ``present=True`` reading of the same clause refuses it.

    The clauses are the BUNDLE's -- :func:`_minted` reads them off the documents through the
    reduction -- so this is not a unit test of ``Match`` (``tests/test_negated_condition.py``
    holds that) but the same assertion made of the values this row actually emits.
    """
    clauses = [
        clause
        for when in _minted()
        for clause in when
        if form_of(clause) == IMMATERIAL
    ]
    assert claimed("immaterial clauses the reduction mints", clauses)
    wrong = []
    for clause in clauses:
        if clause.holds(frozenset(), {}) is not True:
            wrong.append(f"{clause!r} refuses the ABSENT instance")
        if Match(clause.key, True, clause.allowed, clause.forbidden).holds(frozenset(), {}):
            wrong.append(f"{clause!r} is not distinguished from present=True")
        if clause.allowed is not None:
            held = frozenset({clause.key})
            if clause.holds(held, {clause.key: clause.allowed[0]}) is not True:
                wrong.append(f"{clause!r} refuses the value its condition pins")
            if clause.holds(held, {clause.key: _ALIEN}) is not False:
                wrong.append(f"{clause!r} holds of a value its condition does not pin")
    assert wrong == [], wrong


#: A value no ``const`` or ``enum`` of this bundle names, for the one assertion that needs
#: a value OUTSIDE a condition's set.  Not a payload: it never reaches a class, only
#: :meth:`Match.holds`, whose comparison is ``in`` over the document's own tuple.
_ALIEN = object()


def _accepted(graded: TE.Graded) -> Any | None:
    """The committed accepts floor's own drawn instance for this pair, or ``None``.

    ``examples=1`` and the committed store, which is what every other reader of this
    population passes: the floor replays in milliseconds and the draw it replaces is 99.3%
    of a pair (``tests/corpus.py``).  ``None`` where the pair has no held instance, which
    the caller reports rather than skipping silently.
    """
    pair = TE.pair_of(graded)
    seen: list[Any] = []
    harness.check_accepts(
        pair.schema,
        pair.accept,
        examples=1,
        custom_formats=TE.FORMAT_STRATEGIES,
        seen=seen,
        ref=pair.ref,
        corpus=corpus.STORE,
        identity=pair.identity,
    )
    return seen[0] if seen and isinstance(seen[0], dict) else None


def _a_value_the_document_states(node: Any, key: str) -> Any:
    """A value for ``key`` taken from what the DOCUMENT declares for it.

    Needed only for a consequent that FORBIDS a key: violating such a consequent means
    supplying the key, and the value has to come from somewhere.  It comes from the
    document -- the ``const`` or the first ``enum`` member where the declaration pins one,
    otherwise the empty value of the ``type`` it states -- so nothing here is a value this
    file invented.  ``None`` where the document states no type to build one from, and the
    caller then has no witness for that name and says so.
    """
    declared = (node.get("properties") or {}).get(key)
    if not isinstance(declared, dict):
        return None
    if "const" in declared:
        return declared["const"]
    members = declared.get("enum")
    if isinstance(members, list) and members:
        return members[0]
    return {"string": "", "integer": 0, "number": 0.0, "boolean": False, "array": [], "object": {}}.get(
        declared.get("type")
    )


def _holds(instance: dict, clause: Match) -> list[tuple[str, dict]]:
    """Payloads in which ``clause`` HOLDS, derived from one the class already accepted.

    One per state the clause admits, named by the state, because the states are what §8
    sentence 3b is about and a single payload would grade one of them:

    * a VALUE the clause admits -- the ``const`` or the first ``enum`` member the condition
      pins, or the instance's own value where the clause only forbids and that value is not
      forbidden;
    * the key ABSENT, for an IMMATERIAL clause only.  **This is the state that could not
      exist before**: the condition holds because the key did not arrive, and a
      ``present=True`` clause does not fire there.
    """
    out: list[tuple[str, dict]] = []
    if clause.allowed is not None:
        out.append(("a value the condition pins", {**instance, clause.key: clause.allowed[0]}))
    elif clause.forbidden is not None and instance.get(clause.key) not in clause.forbidden:
        out.append(("the drawn value, which the condition does not forbid", dict(instance)))
    if clause.present is None:
        out.append(
            (ABSENT, {k: v for k, v in instance.items() if k != clause.key})
        )
    return out


def _breaks(instance: dict, clause: Match) -> list[tuple[str, dict]]:
    """Payloads in which ``clause`` FAILS, derived the same way.

    The complement's forbidden value is the one state that breaks a complemented clause,
    and a ``present=True`` clause is broken by the key's absence.  A clause pinning a value
    set is broken by the instance's OWN value where the draw did not happen to pin it --
    taken from the draw rather than invented, so the payload stays one the document admits.
    """
    out: list[tuple[str, dict]] = []
    if clause.forbidden is not None:
        out.append(("the value the condition forbids", {**instance, clause.key: clause.forbidden[0]}))
    if clause.allowed is not None and instance.get(clause.key) not in clause.allowed:
        if clause.key in instance:
            out.append(("the drawn value, which the condition does not pin", dict(instance)))
    if clause.present is True:
        out.append(("the required key ABSENT", {k: v for k, v in instance.items() if k != clause.key}))
    return out


def _violations(node: Any, instance: dict, rule: Any) -> list[tuple[str, dict]]:
    """Payloads violating ``rule``'s CONSEQUENT: a required name dropped, a forbidden one added."""
    out: list[tuple[str, dict]] = []
    for name in rule.require:
        if name in instance:
            continue  # the draw supplied it, so dropping it is the witness below
        out.append((f"without the required {name!r}", dict(instance)))
    for name in rule.require:
        if name in instance:
            out.append((f"without the required {name!r}", {k: v for k, v in instance.items() if k != name}))
    for name in rule.forbid:
        value = _a_value_the_document_states(node, name)
        if value is not None or name in (node.get("properties") or {}):
            out.append((f"carrying the forbidden {name!r}", {**instance, name: value}))
    return out


#: The sentence every conditional rule writes into its own refusal
#: (``_runtime.ConditionalRequired.errors``), which is how a refusal is attributed to THIS
#: rule rather than to any other thing the class might have refused the payload for.
#: Two words and not the whole message, because the condition's own text follows them.
SENTENCES = ("required when", "forbidden when")


def _refused_by_the_rule(model: type, payload: dict) -> tuple[bool, list[str]]:
    """Did the CLASS refuse ``payload``, and did a conditional rule's own sentence say so?

    ``model_validate`` and not the pair's entry point: §2 gives acceptance to the schema
    half, and the question reading 1 asks is what a consumer who CONSTRUCTS gets.  The
    messages are returned beside the answer so a failure names what the class actually
    said.
    """
    try:
        model.model_validate(payload)
    except ValidationError as error:
        said = [str(one.get("msg", "")) for one in error.errors()]
        return True, said
    return False, []


def test_each_form_refuses_a_payload_its_document_refuses_and_admits_one_it_admits() -> None:
    """CONNECTEDNESS by VALUE, per form, over the committed accepts floor.

    Three claims, and the DOCUMENT is the arbiter of which apply:

    * **AGREEMENT.** A payload in which the condition holds and the consequent is violated
      is one the document refuses (``conforms`` is asked first, so a candidate the document
      admits is never asserted against), and the class must refuse it.  A class ADMITTING
      one is reading 1 failing in §8 sentence 1's second direction -- *a value the document
      refuses and the class admits* -- and is the defect this file exists to catch.
    * **ATTRIBUTION.** Agreement alone does not prove the RULE: a class can refuse the same
      payload at the field layer, and where the condition's key is itself an unconditionally
      required FIELD, removing it is refused there and the after-validator never runs at
      all.  So each form must produce at least one refusal carrying this rule's OWN sentence
      (:data:`SENTENCES`), which is the rule firing and nothing else.
    * **NO NARROWING.** A payload in which the condition is BROKEN and which the document
      admits must be admitted, and in particular must not carry the rule's sentence: a rule
      firing where the document's conditional does not is the narrowing §2 forbids outright,
      and it is the one outcome worse than the widening this row removes.

    **The ABSENT state is required to reach a payload and is NOT required to be
    attributed, and the difference is a MEASUREMENT rather than a concession**: in all 39
    bindings of the immaterial form, the condition's key is a REQUIRED FIELD of the class
    that carries the rule, so removing it is refused at the field layer and the
    after-validator never runs.  That is asserted from the other side by
    :func:`test_the_immaterial_state_is_the_one_the_document_states_and_no_pair_distinguishes_it`,
    which is where the state itself is graded -- on the clause the reduction minted from
    the document.
    """
    bound = {
        ref: rule
        for form in (IMMATERIAL, COMPLEMENTED)
        for ref, rule in _bound()[form]
    }
    graded = {f"{g.ref.document}{g.ref.pointer}": g for g in TE.graded()}
    attributed: dict[str, list[str]] = collections.defaultdict(list)
    agreed: dict[str, list[str]] = collections.defaultdict(list)
    admitted: dict[str, list[str]] = collections.defaultdict(list)
    disagreed: list[Any] = []
    no_instance: list[str] = []

    for ref, rule in sorted(bound.items(), key=lambda kv: f"{kv[0].document}{kv[0].pointer}"):
        name = f"{ref.document}{ref.pointer}"
        row = graded.get(name)
        if row is None:
            continue
        instance = _accepted(row)
        if instance is None:
            no_instance.append(name)
            continue
        pair = TE.pair_of(row)
        model = row.model
        if not isinstance(model, type):
            continue
        forms = {form_of(clause) for clause in rule.when} - {None}
        # **THE DRAWN INSTANCE ITSELF IS THE FIRST no-narrowing WITNESS**, and it is the
        # one every rule has: the accepts check already proved the class admits it, so what
        # this adds is the ATTRIBUTION -- the rule must not be among the reasons, because
        # the document admits this payload and a rule refusing it is the narrowing §2
        # forbids outright.  For a complemented clause it is also the only such witness the
        # bundle offers: breaking *"status is not rejected"* means SAYING ``rejected``, and
        # the document's own ``else`` arm then refuses the payload for its own reasons.
        if harness.conforms(pair.schema, instance) is not False:
            said, messages = _refused_by_the_rule(model, instance)
            if said and any(one.startswith(SENTENCES) for one in messages):
                disagreed.append(
                    {
                        "pair": name,
                        "rule": repr(rule),
                        "the document ADMITS": "the drawn instance",
                        "and the rule refused it": messages,
                    }
                )
            else:
                for form in forms:
                    admitted[form].append(f"{name}: the drawn instance")
        for clause in rule.when:
            form = form_of(clause)
            if form is None:
                continue
            for state, held in _holds(instance, clause):
                for how, candidate in _violations(pair.schema, held, rule):
                    if harness.conforms(pair.schema, candidate) is not False:
                        continue  # the document admits it: there is nothing to refuse
                    said, messages = _refused_by_the_rule(model, candidate)
                    if not said:
                        disagreed.append(
                            {
                                "pair": name,
                                "rule": repr(rule),
                                "the document refuses": f"{state}, {how}",
                                "and the class ADMITTED it": "the model is wider",
                            }
                        )
                        continue
                    agreed[form].append(f"{name}: {state}, {how}")
                    if state == ABSENT:
                        agreed[f"{form} / absent"].append(f"{name}: {how}")
                    if any(one.startswith(SENTENCES) for one in messages):
                        attributed[form].append(f"{name}: {state}, {how}")
            for state, broken in _breaks(instance, clause):
                if harness.conforms(pair.schema, broken) is False:
                    continue  # the document refuses it for some other reason
                said, messages = _refused_by_the_rule(model, broken)
                if said and any(one.startswith(SENTENCES) for one in messages):
                    disagreed.append(
                        {
                            "pair": name,
                            "rule": repr(rule),
                            "the document ADMITS": state,
                            "and the rule refused it": messages,
                        }
                    )
                    continue
                admitted[form].append(f"{name}: {state}")
        assert forms, (name, rule)

    assert disagreed == [], disagreed
    assert no_instance == [], {"pairs with no held accepts instance": no_instance}
    witnesses = {key: len(value) for key, value in sorted(attributed.items())}
    assert agreed[IMMATERIAL] and agreed[COMPLEMENTED], {
        key: len(value) for key, value in sorted(agreed.items())
    }
    assert attributed[IMMATERIAL] and attributed[COMPLEMENTED], witnesses
    assert agreed[f"{IMMATERIAL} / absent"], {
        "the immaterial clause's ABSENT state reached no payload at all": witnesses
    }
    assert admitted[IMMATERIAL] and admitted[COMPLEMENTED], {
        key: len(value) for key, value in sorted(admitted.items())
    }
