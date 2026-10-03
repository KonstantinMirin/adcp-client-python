"""The public type surface resolves, and no generated class is unreachable.

Three properties, each one a defect this suite caught in a shipped wheel:

* every name in ``adcp.types.__all__`` resolves, and no public binding in
  ``_generated`` reassigns a name the module imports — that reassignment needs
  ``# type: ignore[assignment]``, which left mypy holding the pre-reassignment
  declaration while the runtime held its neighbour (#1141). The static half of
  that contract is ``tests/type_checks/authorized_agents_variants.py``;
* every public class in a non-bundled generated module is importable, from
  ``adcp.types`` when its bare name is unambiguous and from
  ``adcp.types.disambiguated`` when it is not (#911);
* ``adcp.types.error_details`` carries each ``error-details/*.json`` model
  together with the field types its annotations reference, so a seller
  constructs the payload with typed values (#1080).
"""

from __future__ import annotations

import ast
import importlib
import inspect
import pkgutil
import typing
from pathlib import Path

import pytest

import adcp.types
import adcp.types._generated as generated
import adcp.types.disambiguated as disambiguated
import adcp.types.error_details as error_details
from scripts.consolidate_exports import (
    _scan_name_to_modules,
    colliding_names,
    disambiguated_bindings,
    extract_exports_from_module,
    generate_consolidated_exports,
    qualified_public_name,
)

# ---------------------------------------------------------------------------
# Every exported name resolves, and means one thing
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "module",
    [adcp.types, generated, disambiguated, error_details],
    ids=["types", "_generated", "disambiguated", "error_details"],
)
def test_every_name_in_all_resolves(module: object) -> None:
    """``__all__`` is a promise: a name listed there must be importable."""
    unresolved = [name for name in module.__all__ if not hasattr(module, name)]  # type: ignore[attr-defined]
    assert unresolved == []


def test_generated_module_rebinds_no_imported_name() -> None:
    """A public binding in ``_generated`` is a first binding, never a reassignment."""
    tree = ast.parse(Path(generated.__file__).read_text())
    imported = {
        alias.asname or alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    rebound = sorted(
        target.id
        for node in tree.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name) and target.id in imported
    )
    assert rebound == [], (
        "these names are imported and then reassigned, so mypy keeps the "
        "pre-reassignment type while the runtime holds the new object"
    )


# ---------------------------------------------------------------------------
# Every generated class is reachable
# ---------------------------------------------------------------------------


def test_no_generated_type_is_reachable_under_zero_names() -> None:
    """A model an adopter cannot import is a model an adopter cannot construct.

    A generated public name reaches an adopter under its bare spelling when the
    bare name resolves to the class that module defines, and under
    ``<Type>From<DottedModulePath>`` otherwise. The bare name alone is not
    enough: it covers one of the modules that define the name, and the whole
    defect is that the others silently lose it.
    """
    name_to_modules = _scan_name_to_modules()
    qualified = set(disambiguated.__all__) | set(error_details.__all__)

    def bare_resolves_here(type_name: str, module: str) -> bool:
        for surface in (adcp.types, generated):
            if type_name not in surface.__all__:  # type: ignore[attr-defined]
                continue
            bound = getattr(surface, type_name)
            if not inspect.isclass(bound):
                # A union / TypeAlias export carries no defining module.
                return True
            if bound.__module__.removeprefix("adcp.types.generated_poc.") == module:
                return True
        return False

    unreachable = sorted(
        f"{module}.{type_name}"
        for type_name, modules in name_to_modules.items()
        for module in modules
        if qualified_public_name(type_name, module) not in qualified
        and not bare_resolves_here(type_name, module)
    )
    assert unreachable == []


def test_every_colliding_variant_is_reachable_by_its_own_name() -> None:
    """Each qualified name binds the object its own module holds, and nothing is missing.

    Checked in the forward direction — from the tree to the export — because the
    name cannot be decomposed back into a module path, and because not every
    export is a class. A schema whose root composes other schemas generates a
    ``typing.Annotated[...]`` alias, which has no ``__module__`` and no
    ``__name__`` to compare; skipping those would quietly stop grading them.
    """
    name_to_modules = _scan_name_to_modules()
    collisions = colliding_names(name_to_modules)
    assert collisions, "no colliding names in the tree — this test is vacuous"

    expected = disambiguated_bindings(name_to_modules, generate_consolidated_exports().displaced)
    assert set(disambiguated.__all__) == set(expected), (
        "every variant of a shared name, and every class a compatibility alias "
        "displaces, is exported under its qualified name — no more and no fewer"
    )

    for qualified, (module_name, type_name) in sorted(expected.items()):
        source = importlib.import_module(f"adcp.types.generated_poc.{module_name}")
        assert getattr(disambiguated, qualified) is getattr(source, type_name), qualified


