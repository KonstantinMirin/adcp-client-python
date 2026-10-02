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
    """The qualified name binds the class its module defines, not the sort winner."""
    name_to_modules = _scan_name_to_modules()
    collisions = colliding_names(name_to_modules)
    assert collisions, "no colliding names in the tree — this test is vacuous"

    checked = 0
    for name in disambiguated.__all__:
        bound = getattr(disambiguated, name)
        if not inspect.isclass(bound):
            continue
        module = bound.__module__.removeprefix("adcp.types.generated_poc.")
        assert name.startswith(f"{bound.__name__}From"), name
        assert module in name_to_modules.get(bound.__name__, {module})
        checked += 1
    assert checked == len(disambiguated.__all__)


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
# The error-details family
# ---------------------------------------------------------------------------


def _error_details_models() -> dict[str, type]:
    """Every top-level model generated from an ``error-details/*.json`` schema."""
    package = importlib.import_module("adcp.types.generated_poc.error_details")
    models: dict[str, type] = {}
    for info in pkgutil.iter_modules(package.__path__):
        module = importlib.import_module(f"{package.__name__}.{info.name}")
        models.update(
            {
                name: obj
                for name, obj in vars(module).items()
                if inspect.isclass(obj)
                and obj.__module__ == module.__name__
                and name.endswith("Details")
            }
        )
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
