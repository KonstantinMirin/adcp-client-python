"""Tests for the consolidate-step reachability guards (issues #911, #1080).

`consolidate_exports.py` flattens every `generated_poc/` module into a single
namespace. When the same bare type name is defined in more than one module, one
class wins that name in `_generated` and the others would be unreachable, so
`disambiguated.py` names every variant and `error_details.py` names the
error-details family with the field types its models reference.

Both export sets are derived from the module tree. These tests assert the
derivation covers every generated class, that no two classes claim one
qualified name, and that the guard raises when a class would be left
unreachable.
"""

from __future__ import annotations

import pytest

from scripts.consolidate_exports import (
    KNOWN_COLLISIONS,
    _enforce_every_class_is_reachable,
    _scan_name_to_modules,
    colliding_names,
    disambiguated_bindings,
    exports_for_public_consolidation,
    extract_exports_from_module,
    generate_consolidated_exports,
    qualified_public_name,
)


def test_qualified_name_carries_the_whole_module_path():
    """The stem alone is ambiguous: two packages can hold the same filename."""
    assert qualified_public_name(
        "AudienceSource", "enums.audience_source"
    ) != qualified_public_name("AudienceSource", "core.audience_source")
    assert (
        qualified_public_name("QuerySummary", "creative.list_creatives_response")
        == "QuerySummaryFromCreativeListCreativesResponse"
    )


def test_every_colliding_variant_has_a_qualified_name():
    """One binding per (module, type) pair, for every name defined more than once."""
    name_to_modules = _scan_name_to_modules()
    collisions = colliding_names(name_to_modules)
    assert collisions, "the generated tree has no colliding names — guard is vacuous"

    bindings = disambiguated_bindings(name_to_modules)
    expected = {(module, type_name) for type_name, mods in collisions.items() for module in mods}
    assert set(bindings.values()) == expected
    assert len(bindings) == len(expected), "a qualified name bound two classes"


def test_known_collisions_do_not_decide_reachability():
    """A name in KNOWN_COLLISIONS is still carried by the derived bindings.

    The table decides whether the bare slot in ``_generated`` stays unbound. It
    must not be what makes a class importable, because a hand-maintained table
    goes stale on the next schema addition (#911, #1080).
    """
    name_to_modules = _scan_name_to_modules()
    bindings = disambiguated_bindings(name_to_modules)
    for name in KNOWN_COLLISIONS:
        modules = name_to_modules.get(name, set())
        if len(modules) < 2:
            continue
        for module in modules:
            assert bindings.get(qualified_public_name(name, module)) == (module, name)


def test_current_tree_leaves_no_class_unreachable():
    """The guard passes on the generated tree as consolidated today."""
    name_to_modules = _scan_name_to_modules()
    consolidation = generate_consolidated_exports()
    # Must not raise.
    _enforce_every_class_is_reachable(
        name_to_modules,
        consolidation.reachable_here,
        disambiguated_bindings(name_to_modules, consolidation.displaced),
    )


def test_unreachable_class_fails_the_build():
    """A generated class bound by neither module fails the consolidate step."""
    name_to_modules = {"WidgetGuardSentinel": {"core.widget_a", "core.widget_b"}}
    bindings = disambiguated_bindings(name_to_modules)
    # Drop one variant, as a derivation that skipped a class would.
    bindings.pop(qualified_public_name("WidgetGuardSentinel", "core.widget_b"))

    with pytest.raises(ValueError) as excinfo:
        _enforce_every_class_is_reachable(name_to_modules, set(), bindings)

    message = str(excinfo.value)
    assert "core.widget_b.WidgetGuardSentinel" in message
    assert "reachable under no public name" in message
    assert "adcp.types.disambiguated" in message


def test_a_class_the_consolidated_module_binds_is_reachable():
    """A name defined in exactly one module needs no qualified name."""
    name_to_modules = {"SoloGuardSentinel": {"core.solo"}}
    # Must not raise: ``_generated`` binds the bare name.
    _enforce_every_class_is_reachable(name_to_modules, {("core.solo", "SoloGuardSentinel")}, {})


def test_a_displaced_class_is_reachable_through_its_qualified_name():
    """A compatibility alias may take a bare name only if the class keeps one.

    ``Transport = Transport1`` in ``_generated`` takes the bare name from the
    class ``protocol/get-adcp-capabilities-response.json`` generates. Passing it
    as displaced is what keeps it importable.
    """
    name_to_modules = {"Shadowed": {"core.shadowed"}}
    displaced = {("core.shadowed", "Shadowed")}

    with pytest.raises(ValueError):
        _enforce_every_class_is_reachable(name_to_modules, set(), {})

    # Must not raise once the displaced class carries its qualified name.
    _enforce_every_class_is_reachable(
        name_to_modules, set(), disambiguated_bindings(name_to_modules, displaced)
    )


def test_two_classes_claiming_one_qualified_name_fails_the_build():
    """The derivation refuses to drop a binding when names clash."""
    import scripts.consolidate_exports as ce

    name_to_modules = {"Clashing": {"core.a", "core.b"}}
    monkey = lambda type_name, module_name: f"{type_name}Fixed"  # noqa: E731, ARG005
    original = ce.qualified_public_name
    ce.qualified_public_name = monkey
    try:
        with pytest.raises(ValueError) as excinfo:
            ce.disambiguated_bindings(name_to_modules)
    finally:
        ce.qualified_public_name = original

    message = str(excinfo.value)
    assert "ClashingFixed" in message
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
