"""Tests for the consolidate-step reachability guards (issues #911, #1080).

`consolidate_exports.py` flattens every `generated_poc/` module into a single
namespace. When the same bare type name is defined in more than one module, one
class wins that name in `_generated` and the others would be unreachable, so a
module per schema domain re-exports what that domain declares and
`error_details.py` carries the error-details family with the field types its
models reference.

Both export sets are derived from the module tree. These tests assert the
derivation covers every generated class, that no two classes claim one public
name inside a domain, and that the guard raises when a class would be left
unreachable.
"""

from __future__ import annotations

import pytest

from scripts.consolidate_exports import (
    _enforce_every_class_is_reachable,
    _scan_name_to_modules,
    colliding_names,
    domain_bindings,
    exports_for_public_consolidation,
    extract_exports_from_module,
    qualified_public_name,
    schema_domain,
)


def test_a_domain_module_cannot_split_a_name_its_own_domain_declares_twice():
    """The measurement that chose the scheme: a domain path is not always enough."""
    name_to_modules = _scan_name_to_modules()
    collisions = colliding_names(name_to_modules)
    assert collisions, "the generated tree has no colliding names — guard is vacuous"

    solvable, unsolvable = 0, 0
    for mods in collisions.values():
        per_domain = [schema_domain(m) for m in mods]
        if len(set(per_domain)) == len(per_domain):
            solvable += 1
        else:
            unsolvable += 1
    # A domain module alone handles the names no single domain declares twice.
    # The rest need the defining file in the name, which is what
    # ``qualified_public_name`` adds.
    assert solvable > 0 and unsolvable > 0, (solvable, unsolvable)
    assert solvable + unsolvable == len(collisions)


def test_qualified_name_suffixes_the_stem_and_is_unique_in_its_domain():
    """The suffix only has to disambiguate within one domain, so the stem suffices."""
    assert (
        qualified_public_name("Creative", "creative.list_creatives_response")
        == "CreativeFromListCreativesResponse"
    )
    # Two domains may share a stem; the domain module keeps them apart.
    assert qualified_public_name("X", "core.audience_source") == qualified_public_name(
        "X", "enums.audience_source"
    )

    bindings = domain_bindings(_scan_name_to_modules())
    for domain, rows in bindings.items():
        assert len(rows) == len(set(rows)), domain


def test_every_declared_pair_has_exactly_one_domain_binding():
    """One public name per (module, type) pair, for every name in the tree."""
    name_to_modules = _scan_name_to_modules()
    bindings = domain_bindings(name_to_modules)

    expected = {
        (module, type_name) for type_name, modules in name_to_modules.items() for module in modules
    }
    bound = [pair for rows in bindings.values() for pair in rows.values()]
    assert sorted(bound) == sorted(expected)
    assert len(bound) == len(set(bound)), "a pair was bound twice"


def test_names_a_domain_declares_once_keep_the_name_codegen_gave_them():
    """No invented name where the domain path already disambiguates."""
    name_to_modules = _scan_name_to_modules()
    bindings = domain_bindings(name_to_modules)
    plain = sum(1 for rows in bindings.values() for n, (_, t) in rows.items() if n == t)
    invented = sum(1 for rows in bindings.values() for n, (_, t) in rows.items() if n != t)
    assert plain > invented * 3, (
        f"{invented} invented names against {plain} that keep the generated name — "
        "the domain path is supposed to carry the common case"
    )


def test_current_tree_leaves_no_class_unreachable():
    """Guard passes on the generated tree as consolidated today."""
    name_to_modules = _scan_name_to_modules()
    # Must not raise.
    _enforce_every_class_is_reachable(name_to_modules, domain_bindings(name_to_modules))


def test_unreachable_class_fails_the_build():
    """A generated class bound by no domain module fails the consolidate step."""
    name_to_modules = {"WidgetGuardSentinel": {"core.widget_a", "enums.widget_b"}}
    bindings = domain_bindings(name_to_modules)
    bindings.pop("enums")

    with pytest.raises(ValueError) as excinfo:
        _enforce_every_class_is_reachable(name_to_modules, bindings)

    message = str(excinfo.value)
    assert "enums.widget_b.WidgetGuardSentinel" in message
    assert "reachable under no public name" in message
    assert "adcp.types.domains" in message


def test_a_class_its_domain_binds_is_reachable():
    """A name defined in exactly one module needs no qualified name."""
    name_to_modules = {"SoloGuardSentinel": {"core.solo"}}
    bindings = domain_bindings(name_to_modules)
    assert bindings == {"core": {"SoloGuardSentinel": ("core.solo", "SoloGuardSentinel")}}
    # Must not raise.
    _enforce_every_class_is_reachable(name_to_modules, bindings)


