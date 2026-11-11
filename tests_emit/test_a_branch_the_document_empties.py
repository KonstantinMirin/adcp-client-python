"""A branch whose CONJUNCTION admits nothing: the class is emitted and refuses everything.

``core/creative-representation.json`` is an ``allOf`` of two members that contradict each
other on one of the two branches the member it references declares.  ``allOf/0`` is
``$ref: core/creative-manifest.json``, whose ``oneOf`` states exactly two branches --
``oneOf/0`` requires ``format_id`` and forbids ``format_kind``, ``oneOf/1`` the reverse.
``allOf/1`` then says, unconditionally, ``required: ["format_kind"]`` and
``not: {anyOf: [{required: ["format_id"]}, ...]}``.  Conjoined with ``oneOf/0`` that is a
contradiction on BOTH keys at once, so no instance can satisfy the named-format branch of a
Creative Representation: ``allOf/1`` has decided the ``oneOf`` before it is reached.

**THE COMPILER TRANSCRIBES AND DOES NOT DECIDE SATISFIABILITY** (§5 of the architecture
document).  ``CreativeRepresentationFormatId`` is emitted, carries the pointer
``#/allOf/0/oneOf/0``, inherits the forbidding rule from the document's root and the
requiring field from the referenced manifest, and refuses every payload offered to it --
which is the document's own answer reached by the document's own rules.  Declining to emit
it would require proving no instance satisfies it, which is satisfiability over
``required``, ``not``, ``oneOf``, ``if``/``then`` and every ``$ref`` they reach; wrong in
the admitting direction such a proof costs a dead name, wrong in the refusing direction it
removes a class a payload needs and the only evidence is an ``ImportError`` in an adopter's
code.  So the asymmetry decides it and nothing here asserts a suppression.

**THE CLAIM IS ABOUT AN ACCEPTED SET, so every test states it with ``jsonschema`` first and
asks the class to agree** -- the sibling discipline of
``test_a_property_that_admits_nothing.py``, and for the same reason: no reading of the
rendering can tell a faithful empty branch from a defect that refuses too much.  The
control is :func:`test_the_sibling_branch_is_live_for_both`, which requires the canonical
branch to be ADMITTED by both readings, so a class that refused for an unrelated reason --
a missing required pair on an enclosed node, an over-eager rule -- cannot make this file
pass.

Whether the narrowing is intended is the BUNDLE's question and is asked there:
upstream ``adcontextprotocol/adcp#8922``.  The grade is unmoved by the answer, because a
class that refuses everything refuses faithfully.
"""

from __future__ import annotations

import importlib
import json
import pkgutil
import sys
from typing import Any

import fresh
import jsonschema
import pydantic
import pytest
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT7

#: The bundle a run reads, taken from the one declaration of it.
SOURCE = fresh.BUNDLE

#: Every branch of the bundle the document empties: the document, the pointer of the
#: emitted class, and the keys that are REQUIRED on it and FORBIDDEN on it at once.
#:
#: Pinned as a set of SITES and not as a count, because these are positions of the bundle
#: SOURCE and do not move when a row lands.
#: :func:`test_the_bundle_population_is_the_one_this_row_claims` is the derivation that this
#: set is the whole of it.
SITES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("core/creative-representation.json", "#/allOf/0/oneOf/0", ("format_id",)),
)

#: A payload the REFERENCED manifest admits at its own ``oneOf/0`` -- it carries
#: ``format_id`` and not ``format_kind`` -- and which the conjoining document therefore
#: refuses.  ``source``'s own required pair is satisfied, so a refusal here is never about
#: an enclosed node failing to be constructible.
NAMED = {
    "representation_id": "r1",
    "source": {"system": "x", "source_representation": "y"},
    "assets": {},
    "format_id": {"agent_url": "https://a.example.com", "id": "display_300x250"},
}

#: The same payload on the branch the conjunction leaves live.  The control.
CANONICAL = {
    "representation_id": "r1",
    "source": {"system": "x", "source_representation": "y"},
    "assets": {},
    "format_kind": "image",
}

#: The values offered for the forbidden-and-required key.  Every one is refused -- that is
#: what an empty branch means -- and the tests say so over several JSON types rather than
#: trusting one.
VALUES: tuple[Any, ...] = (
    {"agent_url": "https://a.example.com", "id": "display_300x250"},
    {"id": "display_300x250"},
    "display_300x250",
    None,
    7,
    [],
)

_PREFIX = "https://adcontextprotocol.org/schemas/"


def _judge(document: str) -> jsonschema.Draft7Validator:
    """A validator over the RAW document, resolving ``$ref`` from the same bundle.

    The remote prefix carries the bundle's own version and this reads through it rather
    than pinning one, so a bundle bump does not quietly turn every ``$ref`` into an
    unresolvable reference that the validator reports as a pass.
    """

    def retrieve(uri: str) -> Resource:
        if not uri.startswith(_PREFIX):
            raise LookupError(uri)
        relative = uri.removeprefix(_PREFIX).split("/", 1)[1]
        contents = json.loads((SOURCE / relative).read_text())
        return Resource.from_contents(contents, default_specification=DRAFT7)

    contents = json.loads((SOURCE / document).read_text())
    return jsonschema.Draft7Validator(contents, registry=Registry(retrieve=retrieve))


def _module_of(document: str) -> Any:
    name = "adcp.types._schemas." + document.removesuffix(".json").replace("-", "_").replace(
        "/", "."
    )
    __import__(name)
    return sys.modules[name]


