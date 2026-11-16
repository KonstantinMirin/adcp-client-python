"""A ``Legacy*`` name is the compiled class, and there is one per response branch.

Two defects, one cause: the ``Legacy*`` set was curated by hand, so what it
named drifted from what the tree declares.

#1398 — ``adcp.types.LegacyFormatId`` was a SUBCLASS of the compiled
``FormatReferenceStructuredObject``, and no public name on ``adcp.types``
resolved to the compiled class at all. The subclass redeclared four fields and
every redeclaration had become a weakening of the parent it was written to
narrow: ``width: 300.0`` validated against the class the SDK's own model fields
declare and was refused by the public name for it. A public name more permissive
(or less) than the library's own contract fails late and for no visible reason.

#1399 — ``LegacyUpdateMediaBuy{Success,Error}Response`` shipped while
``LegacyUpdateMediaBuySubmittedResponse`` and all three
``LegacyCreateMediaBuy*Response`` branches did not, so four response branches
could only be named through a module path. Adding four names would have fixed
four instances: the generator had ALREADY opened a fifth, by adding a fourth
``preview_creative`` branch that nobody named.

So neither test reads a list. Both derive what the surface must carry from the
compiled tree:

* a response union is emitted as a BASE plus one SUBCLASS per branch
  (rebuild-plan §4 "A union root: the base, the branches, and how a payload
  reaches its branch"), each branch carrying the ``__adcp_schema__`` pointer of
  the ``oneOf`` entry it compiles — so the branches are read off the class
  graph of the declaring module, not from a name pattern and not from
  ``__module__``, which names the canonical spec even for a duplicate and so
  cannot tell a copy from the original;
* a response is "on the ``Legacy*`` surface" when its tool has any ``Legacy*``
  name at all, which is what an adopter migrating through those names has;
* and the obligation is stated as object identity against ``adcp.types``, which
  is the only thing an adopter's ``isinstance`` cares about.

**WHERE A CLASS IS DECLARED.** ``adcp.types._schemas.<domain>.<document>`` is
where the compiler writes, and ``adcp.types.domains.<domain>.<document>`` is a
second NAME for that one module rather than a second module. The checks below
are written against the declaring tree, because that is the name ``__module__``
reports and the round trip asks the module for its own attribute back.
"""

from __future__ import annotations

import importlib
import pathlib
import typing

import pytest
from pydantic import BaseModel

import adcp.types as types

_DECLARED_ROOT = "adcp.types._schemas"
_SCHEMAS_DIR = pathlib.Path(importlib.import_module(_DECLARED_ROOT).__file__).parent

LEGACY_NAMES = sorted(name for name in types.__all__ if name.startswith("Legacy"))
PLAIN_NAMES = sorted(name for name in types.__all__ if not name.startswith("Legacy"))

#: The ``Legacy*`` names bound to a model class. The rest are union aliases
#: (``LegacyBuildCreativeResponse``, ``LegacyProductFormatDeclaration``, ...),
#: which have no field set to weaken — filtered out rather than skipped, so a
#: class that stops being one is a parametrization change and not a quiet skip.
LEGACY_CLASSES = sorted(
    name
    for name in LEGACY_NAMES
    if isinstance(getattr(types, name, None), type) and issubclass(getattr(types, name), BaseModel)
)


def _camel(stem: str) -> str:
    return "".join(part.title() for part in stem.split("_"))