def test_two_classes_claiming_one_name_in_a_domain_fails_the_build():
    """The derivation refuses to drop a binding when stems stop being unique."""
    import scripts.consolidate_exports as ce

    name_to_modules = {"Clashing": {"core.a", "core.b"}}
    original = ce.qualified_public_name
    ce.qualified_public_name = lambda type_name, module_name: f"{type_name}Fixed"
    try:
        with pytest.raises(ValueError) as excinfo:
            ce.domain_bindings(name_to_modules)
    finally:
        ce.qualified_public_name = original

    message = str(excinfo.value)
    assert "core.ClashingFixed" in message
    assert "do not drop a binding" in message


# ---------------------------------------------------------------------------
# Aggregate schemas that inline private copies of a $ref'd schema
# ---------------------------------------------------------------------------
#
# ``card-asset.json`` and ``macro-declaration.json`` ``$ref`` other schemas.
# Whether datamodel-code-generator emits an import or inlines a private copy
# of the referenced graph depends on which module it reaches first, and that
# traversal order shifts whenever the bundle gains or loses a schema — see the
# codegen-instability note in CLAUDE.md.
#
# AdCP 3.2.0-rc.2 added new schemas (sync_reporting_status, consumer status,
# forecast rate range) with no change at all to card-asset.json or
# macro-declaration.json, and the reshuffled traversal made both modules start
# inlining. That produced 12 duplicate public type names for 12 wire types that
# already had canonical homes.
#
# ``exports_for_public_consolidation`` keeps those private copies out of the
# public namespace, exactly as it already does for ``asset_union`` and
# ``coordinated_placements``. These tests pin that behavior against a synthetic
# inlined module, so the guard holds whether or not the pinned bundle currently
# triggers the inlining.

_INLINED_CARD_ASSET = """
from adcp.types.base import AdCPBaseModel


class AiTool(AdCPBaseModel):
    name: str


class C2pa(AdCPBaseModel):
    manifest: str


class EmbeddedProvenanceItem(AdCPBaseModel):
    kind: str


class RenderGuidance(AdCPBaseModel):
    hint: str


class VerificationItem(AdCPBaseModel):
    result: str


class Watermark(AdCPBaseModel):
    media: str


class Provenance(AdCPBaseModel):
    declared_by: str


class CardAsset(AdCPBaseModel):
    asset_type: str
"""

_INLINED_MACRO_DECLARATION = """
from enum import StrEnum

from adcp.types.base import AdCPBaseModel


class MacroMappingStatus(StrEnum):
    mapped = "mapped"


class UniversalMacro(StrEnum):
    device_id = "DEVICE_ID"


class MacroProcessingOperation(StrEnum):
    resolve_value = "resolve_value"


class MacroTranslationTarget(AdCPBaseModel):
    token: str


class MacroValueContext(StrEnum):
    url = "url"


class MacroEncoding(AdCPBaseModel):
    kind: str


class MacroDeclaration(AdCPBaseModel):
    token: str
"""


@pytest.mark.parametrize(
    ("relative_path", "source", "root", "inlined"),
    [
        (
            "core/assets/card_asset.py",
            _INLINED_CARD_ASSET,
            "CardAsset",
            {
                "AiTool",
                "C2pa",
                "EmbeddedProvenanceItem",
                "RenderGuidance",
                "VerificationItem",
                "Watermark",
                "Provenance",
            },
        ),
        (
            "core/macro_declaration.py",
            _INLINED_MACRO_DECLARATION,
            "MacroDeclaration",
            {
                "MacroEncoding",
                "MacroMappingStatus",
                "MacroProcessingOperation",
                "MacroTranslationTarget",
                "MacroValueContext",
                "UniversalMacro",
            },
        ),
    ],
    ids=["card_asset", "macro_declaration"],
)
def test_aggregate_modules_export_only_their_root(
    tmp_path, monkeypatch, relative_path, source, root, inlined
):
    """An inlined private copy must not reach the public namespace.

    Each inlined class is a copy of a wire type whose canonical definition
    lives in its own module (``core/provenance.py``, ``enums/universal_macro.py``
    and friends). Exporting the copy too would put two classes for one wire
    type in ``adcp.types`` and let traversal order pick which one an adopter
    gets.
    """
    module_path = tmp_path / relative_path
    module_path.parent.mkdir(parents=True, exist_ok=True)
    module_path.write_text(source)
    monkeypatch.setattr("scripts.consolidate_exports.GENERATED_POC_DIR", tmp_path)

    exports = exports_for_public_consolidation(module_path)

    assert exports == {root}
    assert not (exports & inlined), "inlined private copies must stay out of the namespace"
    # Sanity: without the suppression the raw extractor does see them, so this
    # test would fail loudly if the special case were dropped.
    assert inlined <= extract_exports_from_module(module_path)