def test_the_bare_name_and_the_field_type_can_differ() -> None:
    """The defect the qualified names answer, pinned as the behaviour it is.

    ``ListCreativesResponse.query_summary`` is typed with the ``QuerySummary``
    that ``creative/list-creatives-response.json`` generates, which requires
    ``total_matching`` and ``returned``. The bare ``adcp.types`` name resolves to
    a different class, and that one accepts ``{}``.
    """
    from adcp.types.disambiguated import QuerySummaryFromCreativeListCreativesResponse
    from adcp.types.generated_poc.creative.list_creatives_response import ListCreativesResponse

    field_type = ListCreativesResponse.model_fields["query_summary"].annotation
    assert QuerySummaryFromCreativeListCreativesResponse in typing.get_args(field_type) or (
        field_type is QuerySummaryFromCreativeListCreativesResponse
    )
    assert sorted(
        name
        for name, field in QuerySummaryFromCreativeListCreativesResponse.model_fields.items()
        if field.is_required()
    ) == ["returned", "total_matching"]


# ---------------------------------------------------------------------------
# The generated modules re-export, they never rebuild
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "module",
    [generated, disambiguated, error_details],
    ids=["_generated", "disambiguated", "error_details"],
)
def test_generated_modules_define_and_build_no_class(module: object) -> None:
    """A derived export module binds the generated class, never a copy of it.

    Rebuilding a model with ``create_model`` and a copy of its ``model_fields``
    carries the fields and drops everything else attached to the class — model
    validators, field validators, custom methods. A copy like that validates
    documents the class it stands in for rejects, with no symptom until the data
    is wrong, so disambiguating a name by cloning is not an option here.
    """
    tree = ast.parse(Path(module.__file__).read_text())  # type: ignore[attr-defined]
    assert [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)] == []
    constructors = sorted(
        {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in {"create_model", "type", "ModelMetaclass", "new_class"}
        }
    )
    assert constructors == []


def test_every_exported_class_is_the_class_its_module_defines() -> None:
    """Identity, not shape: the exported name IS the generated class object.

    ``__module__`` must point into ``generated_poc`` and the class must be the
    object that module holds under its own name. Both halves matter:
    ``create_model`` stamps the calling module onto the class it builds, so a
    copy would satisfy an identity check that trusted ``__module__``.
    """
    checked = 0
    for module in (disambiguated, error_details):
        for name in module.__all__:  # type: ignore[attr-defined]
            bound = getattr(module, name)
            if not inspect.isclass(bound):
                continue
            assert bound.__module__.startswith("adcp.types.generated_poc."), (
                f"{name} resolves to {bound.__module__}.{bound.__name__}, which codegen "
                "did not define — a derived export re-exports, it does not rebuild"
            )
            source = importlib.import_module(bound.__module__)
            assert getattr(source, bound.__name__) is bound, name
            checked += 1
    assert checked > 1000, f"only {checked} classes checked — the surface shrank"


# ---------------------------------------------------------------------------
# The error-details family
# ---------------------------------------------------------------------------


def _error_details_models() -> dict[str, object]:
    """Every public top-level ``*Details`` name an ``error-details/*`` module declares.

    Read from the AST rather than filtered on ``inspect.isclass``: a composing
    root generates a ``typing.Annotated[...]`` alias, and an alias is a model an
    adopter imports like any other. The ``isclass`` filter dropped two of them
    the moment codegen started emitting that shape.
    """
    package = importlib.import_module("adcp.types.generated_poc.error_details")
    package_dir = Path(package.__path__[0])
    models: dict[str, object] = {}
    for info in pkgutil.iter_modules(package.__path__):
        module = importlib.import_module(f"{package.__name__}.{info.name}")
        for name in extract_exports_from_module(package_dir / f"{info.name}.py"):
            if name.endswith("Details") and hasattr(module, name):
                models[name] = getattr(module, name)
    return models


def test_every_error_details_model_is_exported() -> None:
    """Derived from the schema file list, so a new schema arrives exported."""
    models = _error_details_models()
    assert len(models) >= 24, "the error-details family shrank unexpectedly"
    missing = sorted(name for name in models if not hasattr(error_details, name))
    assert missing == []
    for name, cls in models.items():
        assert getattr(error_details, name) is cls


def test_every_error_details_field_type_is_exported() -> None:
    """Exporting a model without its field types leaves it unconstructable."""
    unreachable: list[str] = []
    exported = {
        obj
        for name in error_details.__all__
        if inspect.isclass(obj := getattr(error_details, name))
    }
    for model_name, model in _error_details_models().items():
        for field_name, field in model.model_fields.items():
            pending = [field.annotation]
            while pending:
                annotation = pending.pop()
                pending.extend(typing.get_args(annotation))
                if (
                    inspect.isclass(annotation)
                    and annotation.__module__.startswith("adcp.types.generated_poc.")
                    and annotation not in exported
                ):
                    unreachable.append(f"{model_name}.{field_name}: {annotation.__name__}")
    assert sorted(set(unreachable)) == []


def test_error_details_payload_constructs_with_typed_values() -> None:
    """The point of exporting the family: no dict at the raise site."""
    details = error_details.VersionUnsupportedDetails(
        adcp_version="3.2",
        supported_versions=[
            error_details.SupportedVersion("3.1"),
            error_details.SupportedVersion("3.2"),
        ],
        supported_majors=[error_details.SupportedMajor(3)],
    )
    assert details.model_dump(exclude_none=True) == {
        "adcp_version": "3.2",
        "supported_versions": ["3.1", "3.2"],
        "supported_majors": [3],
    }
    with pytest.raises(ValueError):
        error_details.VersionUnsupportedDetails(adcp_version="3.2")  # type: ignore[call-arg]