def _response_branches() -> list[tuple[str, str, type[BaseModel]]]:
    """Every branch of every response union whose tool is on the ``Legacy*`` surface.

    ``(tool, branch name, branch class)``. The branches come from the declaring
    module's own ``<Tool>Response`` base and the subclasses that module itself
    declares, so a document that gains or loses a ``oneOf`` entry changes this
    list with no edit here. A response that is one class rather than a union
    contributes that class as its only branch.
    """

    branches: list[tuple[str, str, type[BaseModel]]] = []
    for path in sorted(_SCHEMAS_DIR.rglob("*_response.py")):
        relative = path.relative_to(_SCHEMAS_DIR)
        tool = _camel(relative.stem.removesuffix("_response"))
        if not any(name.startswith(f"Legacy{tool}") for name in LEGACY_NAMES):
            continue
        module = importlib.import_module(
            ".".join([_DECLARED_ROOT, *relative.parts[:-1], relative.stem])
        )
        base = getattr(module, f"{tool}Response", None)
        if not (isinstance(base, type) and issubclass(base, BaseModel)):
            continue
        members = [
            child for child in base.__subclasses__() if child.__module__ == module.__name__
        ] or [base]
        branches.extend((tool, member.__name__, member) for member in members)
    return branches


BRANCHES = _response_branches()
BRANCH_IDS = [f"{tool}:{name}" for tool, name, _ in BRANCHES]


def test_the_derived_sets_are_not_empty() -> None:
    """Neither obligation below may go quiet when the tree is reorganized.

    A derivation that silently resolves to nothing is worse than a hand-written
    list, because a list at least fails loudly when it stops matching.
    """
    assert len(LEGACY_NAMES) > 40, LEGACY_NAMES
    assert len(LEGACY_CLASSES) > 35, LEGACY_CLASSES
    assert len(BRANCHES) > 12, BRANCH_IDS
    assert {tool for tool, _, _ in BRANCHES} >= {
        "BuildCreative",
        "CreateMediaBuy",
        "PreviewCreative",
        "UpdateMediaBuy",
    }, sorted({tool for tool, _, _ in BRANCHES})


def test_each_branch_states_the_oneof_entry_it_compiles() -> None:
    """What makes the derivation above a reading of the documents.

    A subclass of the response base is a branch because its ``__adcp_schema__``
    points at an entry of the document's own union, and the base points at the
    document root. Without this the set would be "whatever subclasses the
    module happens to declare", which is a name pattern wearing a class graph.
    """
    unpointed = [
        f"{tool}:{name}"
        for tool, name, branch in BRANCHES
        if "/oneOf/" not in typing.cast("str", branch.__adcp_schema__.pointer)
        and branch.__name__ != f"{tool}Response"
    ]
    assert unpointed == [], unpointed


# ---------------------------------------------------------------------------
# #1398 — a Legacy name is the compiled class, never a shim over it
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", LEGACY_CLASSES)
def test_a_legacy_name_is_the_compiled_class_not_a_subclass_of_it(name: str) -> None:
    """``Legacy<X>`` means "the class the compiler emitted", with nothing in between.

    The load-bearing assertion is the ROUND TRIP: the class must be the
    attribute the module it claims actually binds under its own qualname.
    Neither half of it is sufficient alone, and a fire probe proved it —

    * ``__module__.startswith(_DECLARED_ROOT)`` alone is defeated by one line
      (``Clone.__module__ = "adcp.types._schemas.core.format_id"``), and
      ``__module__`` is a weak witness by construction here: ``module_from_spec``
      stamps the canonical spec's name onto a duplicate too, so it cannot tell a
      copy from the original;
    * the MRO check alone misses the shape this repo actually shipped. #1398's
      clone was ``class LegacyFormatId(FormatReferenceStructuredObject)`` — a
      different class NAME, so a "shadows a same-named base" rule reports
      nothing. That rule is kept below for the subclass that does reuse the
      name, but it is not what catches a renamed shim.

    Together they do: a shim declared anywhere but the compiled tree fails the
    first, and a shim that lies about where it was declared fails the second,
    because the module it names binds no such attribute.

    A ``Legacy*`` name bound to a union alias rather than a class is out of the
    parametrization: there is no field set to weaken.
    """
    value = getattr(types, name)

    assert value.__module__.startswith(_DECLARED_ROOT), (
        f"adcp.types.{name} is {value.__module__}.{value.__qualname__}, declared "
        f"outside the compiled tree. A Legacy name is the compiled class "
        f"itself, so a class in between reshapes the contract the SDK's own "
        f"model fields carry (#1398)"
    )
    declaring = importlib.import_module(value.__module__)
    assert getattr(declaring, value.__qualname__, None) is value, (
        f"adcp.types.{name} reports {value.__module__} but that module binds no "
        f"{value.__qualname__} — it is a local class claiming a compiled address"
    )

    shadowed = [
        base
        for base in value.__mro__[1:]
        if isinstance(base, type)
        and issubclass(base, BaseModel)
        and base.__name__ == value.__name__
    ]
    assert shadowed == [], f"adcp.types.{name} shadows the same-named {shadowed[0]!r}"


