"""The flat surface upstream's own machinery asks of ``adcp.types``, from the modules
restored at upstream's own paths.

**THE DEMAND, measured.**  95 of upstream's own test files write
``from adcp.types import MEDIA_BUY_LEGACY_STATUS_VALUES``, and that constant is not a
schema subject: it is a ``frozenset`` of six lifecycle words that upstream's own docstring
explains by SUBTRACTION -- ``completed`` is excluded because it is also the 3.1
task-envelope success status -- so a set derived from the bundle's enumeration would have
been a different set and wrong.  The only thing that can serve it is the file that declares
it, and that file is restored at ``adcp.types.media_buy_status_helpers`` byte for byte.

**WHY THE FLAT SPELLING NEEDS A MODULE OF ITS OWN.**  Upstream serves it from their own
``_eager``, and that module is not restorable here: measured, it carries 16 imports of
their generated ``_generated`` aggregator plus ``_ergonomic``, ``_forward_compat``,
``projections``, ``aliases`` and ``guards``, and the aggregator stays deleted along with
the generator that wrote it.  So the flat surface has to reach the restored files directly,
and ``adcp.types.compat`` cannot do it --
that module is the ALIAS table, keyed on a document and the word the document gives, and
none of these names has a document.

**IT NAMES MODULES AND NEVER NAMES.**  :data:`MODULES` is the whole of what is written
down, and :func:`offered` derives the names from each module's own ``__all__`` or, where it
declares none -- four of the six do not -- from what the module itself DECLARED.  So a name
upstream adds to one of these files is reachable flat with nothing here edited, and a name
removed stops being reachable rather than becoming a stale alias.  ``tests_emit/
test_the_restored_flat_surface.py`` holds :data:`MODULES` against
``survey/upstream-machinery-9.6.1.tsv``'s own ``restored`` column -- which is BYTE IDENTITY
against upstream's commit and not "a file exists at the path" -- in both directions, so a
seventh restored module joins this surface by a run reporting it.

**CONSULTED LAST**, after ``compat`` and ``_adapter`` (``adcp.types.__getattr__``), so no
name either of those decides can be overridden here; and LAZILY, for the reason that
package's own docstring gives: nothing may import the generated tree while
``adcp/types/__init__.py``'s body runs.  Measured and not assumed -- none of the six
imports ``adcp.types`` at all, so consulting this module costs no generated import even
when it answers.
"""

from __future__ import annotations

import importlib
import types

#: The restored modules of ``adcp.types``, by MODULE.
#:
#: Upstream's own hand-written machinery, put back at upstream's own path byte for byte,
#: which is ``survey/upstream-machinery-9.6.1.tsv``'s ``restored`` verdict.  Nine today.
#: Written here because a shipped package cannot read a survey table, and held against
#: that table by the gate named in this module's docstring -- so the authority is byte
#: identity against upstream's commit and this tuple is the derivation's cached answer
#: rather than its source.
#:
#: ``base`` and its leaf ``_geo_place_keys`` joined on `adcp-client-python-1zmw`, and what
#: they add to the flat surface is the one thing worth reading twice: ``AdCPBaseModel`` is
#: unbound on ``adcp.types`` today and binds here now, to UPSTREAM's class -- which under
#: that ruling is the class ``adcp.types._base``'s own derives from, so the flat spelling,
#: upstream's module path and every emitted model are one lineage and ``isinstance`` holds
#: against any of the three.  The 10 names only upstream's ``base.py`` declares arrive with
#: it (``defer_model_rebuild``, ``inherit_field``, ``NoExplicitNull``, ``WireUrl`` and the
#: rest); nothing else in ``src/adcp/`` declares any of them.
#:
#: ``_product_format_declaration`` joined beside them as ``canonical_creative``'s last
#: MECHANICAL blocker (`adcp-client-python-rqjo`): 102 lines, no ``adcp.types`` import at
#: all, and its one import of ours -- ``adcp.validation.schema_loader.get_named_validator``
#: -- resolves here already.  It brings ``PRODUCT_FORMAT_DECLARATION_SCHEMA`` and
#: ``check_declaration_rules``, which an adapter could never have served because one is a
#: hand-written function and the other is a document path a re-export has no name for.
MODULES = (
    "_geo_place_keys",
    "_legacy_assets",
    "_product_format_declaration",
    "_scalar",
    "_str_enum",
    "_wire",
    "base",
    "error_narrowing",
    "media_buy_status_helpers",
)


def offered(module: types.ModuleType) -> dict[str, object]:
    """What ``module`` offers the flat surface: its ``__all__``, or what it DECLARED.

    ``__all__`` first, because a module that declares one has said what it offers and the
    answer is not this function's to improve -- ``_wire`` and ``error_narrowing`` are the
    two of the six that do.

    Otherwise the names a reader would call the module's own, and the discriminator is the
    one Python answers rather than one a list would: a class or a function carries the
    ``__module__`` of the body that created it, so ``typing.Any``,
    ``collections.abc.Mapping`` and ``pydantic.RootModel`` imported into a restored file
    are excluded without being named, and a name with no ``__module__`` at all is the
    module's own DATA -- which is exactly what ``MEDIA_BUY_LEGACY_STATUS_VALUES`` is, a
    ``frozenset`` instance, and what a rule written over ``__module__`` alone would have
    dropped.  A submodule bound by an ``import`` is excluded as a module.
    """
    advertised = getattr(module, "__all__", None)
    if advertised is not None:
        return {name: getattr(module, name) for name in advertised if hasattr(module, name)}
    out: dict[str, object] = {}
    for name, value in vars(module).items():
        if name.startswith("_") or isinstance(value, types.ModuleType):
            continue
        home = getattr(value, "__module__", None)
        if home is None or home == module.__name__:
            out[name] = value
    return out


def _surface() -> dict[str, object]:
    """Every name the restored modules offer, in :data:`MODULES` order.

    Earlier modules win, which is :data:`MODULES`' own order and is a decision only in
    the sense that a collision has to resolve somehow: measured over the six, there is
    none, and ``tests_emit/test_the_restored_flat_surface.py`` asserts that rather than
    leaving the order to carry the weight.
    """
    found: dict[str, object] = {}
    for module in MODULES:
        for name, value in offered(importlib.import_module(f"{__package__}.{module}")).items():
            found.setdefault(name, value)
    return found


def __getattr__(name: str) -> object:
    """A restored module's own name, or ``AttributeError``.

    ``__all__`` is answered here too, through PEP 562, so the set is derived at the moment
    it is asked for and this module holds no second copy of it.
    """
    if name == "__all__":
        return sorted(_surface())
    if name.startswith("__"):
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    try:
        return _surface()[name]
    except KeyError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None


def __dir__() -> list[str]:
    return sorted(_surface())