def _class_at(document: str, pointer: str) -> type[pydantic.BaseModel]:
    """The emitted class whose ``__adcp_schema__`` names this node.

    Found by the schema reference the class carries and never by name, because the NAME is
    a derivation this row is not about: a renaming there must not be able to make this gate
    pass by failing to find anything.
    """
    module = _module_of(document)
    found = [
        value
        for value in vars(module).values()
        if isinstance(value, type)
        and issubclass(value, pydantic.BaseModel)
        and getattr(value, "__adcp_schema__", None) is not None
        and value.__adcp_schema__.document == document
        and value.__adcp_schema__.pointer == pointer
    ]
    assert len(found) == 1, f"{document}{pointer}: {[c.__name__ for c in found]}"
    return found[0]


def _forbidden_singles(cls: type[pydantic.BaseModel]) -> set[str]:
    """Every key a single-key ``ForbiddenGroups`` group forbids, read over the MRO.

    Over the MRO and not off ``cls._adcp_rules``, because the conjunction this row is about
    is spelled as inheritance: the forbidding rule is the document root's and the requiring
    field is the referenced manifest branch's, and only the child holds both.
    """
    keys: set[str] = set()
    for ancestor in cls.__mro__:
        for rule in ancestor.__dict__.get("_adcp_rules", ()):
            if type(rule).__name__ == "ForbiddenGroups":
                keys |= {group[0] for group in rule.groups if len(group) == 1}
    return keys


def _emptied() -> list[tuple[str, str, tuple[str, ...]]]:
    """Every emitted class with a key both required and forbidden on it.

    This is the one family of emptiness that is decidable by READING rather than by solving,
    which is why it is the one this file ranges over: a key in ``required`` and in a
    single-key forbidden group admits nothing whether it is present or absent, and no
    search over the other keywords is needed to say so.
    """
    import adcp.types._schemas as schemas

    out = []
    for found in pkgutil.walk_packages(schemas.__path__, schemas.__name__ + "."):
        try:
            module = importlib.import_module(found.name)
        except Exception:  # noqa: BLE001 -- an unimportable module is another row's gate
            continue
        for value in vars(module).values():
            if not (
                isinstance(value, type)
                and issubclass(value, pydantic.BaseModel)
                and value.__module__ == found.name
            ):
                continue
            ref = getattr(value, "__adcp_schema__", None)
            if ref is None:
                continue
            required = {k for k, f in value.model_fields.items() if f.is_required()}
            clash = tuple(sorted(required & _forbidden_singles(value)))
            if clash:
                out.append((ref.document, ref.pointer, clash))
    return sorted(out)


def test_the_bundle_population_is_the_one_this_row_claims() -> None:
    """:data:`SITES` is the WHOLE of it, derived rather than assumed."""
    assert _emptied() == sorted(SITES)


@pytest.mark.parametrize(("document", "pointer", "keys"), SITES)
def test_the_class_is_emitted_and_carries_its_pointer(
    document: str, pointer: str, keys: tuple[str, ...]
) -> None:
    """Nothing is suppressed: the branch has a class and the class names its node."""
    cls = _class_at(document, pointer)
    required = {name for name, f in cls.model_fields.items() if f.is_required()}
    assert set(keys) <= required
    assert set(keys) <= _forbidden_singles(cls)


@pytest.mark.parametrize("value", VALUES)
def test_the_document_refuses_the_named_branch_whatever_the_key_holds(
    value: Any,
) -> None:
    """The DOCUMENT's reading first: the conjunction admits nothing with the key present."""
    judge = _judge("core/creative-representation.json")
    errors = list(judge.iter_errors({**NAMED, "format_id": value}))
    assert errors, value
    assert {"not", "oneOf"} & {error.validator for error in errors}, [
        error.validator for error in errors
    ]


def test_the_document_refuses_the_named_branch_with_the_key_absent_too() -> None:
    """And with it absent, by the referenced ``oneOf`` -- which is what EMPTY means."""
    judge = _judge("core/creative-representation.json")
    without = {k: v for k, v in NAMED.items() if k != "format_id"}
    assert not judge.is_valid(without)


@pytest.mark.parametrize("value", VALUES)
def test_the_class_agrees_and_admits_nothing(value: Any) -> None:
    """The class's reading second, and it must be the same one."""
    cls = _class_at("core/creative-representation.json", "#/allOf/0/oneOf/0")
    with pytest.raises(pydantic.ValidationError):
        cls.model_validate({**NAMED, "format_id": value})


def test_the_union_refuses_the_named_payload_as_the_document_does() -> None:
    """Offered to the document's ROOT class, the same payload is refused the same way.

    The branch class is reached through dispatch in real use, so the agreement has to hold
    at the position an adopter actually constructs.
    """
    root = _class_at("core/creative-representation.json", "#")
    judge = _judge("core/creative-representation.json")
    assert not judge.is_valid(NAMED)
    with pytest.raises(pydantic.ValidationError):
        root.model_validate(NAMED)


def test_the_sibling_branch_is_live_for_both() -> None:
    """THE CONTROL: the canonical branch is ADMITTED by document and class alike.

    Without this every assertion above is satisfiable by a class that refuses everything
    for a reason that has nothing to do with the conjunction -- an enclosed node that
    cannot be constructed, a rule that fires on the wrong key.  The two payloads differ in
    exactly one key.
    """
    judge = _judge("core/creative-representation.json")
    assert judge.is_valid(CANONICAL), [error.message for error in judge.iter_errors(CANONICAL)]
    root = _class_at("core/creative-representation.json", "#")
    live = _class_at("core/creative-representation.json", "#/allOf/0/oneOf/1")
    assert isinstance(root.model_validate(CANONICAL), live)