def test_the_format_reference_is_reachable_under_a_public_name() -> None:
    """#1398's first half, on the one class it was measured on.

    ``[n for n in adcp.types.__all__ if getattr(adcp.types, n) is
    FormatReferenceStructuredObject]`` was empty: model fields are annotated
    with this class and nothing on the flat surface named it.

    Stated as membership rather than as the whole list, because the compiler
    binds the document's own words too — ``core/format-id.json`` is titled
    "Format Reference (Structured Object)" and the position it is referenced
    from gives ``FormatId`` — and a name a document states is not a drift to be
    pinned out. What #1398 needs is that the ``Legacy*`` spellings an adopter
    migrates through reach the compiled class, which is what is asserted.
    """
    declared = importlib.import_module(f"{_DECLARED_ROOT}.core.format_id")
    reference = declared.FormatReferenceStructuredObject

    public = [name for name in types.__all__ if getattr(types, name, None) is reference]
    assert {"LegacyFormatId", "LegacyFormatReferenceStructuredObject"} <= set(public), public


def test_the_format_reference_accepts_what_the_sdk_s_own_model_fields_accept() -> None:
    """The measured consequence of the dropped validators, stated as behaviour.

    ``width``/``height`` are ``SchemaInt`` on the compiled class, which carries
    a ``BeforeValidator`` for the JSON-schema spelling of an integer. The
    subclass declared ``StrictInt`` and refused ``300.0`` — a payload every
    model that declares the real type accepts.
    """
    wire = {"agent_url": "https://creative.adcontextprotocol.org", "id": "display_300x250"}

    reference = types.LegacyFormatId.model_validate({**wire, "width": 300.0, "height": 250.0})
    assert (reference.width, reference.height) == (300, 250)

    assert reference.model_json_schema()["properties"]["agent_url"]["format"] == "uri"


# ---------------------------------------------------------------------------
# #1399 — one Legacy name per branch, derived from the compiled unions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("tool", "branch_name", "branch"), BRANCHES, ids=BRANCH_IDS)
def test_every_branch_of_a_response_on_the_legacy_surface_is_publicly_nameable(
    tool: str, branch_name: str, branch: type[BaseModel]
) -> None:
    """The branch itself, not only a base or an alias that covers it.

    A seller reading a response off the wire holds an instance of the BRANCH
    the payload selected, so an ``isinstance`` against anything narrower is
    False for that instance and the only public spelling for the thing in hand
    was a module path. Every branch of a response whose tool is on the
    ``Legacy*`` surface needs a name on the flat surface — its own, or a
    ``Legacy*`` one.
    """
    direct = [name for name in PLAIN_NAMES if getattr(types, name, None) is branch]
    through_legacy = [name for name in LEGACY_NAMES if getattr(types, name, None) is branch]

    assert direct or through_legacy, (
        f"{branch.__module__}.{branch_name} is a branch of {tool}Response and no "
        f"public name on adcp.types resolves to it, so it can only be named "
        f"through a module path. Bind Legacy{tool}<Branch>Response in "
        f"src/adcp/types/legacy.py (#1399)"
    )
