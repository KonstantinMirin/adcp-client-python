"""An ``allOf`` root: the reference conjuncts become BASES, and the rest becomes
fields of the node itself.

D2's product row.  Two things come out of one conjunct list, and a third is
deliberately absent:

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

**A subclass never restates an inherited field.**  That is this module's one merge
rule: a restatement is admitted only when it NARROWS, meaning it keeps every
keyword the inherited declaration states, with the same value, and adds at least
one more.  Everything else is either nothing (the field is inherited, and the
subclass declares no field at all) or a conflict (the document is refused).
:func:`_restatement` is the whole decision, and it is SYMMETRIC, so there is no
order-dependent "last wins" to come back to -- a generator that let the later
conjunct win made its accepted set a function of member order.

MEASURED over this step's 287 documents, 100 sites restate an inherited property:
51 restate it identically, 31 state nothing but ``default`` and ``description``,
16 point a ``$ref`` at a fragment of the base's own node, and 2 add a keyword.
**The 31 are this step's highest-value defect** -- in the previous generated tree
they were 31 of 42 ``Any`` fields, each one shadowing a typed base field across 15
classes.  ``formats/canonical/responsive_creative.json`` is the control shape:
it restates ``experimental``, ``v1_translatable`` and ``slots`` with nothing but a
default and a description, while ``formats/canonical/_base.json`` types them
``boolean``, ``boolean`` and ``array``, so a restatement lowered on its own is
``Any | None`` shadowing a typed base field.  Inheriting instead makes the shadow
UNSPELLABLE rather than caught.

The same rule closes the inventory's "41 subclass fields optional where their base
requires them" by construction: a field the subclass does not declare keeps the
base's requiredness, because there is nothing of the subclass's to override it.  A
field it DOES narrow keeps it too -- the inherited required set is unioned in.
"""

from __future__ import annotations

from typing import Any

from codegen.compiler import (
    ANNOTATIONS,
    Module,
    Shape,
    check_keywords,
    declare_object,
    fields,
)
from codegen.refusal import Refusal

#: What a conjunct may carry and still be an inline object declaring fields.
#: ``additionalProperties`` is absent on purpose: D8 derives ``extra`` from the
#: ROOT's, and a conjunct carrying a second one would be a second source for one
#: class attribute.  There are 0 such conjuncts over the population, so this
#: refuses rather than choosing between them.
INLINE = frozenset({"type", "properties", "required"})

#: What the root itself may carry beside its conjunct list.
ROOT = frozenset({"type", "allOf", "properties", "required", "additionalProperties"})


def lower_root(doc: dict, name: str, pointer: str, mod: Module) -> str:
    """Append the class for an ``allOf`` node and return its name."""
    check_keywords(doc, pointer, set(ROOT))
    if doc.get("type") not in (None, "object"):
        raise Refusal("type", pointer, f"an allOf of type {doc['type']!r} composes no object")

    bases: list[str] = []
    inherited: dict[str, dict] = {}
    inherited_required: set[str] = set()
    #: Every LOCAL declaration that won its key, and where it was declared.  The
    #: root's own properties and an inline conjunct's land in the SAME map,
    #: because draft-07 applies both to the same instance.
    local: dict[str, dict] = {}
    at: dict[str, str] = {}
    required: set[str] = set(_required(doc, pointer))

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
            )

    for key, sub in (doc.get("properties") or {}).items():
        declare(key, sub, f"{pointer}/properties/{key}")

    for i, conjunct in enumerate(doc["allOf"]):
        where = f"{pointer}/allOf/{i}"
        if not isinstance(conjunct, dict):
            raise Refusal("allOf", where, "a conjunct that is not a schema")
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
                )
            mod.imports.add((target.module, target.symbol))
            bases.append(target.symbol)
            inherited.update(target.shape.properties)
            inherited_required |= target.shape.required
            continue
        if "properties" in keys and keys <= INLINE:
            check_keywords(conjunct, where, set(INLINE))
            if conjunct.get("type") not in (None, "object"):
                raise Refusal("type", where, f"a conjunct of type {conjunct['type']!r} is not one")
            if not isinstance(conjunct["properties"], dict) or not conjunct["properties"]:
                raise Refusal("properties", where, "a conjunct declaring no property")
            for key, sub in conjunct["properties"].items():
                declare(key, sub, f"{where}/properties/{key}")
            required |= set(_required(conjunct, where))
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
            )
        raise Refusal(
            min(keys) if keys else "allOf",
            where,
            "this step lowers a $ref conjunct (a base) or an inline conjunct with "
            "properties; a later D2 row lowers this one",
        )

    own: dict[str, dict] = {}
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
            )
        if verdict:
            own[key] = node  # it narrows, so the subclass is the one that states it
        # Otherwise it adds nothing and the field is INHERITED: no line, no shadow.

    decided = fields(
        own,
        required | (inherited_required & set(own)),
        pointer,
        name,
        mod,
        inherited=set(inherited),
        declared_at=at,
    )
    return declare_object(
        doc,
        name,
        pointer,
        mod,
        decided,
        Shape({**inherited, **own}, frozenset(required | inherited_required)),
        bases=tuple(bases),
    )


def _required(node: dict, pointer: str) -> list[str]:
    req = node.get("required", [])
    if not isinstance(req, list) or not all(isinstance(r, str) for r in req):
        raise Refusal("required", pointer, f"required is {req!r}, not a list of names")
    return req


def _constraining(node: dict) -> dict:
    """What a declaration says about the INSTANCE.

    ``default``, ``description`` and the rest of ``ANNOTATIONS`` annotate the node
    without constraining anything, so a declaration holding only those says
    nothing and cannot narrow.  That is precisely the shadow: the three
    ``responsive_creative.json`` restatements are a ``default`` plus a
    ``description`` and nothing else.
    """
    return {k: v for k, v in node.items() if k not in ANNOTATIONS and not k.startswith("x-")}


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
