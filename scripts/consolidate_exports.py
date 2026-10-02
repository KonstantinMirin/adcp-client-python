#!/usr/bin/env python3
"""
Create the consolidated export files that re-export all types from generated_poc modules.

This script analyzes all modules in generated_poc/ and writes three modules:

* ``_generated.py`` — every public generated type in one namespace. A bare type
  name defined by several generated modules resolves to one winner here.
* ``disambiguated.py`` — every variant of every such name under a module-qualified
  public name, derived from the module tree. No class is reachable under zero names.
* ``error_details.py`` — the ``error-details/*.json`` model family plus the
  transitive closure of its field types, derived from the generated package.

Two build guards replace the former checked-in collision allowlist: the consolidate
step fails when a generated public class is reachable under no name, and when two
(name, module) pairs want the same qualified name. Both are properties of the tree,
so a schema addition cannot reopen the gap. See issues #911 and #1080.

Usage:
    python scripts/consolidate_exports.py
"""

from __future__ import annotations

import argparse
import ast
import importlib
import inspect
import pkgutil
import re
import subprocess
import sys
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import NamedTuple, get_args

GENERATED_POC_DIR = Path(__file__).parent.parent / "src" / "adcp" / "types" / "generated_poc"
OUTPUT_FILE = Path(__file__).parent.parent / "src" / "adcp" / "types" / "_generated.py"
DISAMBIGUATED_FILE = Path(__file__).parent.parent / "src" / "adcp" / "types" / "disambiguated.py"
ERROR_DETAILS_FILE = Path(__file__).parent.parent / "src" / "adcp" / "types" / "error_details.py"

_GENERATION_DATE_RE = re.compile(r"^Generation date: .+$", re.MULTILINE)

# Bare names this module refuses to bind to one winner in ``_generated``, each
# listed with the module stems that define it. ``aliases.py`` imports the
# ``_<Name>From<Stem>`` private exports these produce and gives them semantic
# public names.
#
# Reachability does NOT depend on this table: ``disambiguated.py`` carries every
# variant of every colliding name, derived from the module tree. A name belongs
# here only when the bare slot in ``_generated`` must stay unbound.
KNOWN_COLLISIONS: dict[str, set[str]] = {
    "Package": {"package", "create_media_buy_response", "get_media_buys_response"},
    # DeliveryStatus appears in get_media_buy_delivery_response (5 values) and
    # get_media_buys_response (6 values, adds not_delivering). Export both with
    # qualified names so aliases.py can re-export the superset as the canonical one.
    "DeliveryStatus": {"get_media_buy_delivery_response", "get_media_buys_response"},
    # Note: "Catalog" also collides between core.catalog and media_buy.sync_catalogs_response.
    # We intentionally let core.catalog win (first-seen, since core/ sorts before media_buy/).
    # The response-level Catalog is imported directly in aliases.py as SyncCatalogResult.
    # Audience collides between get_media_buy_delivery_request (breakdown config) and
    # sync_audiences_request (audience payload). aliases.py imports the request one directly.
    "Audience": {
        "get_media_buy_delivery_request",
        "sync_audiences_request",
        "sync_audiences_response",
    },
    # Error collides between core.error (Pydantic model used everywhere) and
    # compliance.comply_test_controller_response (test-only enum). Export both
    # with qualified names; aliases/init re-export core Error as the canonical one.
    "Error": {"error", "comply_test_controller_response"},
    # FormatId: AdCP 3.0.1 renamed core/format-id.json title from "Format ID"
    # to "Format Reference (Structured Object)". The canonical class in
    # core/format_id.py is now FormatReferenceStructuredObject, but every
    # bundled-message file inlines a per-message duplicate still named
    # FormatId. Without this entry, the bundled stale duplicate would win
    # the bare-name slot in _generated.py and shadow the canonical class.
    # aliases.py re-exports the canonical FormatReferenceStructuredObject as
    # the public FormatId.
    "FormatId": {
        "build_creative_request",
        "build_creative_response",
        "calibrate_content_request",
        "create_content_standards_request",
        "create_media_buy_request",
        "create_media_buy_response",
        "get_content_standards_response",
        "get_creative_delivery_response",
        "get_creative_features_request",
        "get_media_buy_artifacts_response",
        "get_products_request",
        "get_products_response",
        "list_content_standards_response",
        "list_creative_formats_request",
        "list_creative_formats_response",
        "list_creatives_request",
        "list_creatives_response",
        "package_request",
        "preview_creative_request",
        "preview_creative_response",
        "sync_creatives_request",
        "update_content_standards_request",
        "update_media_buy_request",
        "update_media_buy_response",
        "validate_content_delivery_request",
    },
    # DeclaredBy appears in core provenance and SI sponsored-context schemas
    # with different Role enums. Export both qualified variants and expose
    # semantic aliases from aliases.py.
    "DeclaredBy": {"provenance", "si_sponsored_context"},
    # Trusted Match uses TmpxMacro for two different wire shapes:
    # provider_registration defines the registered macro name as a string
    # RootModel, while identity_match_response defines emitted macro/value
    # pairs. Export both and expose semantic aliases from aliases.py.
    "TmpxMacro": {"identity_match_response", "provider_registration"},
    # Beta.3 rendering schemas introduce same-named types for distinct trust
    # domains. Export every variant under a semantic alias instead of letting
    # generated module order choose a public class.
    "Provenance": {"provenance", "reference_renderer"},
    "RenderingOrigin": {"preview_renderer_metadata", "get_adcp_capabilities_response"},
    "Route": {"preview_provider", "get_adcp_capabilities_response"},
    # Beta.4 introduces a request-proposals compatibility result whose
    # product-id wrapper is distinct from the discovery-criteria wrapper.
    # Export both under qualified internal names; aliases.py exposes stable
    # semantic names for adopters.
    "ProductId": {"product_discovery_criteria", "request_proposals_response"},
    # Beta.5 adds the compact proposal budget-guidance shape to the canonical
    # proposal and refine response while retaining the structurally different
    # legacy proposal shape. Export every generated class under an explicit
    # semantic alias instead of allowing module order to select one silently.
    "TotalBudgetGuidance": {
        "canonical_proposal",
        "proposal",
        "refine_proposals_response",
    },
    # Request-signing capability entries and downstream connection
    # requirements use distinct validation constraints despite sharing a
    # generated title. aliases.py exposes both under semantic names.
    "RequiredForItem": {
        "downstream_connection_requirement",
        "get_adcp_capabilities_response",
    },
}


def module_qualifier(module_name: str) -> str:
    """CamelCase the dotted generated-module path: ``core.error`` -> ``CoreError``."""
    return "".join(
        part.replace("_", " ").title().replace(" ", "") for part in module_name.split(".")
    )


def qualified_public_name(type_name: str, module_name: str) -> str:
    """The unambiguous public name for one variant of a colliding type name.

    The whole dotted module path goes into the name, not just the filename stem:
    module paths are unique, so the qualified name is unique by construction and
    stays stable when a schema addition introduces another module with the same
    stem under a different package.
    """
    return f"{type_name}From{module_qualifier(module_name)}"


def extract_exports_from_module(module_path: Path) -> set[str]:
    """Extract all public class and type alias names from a Python module."""
    with open(module_path) as f:
        try:
            tree = ast.parse(f.read())
        except SyntaxError:
            return set()

    exports = set()

    def _add_public_type_name(name: str) -> None:
        if name and not name.startswith("_") and name[0].isupper():
            exports.add(name)

    # Only look at module-level nodes (not inside classes)
    for node in tree.body:
        # Class definitions
        if isinstance(node, ast.ClassDef):
            if not node.name.startswith("_"):
                exports.add(node.name)
        # Module-level assignments (type aliases)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    # Only export if it looks like a type name (starts with capital)
                    _add_public_type_name(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            # ``Foo: TypeAlias = ...`` is common in post-generated response
            # unions; keep those public aliases in the consolidated namespace.
            _add_public_type_name(node.target.id)

    return exports


def exports_for_public_consolidation(module_path: Path) -> set[str]:
    """Return the intentional public exports for a generated module.

    Some aggregate/reference schemas necessarily define private copies of
    source models. Re-exporting every nested helper makes those copies shadow
    the canonical module with the same wire type.
    """
    rel_path = module_path.relative_to(GENERATED_POC_DIR)
    if rel_path == Path("brand_discovery.py"):
        return set()
    if rel_path.parts[:2] == ("core", "async_response_refs"):
        return set()

    exports = extract_exports_from_module(module_path)
    if rel_path == Path("core/assets/asset_union.py"):
        return exports & {"AssetVariant"}
    if rel_path == Path("formats/canonical/coordinated_placements.py"):
        # This aggregate schema inlines the component canonical formats. Keep
        # those nested implementation copies private and export only its root.
        return exports & {"CanonicalFormatCoordinatedPlacements"}
    if rel_path == Path("core/assets/card_asset.py"):
        # card-asset.json ``$ref``s core/provenance.json. Depending on which
        # module the generator visits first, it either emits an import or
        # inlines the whole provenance graph here (AiTool, C2pa,
        # EmbeddedProvenanceItem, RenderGuidance, VerificationItem,
        # Watermark). Those inlined classes are copies of the canonical ones
        # in core/provenance.py, so exporting them would put two classes for
        # one wire type in the public namespace and let traversal order decide
        # which an adopter gets. Export only the root.
        return exports & {"CardAsset"}
    if rel_path == Path("core/macro_declaration.py"):
        # Same shape: macro-declaration.json ``$ref``s the macro enums and
        # core/macro-encoding.json / core/macro-translation-target.json, and
        # the generator inlines copies of them here when it reaches this
        # module first. The canonical definitions live in enums/ and their
        # own core/ modules; keep these copies private and export the root.
        return exports & {"MacroDeclaration"}
    return exports


def colliding_names(name_to_modules: dict[str, set[str]]) -> dict[str, set[str]]:
    """Every public name defined by two or more non-bundled generated modules."""
    return {n: mods for n, mods in name_to_modules.items() if len(mods) > 1}


def disambiguated_bindings(
    name_to_modules: dict[str, set[str]],
    displaced: set[tuple[str, str]] = frozenset(),  # type: ignore[assignment]
) -> dict[str, tuple[str, str]]:
    """Map each qualified public name to the (module, type name) it binds.

    Two kinds of class land here, and both are derived rather than listed:
    every variant of a name that several generated modules define, and every
    class whose bare name a compatibility alias in ``_generated`` takes over
    (``displaced``). Adding a schema that reuses a type name extends this
    mapping instead of hiding a class.
    """
    pairs = [
        (module_name, type_name)
        for type_name, modules in colliding_names(name_to_modules).items()
        for module_name in modules
    ]
    pairs.extend(sorted(displaced))

    bindings: dict[str, tuple[str, str]] = {}
    clashes: dict[str, list[tuple[str, str]]] = {}
    for module_name, type_name in pairs:
        qualified = qualified_public_name(type_name, module_name)
        if bindings.get(qualified) == (module_name, type_name):
            continue
        if qualified in bindings:
            clashes.setdefault(qualified, [bindings[qualified]]).append((module_name, type_name))
            continue
        bindings[qualified] = (module_name, type_name)
    if clashes:
        details = "\n".join(
            f"  {qualified}: {sorted(f'{m}.{t}' for m, t in sources)}"
            for qualified, sources in sorted(clashes.items())
        )
        raise ValueError(
            f"{len(clashes)} qualified export name(s) are claimed by more than one "
            f"generated class:\n{details}\n\n"
            "qualified_public_name() must produce one name per (module, type) pair. "
            "Two generated modules with the same dotted path cannot exist, so this "
            "means the name derivation lost information — fix "
            "qualified_public_name(), do not drop a binding.\n"
        )
    return bindings


def _enforce_every_class_is_reachable(
    name_to_modules: dict[str, set[str]],
    consolidated_sources: set[tuple[str, str]],
    disambiguated_exports: dict[str, tuple[str, str]],
) -> None:
    """Fail the build when a generated public class is reachable under no name.

    ``_generated`` binds one winner per bare name, so a colliding class reaches
    adopters only through its qualified name in ``disambiguated``. This guard is
    a property of the tree rather than a snapshot of it: a schema addition that
    introduces a new collision satisfies it automatically, and a change that
    makes the derivation skip a class fails it.
    """
    reachable = set(disambiguated_exports.values()) | consolidated_sources
    unreachable = [
        (module_name, type_name)
        for type_name, modules in name_to_modules.items()
        for module_name in modules
        if (module_name, type_name) not in reachable
    ]
    if not unreachable:
        return
    details = "\n".join(f"  {module}.{name}" for module, name in sorted(unreachable))
    raise ValueError(
        f"{len(unreachable)} generated public class(es) are reachable under no "
        f"public name:\n{details}\n\n"
        "Every public class in a non-bundled generated module must be importable "
        "either from adcp.types (the bare name, when it is unambiguous) or from "
        "adcp.types.disambiguated (the module-qualified name, when it is not). A "
        "class that is reachable under no name is a model an adopter cannot "
        "construct, which is how the error-details family became unusable "
        "(#1080).\n"
    )


def _scan_name_to_modules() -> dict[str, set[str]]:
    """Map every public name to the set of non-bundled modules that define it."""

    def _module_sort_key(p: Path) -> tuple[int, int, str]:
        rel = p.relative_to(GENERATED_POC_DIR)
        is_enum = rel.parts[0] == "enums" if len(rel.parts) > 1 else False
        is_bundled = rel.parts[0] == "bundled" if len(rel.parts) > 1 else False
        return (0 if is_enum else 1, 1 if is_bundled else 0, str(p))

    modules = sorted(GENERATED_POC_DIR.rglob("*.py"), key=_module_sort_key)
    modules = [
        m
        for m in modules
        if m.stem != "__init__"
        and not m.stem.startswith(".")
        and m.relative_to(GENERATED_POC_DIR).parts[0] != "bundled"
    ]

    name_to_modules: dict[str, set[str]] = {}
    for module_path in modules:
        rel_path = module_path.relative_to(GENERATED_POC_DIR)
        module_name = ".".join(list(rel_path.parts[:-1]) + [rel_path.stem])
        for export_name in exports_for_public_consolidation(module_path):
            name_to_modules.setdefault(export_name, set()).add(module_name)
    return name_to_modules


class Consolidation(NamedTuple):
    """The ``_generated`` module plus what the other two generated modules need."""

    content: str
    #: (module, type name) pairs this module binds under a name in its ``__all__``.
    reachable_here: set[tuple[str, str]]
    #: (module, type name) pairs whose bare name a compatibility alias took over.
    displaced: set[tuple[str, str]]


def generate_consolidated_exports() -> Consolidation:
    """Generate the consolidated exports file content."""

    # Discover all modules recursively (including subdirectories)
    # Sort order: enums first (canonical enum definitions), then non-bundled,
    # then bundled. Bundled schemas inline the same types as non-bundled, but
    # as renumbered/enum duplicates — we want the canonical class definitions
    # from non-bundled to win the first-seen dedup.
    def _module_sort_key(p: Path) -> tuple[int, int, str]:
        rel = p.relative_to(GENERATED_POC_DIR)
        is_enum = rel.parts[0] == "enums" if len(rel.parts) > 1 else False
        is_bundled = rel.parts[0] == "bundled" if len(rel.parts) > 1 else False
        return (0 if is_enum else 1, 1 if is_bundled else 0, str(p))

    modules = sorted(GENERATED_POC_DIR.rglob("*.py"), key=_module_sort_key)
    modules = [
        m
        for m in modules
        if m.stem != "__init__" and not m.stem.startswith(".")
        # Bundled schemas inline complete task envelopes for validation and
        # SDK-internal use. They duplicate the public non-bundled models and
        # can contain enormous inline unions that Pydantic refuses to build
        # when imported eagerly through _generated. Keep the files on disk,
        # but do not re-export bundled copies as public SDK types.
        and m.relative_to(GENERATED_POC_DIR).parts[0] != "bundled"
    ]

    print(f"Found {len(modules)} modules to consolidate")

    # Build import statements and collect all exports
    # Track which module first defined each export name
    export_to_module: dict[str, str] = {}
    import_lines = []
    all_exports = set()
    collisions = []
    # Every name this module binds, mapped to the generated class behind it. The
    # reachability guard reads it, so a binding that drops a class shows up as a
    # build failure rather than as a missing import an adopter discovers.
    name_source: dict[str, tuple[str, str]] = {}

    # Special handling for known collisions
    # We need BOTH versions of these types available, so import them with qualified names
    known_collisions = KNOWN_COLLISIONS

    # Record every module that defines each name so the build guard can detect
    # name collisions independently of which module wins the bare-name slot.
    # A name in >1 module is a collision regardless of whether it resolves via
    # first-seen or stem-preference order.
    name_to_modules: dict[str, set[str]] = {}

    special_imports = []
    collision_modules_seen: dict[str, set[str]] = {name: set() for name in known_collisions}

    def _stem_matches_export(module_stem: str, export_name: str) -> bool:
        """True if the module filename matches the export (snake_case ↔ PascalCase)."""
        return module_stem.replace("_", "").lower() == export_name.lower()

    # First pass: decide which module owns each export name.
    # Canonical class definitions live in files named after the class
    # (e.g. core/format.py defines Format). Prefer those over duplicates
    # elsewhere (bundled copies, enum aliases in unrelated files).
    module_exports: dict[str, set[str]] = {}
    for module_path in modules:
        rel_path = module_path.relative_to(GENERATED_POC_DIR)
        module_parts = list(rel_path.parts[:-1]) + [rel_path.stem]
        module_name = ".".join(module_parts)
        display_name = rel_path.stem

        exports = exports_for_public_consolidation(module_path)
        if not exports:
            continue
        module_exports[module_name] = exports

        for export_name in exports:
            name_to_modules.setdefault(export_name, set()).add(module_name)

            if export_name in known_collisions and display_name in known_collisions[export_name]:
                collision_modules_seen[export_name].add(module_name)
                # Sentinel: known collisions are only imported via qualified
                # names later, never as a primary export.
                export_to_module[export_name] = "<collision>"
                continue

            if export_name in export_to_module:
                first_module = export_to_module[export_name]
                first_stem = first_module.rsplit(".", 1)[-1]
                if _stem_matches_export(display_name, export_name) and not _stem_matches_export(
                    first_stem, export_name
                ):
                    export_to_module[export_name] = module_name
                    collisions.append(
                        f"  {export_name}: defined in ['{first_module}', '{module_name}'] "
                        f"(preferring {module_name} — stem matches export name)"
                    )
                else:
                    collisions.append(
                        f"  {export_name}: defined in both "
                        f"{first_module} and {module_name} (using {first_module})"
                    )
            else:
                export_to_module[export_name] = module_name

    # Second pass: record which exports each module owns. The import lines come
    # later, because a name that a compatibility alias rebinds is imported under
    # a private name instead of its own (see ``compatibility_bindings``).
    owned_by_module: dict[str, set[str]] = {}
    for module_name, exports in module_exports.items():
        owned = {e for e in exports if export_to_module.get(e) == module_name}
        display_name = module_name.rsplit(".", 1)[-1]
        if not owned:
            print(f"  {display_name}: 0 unique exports (all collisions)")
            continue
        print(f"  {display_name}: {len(owned)} exports")
        owned_by_module[module_name] = owned
        all_exports.update(owned)

    # Generate special imports for all known collisions
    for type_name, modules_seen in collision_modules_seen.items():
        if not modules_seen:
            continue
        collisions.append(
            f"  {type_name}: defined in {sorted(modules_seen)} (all exported with qualified names)"
        )
        for module_name in sorted(modules_seen):
            # Non-bundled versions use the stem as the alias suffix
            # (_PackageFromGetMediaBuysResponse). Bundled versions prepend
            # "Bundled<Subdir>" so the same filename existing under both
            # bundled/creative/ and bundled/media_buy/ produces distinct
            # qualified names (otherwise the duplicate triggers a mypy
            # incompatible-import error at import time).
            parts = module_name.split(".")
            stem = parts[-1].replace("_", " ").title().replace(" ", "")
            if parts[0] == "bundled" and len(parts) >= 3:
                subdir = parts[1].replace("_", " ").title().replace(" ", "")
                prefix = f"Bundled{subdir}"
            elif parts[0] == "bundled":
                prefix = "Bundled"
            else:
                prefix = ""
            qualified_name = f"_{type_name}From{prefix}{stem}"
            import_str = (
                f"from adcp.types.generated_poc.{module_name}"
                f" import {type_name} as {qualified_name}"
            )
            special_imports.append(import_str)
            all_exports.add(qualified_name)
            name_source[qualified_name] = (module_name, type_name)

    if collisions:
        print("\n⚠️  Name collisions detected (duplicates skipped):")
        for collision in sorted(collisions):
            print(collision)

    # Backward compatibility aliases (only if source exists).
    #
    # A name on the left here is NOT imported under its own name below: the
    # generated class it would have bound is imported privately instead, so every
    # public binding is a first binding. Rebinding an imported name needs
    # ``# type: ignore[assignment]``, and that suppression is what made the public
    # symbol mean one class to mypy and another at runtime (#1141) — mypy keeps
    # the pre-rebind declaration, so a whole shifted window of names typed one
    # variant off what they held.
    aliases: dict[str, str] = {}
    # AdCP renumbered the adagents authorization variants when it added an arm at
    # the front. Each historical public name keeps the shape it has always had,
    # and the root union gets its own name.
    if {"AuthorizedAgents", "AuthorizedAgents6"}.issubset(all_exports):
        aliases["AuthorizedAgentsUnion"] = "AuthorizedAgents"
        for variant in range(6):
            public = "AuthorizedAgents" if variant == 0 else f"AuthorizedAgents{variant}"
            aliases[public] = f"AuthorizedAgents{variant + 1}"
    # Concrete creative asset / manifest classes for subclassing and direct
    # construction; the root unions get their own names.
    for base in ("CreativeAsset", "CreativeManifest"):
        if {base, f"{base}1"}.issubset(all_exports):
            aliases[f"{base}Union"] = base
            aliases[base] = f"{base}1"
    if "AdvertisingChannels" in all_exports:
        aliases["Channels"] = "AdvertisingChannels"
    # Package from get_media_buys_response is a distinct enriched view with creative approvals
    # and delivery snapshots. Export as MediaBuyPackage to avoid collision with core Package.
    if "_PackageFromGetMediaBuysResponse" in all_exports:
        aliases["MediaBuyPackage"] = "_PackageFromGetMediaBuysResponse"
    # DeliveryStatus from get_media_buys_response is a superset (adds not_delivering).
    # Export as the canonical DeliveryStatus so users can compare against all values.
    if "_DeliveryStatusFromGetMediaBuysResponse" in all_exports:
        aliases["DeliveryStatus"] = "_DeliveryStatusFromGetMediaBuysResponse"
    # AdCP 3.1 RC renamed the signals-domain enum to SignalAvailabilityType.
    # Keep the historical public SignalCatalogType name as a compatibility alias.
    if "SignalCatalogType" not in all_exports and "SignalAvailabilityType" in all_exports:
        aliases["SignalCatalogType"] = "SignalAvailabilityType"
    # Reporting-delivery capabilities introduced a nested string RootModel named
    # Transport alongside the existing SI endpoint Transport model. Preserve the
    # established public Transport constructor used by decisioning adopters.
    if "Transport" in all_exports and "Transport1" in all_exports:
        aliases["Transport"] = "Transport1"
    # AdCP 3.1 beta 3 collapsed many single-shape response schemas from
    # RootModel union variants (FooResponse1/FooResponse2) to one concrete
    # FooResponse model. Keep the old numbered names as aliases when the
    # upstream generator no longer emits them so legacy imports continue to
    # work while resolving to the beta 3 shape.
    response_arm_aliases = {
        "AcquireRightsResponse1": "AcquireRightsResponse",
        "AcquireRightsResponse2": "AcquireRightsResponse",
        "AcquireRightsResponse3": "AcquireRightsResponse",
        "AcquireRightsResponse4": "AcquireRightsResponse",
        "ActivateSignalResponse1": "ActivateSignalResponse",
        "ActivateSignalResponse2": "ActivateSignalResponse",
        "BuildCreativeResponse1": "BuildCreativeResponse",
        "BuildCreativeResponse2": "BuildCreativeResponse",
        "CalibrateContentResponse1": "CalibrateContentResponse",
        "CalibrateContentResponse2": "CalibrateContentResponse",
        "ComplyTestControllerResponse1": "ComplyTestControllerResponse",
        "ComplyTestControllerResponse2": "ComplyTestControllerResponse",
        "ComplyTestControllerResponse3": "ComplyTestControllerResponse",
        "ComplyTestControllerResponse4": "ComplyTestControllerResponse",
        "CreateContentStandardsResponse1": "CreateContentStandardsResponse",
        "CreateContentStandardsResponse2": "CreateContentStandardsResponse",
        "CreateMediaBuyResponse1": "CreateMediaBuyResponse",
        "CreateMediaBuyResponse2": "CreateMediaBuyResponse",
        "CreateMediaBuyResponse3": "CreateMediaBuyResponse",
        "GetAccountFinancialsResponse1": "GetAccountFinancialsResponse",
        "GetAccountFinancialsResponse2": "GetAccountFinancialsResponse",
        "GetBrandIdentityResponse1": "GetBrandIdentityResponse",
        "GetBrandIdentityResponse2": "GetBrandIdentityResponse",
        "GetContentStandardsResponse1": "GetContentStandardsResponse",
        "GetContentStandardsResponse2": "GetContentStandardsResponse",
        "GetCreativeFeaturesResponse1": "GetCreativeFeaturesResponse",
        "GetCreativeFeaturesResponse2": "GetCreativeFeaturesResponse",
        "GetMediaBuyArtifactsResponse1": "GetMediaBuyArtifactsResponse",
        "GetMediaBuyArtifactsResponse2": "GetMediaBuyArtifactsResponse",
        "GetRightsResponse1": "GetRightsResponse",
        "GetRightsResponse2": "GetRightsResponse",
        "ListContentStandardsResponse1": "ListContentStandardsResponse",
        "ListContentStandardsResponse2": "ListContentStandardsResponse",
        "LogEventResponse1": "LogEventResponse",
        "LogEventResponse2": "LogEventResponse",
        "PreviewCreativeResponse1": "PreviewCreativeResponse",
        "PreviewCreativeResponse2": "PreviewCreativeResponse",
        "PreviewCreativeResponse3": "PreviewCreativeResponse",
        "ProvidePerformanceFeedbackResponse1": "ProvidePerformanceFeedbackResponse",
        "ProvidePerformanceFeedbackResponse2": "ProvidePerformanceFeedbackResponse",
        "SyncAccountsResponse1": "SyncAccountsResponse",
        "SyncAccountsResponse2": "SyncAccountsResponse",
        "SyncAudiencesResponse1": "SyncAudiencesResponse",
        "SyncAudiencesResponse2": "SyncAudiencesResponse",
        "SyncCatalogsResponse1": "SyncCatalogsResponse",
        "SyncCatalogsResponse2": "SyncCatalogsResponse",
        "SyncCreativesResponse1": "SyncCreativesResponse",
        "SyncCreativesResponse2": "SyncCreativesResponse",
        "SyncEventSourcesResponse1": "SyncEventSourcesResponse",
        "SyncEventSourcesResponse2": "SyncEventSourcesResponse",
        "UpdateContentStandardsResponse1": "UpdateContentStandardsResponse",
        "UpdateContentStandardsResponse2": "UpdateContentStandardsResponse",
        "UpdateMediaBuyResponse1": "UpdateMediaBuyResponse",
        "UpdateMediaBuyResponse2": "UpdateMediaBuyResponse",
        "UpdateMediaBuyResponse3": "UpdateMediaBuyResponse",
        "ValidateContentDeliveryResponse1": "ValidateContentDeliveryResponse",
        "ValidateContentDeliveryResponse2": "ValidateContentDeliveryResponse",
    }
    for alias, target in response_arm_aliases.items():
        if alias not in all_exports and target in all_exports:
            aliases[alias] = target
    # The beta 3 product schema is a oneOf over two concrete product shapes.
    # Preserve the historical public Product class as the first concrete model
    # so adopters can keep subclassing it for internal-only fields.
    if "Product" in all_exports and "Product1" in all_exports:
        aliases["Product"] = "Product1"

    # A public name a compatibility alias binds keeps its generated class under a
    # private name, so the alias is the name's first and only binding.
    rebound = {name for name in aliases if name in all_exports}
    private_name = {name: f"_Generated{name}" for name in rebound}

    # Emit one import line per module. Rebound names come in privately.
    for module_name, owned in owned_by_module.items():
        imported = []
        for export_name in sorted(owned):
            if export_name in private_name:
                imported.append(f"{export_name} as {private_name[export_name]}")
                name_source[private_name[export_name]] = (module_name, export_name)
            else:
                imported.append(export_name)
                name_source[export_name] = (module_name, export_name)
        import_lines.append(
            f"from adcp.types.generated_poc.{module_name} import {', '.join(imported)}"
        )

    all_exports_with_aliases = all_exports | set(aliases)

    alias_lines = []
    if aliases:
        alias_lines.extend(
            [
                "",
                "# Backward compatibility aliases for renamed types",
            ]
        )
        for alias, target in aliases.items():
            source = private_name.get(target, target)
            alias_lines.append(f"{alias} = {source}")
            name_source[alias] = name_source[source]

    # The classes whose bare name a compatibility alias took over. They reach
    # adopters through their qualified names in ``disambiguated``.
    displaced = {name_source[private] for private in private_name.values()}
    reachable_here = {
        source for name, source in name_source.items() if name in all_exports_with_aliases
    }

    # Generate file content
    generation_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        '"""INTERNAL: Consolidated generated types.',
        "",
        "DO NOT import from this module directly.",
        "Use 'from adcp import Type' or 'from adcp.types import Type' instead.",
        "",
        "This module consolidates all generated types from generated_poc/ into a single",
        "namespace for convenience. The leading underscore signals this is private API.",
        "",
        "A bare type name that several generated modules define resolves to one class",
        "here. Every variant of such a name is exported from adcp.types.disambiguated",
        "under its module-qualified name.",
        "",
        "Auto-generated by datamodel-code-generator from JSON schemas.",
        "DO NOT EDIT MANUALLY.",
        "",
        "Generated from: https://github.com/adcontextprotocol/adcp/tree/main/schemas",
        f"Generation date: {generation_date}",
        '"""',
        "# ruff: noqa: E501, I001",
        "from __future__ import annotations",
        "",
        "# Import all types from generated_poc modules",
    ]

    lines.extend(import_lines)

    # Add special imports for name collisions
    if special_imports:
        lines.extend(
            [
                "",
                "# Special imports for name collisions"
                " (qualified names for types defined in multiple modules)",
            ]
        )
        lines.extend(special_imports)

    lines.extend(alias_lines)

    # Add backwards-compat stubs for types removed from upstream schemas.
    # Kept so existing code importing them continues to work.
    # Model stubs accept any payload (extra="allow").
    # PromotedOfferingsRequirement is preserved as an Enum since it was one upstream.
    # No backward-compat stubs. The SDK surface matches the spec directly.
    # Removed types (BrandManifest, PromotedOfferings, DeliverTo, Pricing,
    # FormatCategory, PackageStatus, etc.) are documented in
    # MIGRATION_v3_to_v4.md.

    # Format __all__ list with proper line breaks (max 100 chars per line)
    # Exclude private names that are alias targets (internal intermediates only).
    # Private names that external modules import (e.g., _PackageFromPackage used by aliases.py)
    # must remain in __all__ so mypy allows the import.
    internal_alias_targets = {v for v in aliases.values() if v.startswith("_")}
    exports_list = sorted(
        name
        for name in all_exports_with_aliases
        if not name.startswith("_") or name not in internal_alias_targets
    )
    lines.extend(_format_all_block(exports_list))

    # Add model_rebuild() calls for types with forward references
    # This resolves Pydantic forward references after all types are imported
    rebuild_candidates = [
        "CreativeManifest",
        "PreviewCreativeRequest1",
        "PreviewCreativeRequest2",
    ]
    rebuild_types = [t for t in rebuild_candidates if t in all_exports]

    rebuild_lines = [
        "",
        "# Rebuild models with forward references",
        "# This must happen AFTER all imports to resolve forward reference chains",
        "",
        "# Import individual modules needed for rebuilding",
        "from adcp.types import generated_poc  # noqa: F401",
        "",
        "# Rebuild models that reference other models via forward refs",
        "# Note: only call model_rebuild() on actual classes, not Union type aliases",
    ]
    for t in rebuild_types:
        rebuild_lines.append(f"{t}.model_rebuild()")
    rebuild_lines.append("")
    lines.extend(rebuild_lines)

    return Consolidation("\n".join(lines), reachable_here, displaced)


def _format_all_block(names: list[str]) -> list[str]:
    """Render ``__all__`` for ``names``, wrapped at 100 columns."""
    lines = ["", "# Explicit exports", "__all__ = ["]
    current = "    "
    for i, name in enumerate(names):
        entry = f'"{name}"' + ("," if i < len(names) - 1 else "")
        if len(current + entry + " ") > 100 and current.strip():
            lines.append(current.rstrip())
            current = "    " + entry + " "
        else:
            current += entry + " "
    if current.strip():
        lines.append(current.rstrip())
    lines.append("]")
    lines.append("")
    return lines


def generate_disambiguated_exports(displaced: set[tuple[str, str]]) -> str:
    """Generate the module that names every variant of every colliding type.

    ``_generated`` binds one class per bare name, so an adopter who writes
    ``from adcp.types import QuerySummary`` gets whichever generated module won
    the sort order — a different class from the one the field it is reading is
    typed with. This module exports every variant of every such name under
    ``<Name>From<DottedModulePath>``, so the adopter names the class it wants.

    The export set is derived from the generated module tree. A schema addition
    that introduces another same-named class extends it with no edit here.
    """
    bindings = disambiguated_bindings(_scan_name_to_modules(), displaced)
    by_module: dict[str, list[tuple[str, str]]] = {}
    for qualified, (module_name, type_name) in bindings.items():
        by_module.setdefault(module_name, []).append((type_name, qualified))

    generation_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        '"""Unambiguous names for generated types that share a bare type name.',
        "",
        "AdCP schemas name an inline object after the property that holds it, so",
        "several generated modules legitimately define a class called ``QuerySummary``",
        "or ``Creative``. ``adcp.types`` binds one of them per name. Import from here",
        "to name the variant you want:",
        "",
        "    from adcp.types.disambiguated import QuerySummaryFromCreativeListCreativesResponse",
        "",
        "The name is ``<Type>From<DottedModulePath>`` in CamelCase, derived from the",
        "module that defines the class. Every variant of every shared name is here,",
        "including the one ``adcp.types`` binds.",
        "",
        "Auto-generated from the generated_poc module tree. DO NOT EDIT MANUALLY.",
        f"Generation date: {generation_date}",
        '"""',
        "# ruff: noqa: E501, I001",
        "from __future__ import annotations",
        "",
    ]
    for module_name in sorted(by_module):
        imported = ", ".join(
            f"{type_name} as {qualified}" for type_name, qualified in sorted(by_module[module_name])
        )
        lines.append(f"from adcp.types.generated_poc.{module_name} import {imported}")

    lines.extend(_format_all_block(sorted(bindings)))
    print(f"  disambiguated: {len(bindings)} qualified exports over {len(by_module)} modules")
    return "\n".join(lines)


def _error_details_closure() -> dict[str, list[str]]:
    """Map each generated module to the error-details names it must export.

    The set is the ``error-details/*.json`` models plus the transitive closure of
    their field types. Issue #1080 asked for the family to be importable and was
    closed by listing 16 names; a model whose field types are unreachable still
    cannot be constructed with typed values, and the list went stale on the next
    schema addition. Walking the generated package covers both.
    """
    package = importlib.import_module("adcp.types.generated_poc.error_details")
    roots: list[type] = []
    for module_info in sorted(pkgutil.iter_modules(package.__path__), key=lambda m: m.name):
        module = importlib.import_module(f"{package.__name__}.{module_info.name}")
        roots.extend(
            obj
            for name, obj in sorted(vars(module).items())
            if inspect.isclass(obj)
            and obj.__module__ == module.__name__
            and not name.startswith("_")
        )

    seen: set[type] = set()
    queue = list(roots)
    while queue:
        cls = queue.pop()
        if cls in seen:
            continue
        seen.add(cls)
        model_fields = getattr(cls, "model_fields", None)
        if not model_fields:
            continue
        for field in model_fields.values():
            pending = [field.annotation]
            while pending:
                annotation = pending.pop()
                pending.extend(get_args(annotation))
                if (
                    inspect.isclass(annotation)
                    and annotation not in seen
                    and annotation.__module__.startswith("adcp.types.generated_poc.")
                    and (hasattr(annotation, "model_fields") or issubclass(annotation, Enum))
                ):
                    queue.append(annotation)

    by_module: dict[str, list[str]] = {}
    for cls in seen:
        module_name = cls.__module__.removeprefix("adcp.types.generated_poc.")
        by_module.setdefault(module_name, []).append(cls.__name__)
    return {module: sorted(names) for module, names in sorted(by_module.items())}


def generate_error_details_exports() -> str:
    """Generate the error-details surface: the models and their field types."""
    closure = _error_details_closure()
    occurrences: dict[str, int] = {}
    for names in closure.values():
        for name in names:
            occurrences[name] = occurrences.get(name, 0) + 1

    exported: list[str] = []
    import_lines: list[str] = []
    for module_name, names in closure.items():
        imported = []
        for name in names:
            # A nested name two error-details schemas both define (``Scope`` is in
            # billing-not-supported and rate-limited) has no unambiguous bare
            # spelling, so it gets only its qualified one. Binding one of them to
            # the bare name is how the wrong class reaches a call site.
            public = name if occurrences[name] == 1 else qualified_public_name(name, module_name)
            imported.append(name if public == name else f"{name} as {public}")
            exported.append(public)
        import_lines.append(
            f"from adcp.types.generated_poc.{module_name} import {', '.join(imported)}"
        )

    generation_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        '"""The AdCP structured error-details models, with their field types.',
        "",
        "``Error.details`` is typed ``dict``, so nothing constrains what a raise site",
        "puts in it. One model per ``error-details/*.json`` schema encodes the required",
        "keys, and this module exports every one of them together with the transitive",
        "closure of their field types — the enums and nested models their annotations",
        "reference — so a seller constructs the payload with typed values:",
        "",
        "    from adcp.types.error_details import SupportedVersion, VersionUnsupportedDetails",
        "",
        "    VersionUnsupportedDetails(",
        '        adcp_version="3.2",',
        '        supported_versions=[SupportedVersion("3.1"), SupportedVersion("3.2")],',
        "    )",
        "",
        "A nested name that two error-details schemas both define carries its",
        "``<Type>From<DottedModulePath>`` name instead of a bare one.",
        "",
        "Auto-generated from the generated_poc module tree. DO NOT EDIT MANUALLY.",
        f"Generation date: {generation_date}",
        '"""',
        "# ruff: noqa: E501, I001",
        "from __future__ import annotations",
        "",
        *import_lines,
    ]
    lines.extend(_format_all_block(sorted(exported)))
    print(f"  error_details: {len(exported)} exports over {len(closure)} modules")
    return "\n".join(lines)


def preserve_generation_date_if_unchanged(previous: str, generated: str) -> str:
    """Keep the prior timestamp when regeneration changed no exported content."""
    previous_without_date = _GENERATION_DATE_RE.sub("Generation date:", previous)
    generated_without_date = _GENERATION_DATE_RE.sub("Generation date:", generated)
    if previous_without_date != generated_without_date:
        return generated

    previous_date = _GENERATION_DATE_RE.search(previous)
    if previous_date is None:
        return generated
    return _GENERATION_DATE_RE.sub(previous_date.group(0), generated, count=1)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=GENERATED_POC_DIR,
        help="generated_poc tree to consolidate",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=OUTPUT_FILE,
        help="destination for the consolidated Python module",
    )
    return parser.parse_args(argv)


def write_generated_module(path: Path, content: str) -> None:
    """Write ``content`` to ``path``, black-format it, and keep a stable date."""
    previous_content = path.read_text() if path.exists() else ""
    print(f"\nWriting {path}...")
    path.write_text(content)

    # Run black to format the generated file.
    # Try uv run first (works in the project virtualenv), then fall back to sys.executable.
    print("Formatting with black...")
    black_commands = [
        ["uv", "run", "black", str(path), "--quiet"],
        [sys.executable, "-m", "black", str(path), "--quiet"],
    ]
    formatted = False
    for cmd in black_commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode == 0:
                print("✓ Formatted with black")
                formatted = True
                break
        except FileNotFoundError:
            continue
    if not formatted:
        print("⚠ Could not format with black (not installed)")

    formatted_content = path.read_text()
    stable_content = preserve_generation_date_if_unchanged(previous_content, formatted_content)
    if stable_content != formatted_content:
        path.write_text(stable_content)


def main(argv: list[str] | None = None):
    """Generate the consolidated, disambiguated and error-details export modules."""
    global GENERATED_POC_DIR, OUTPUT_FILE

    args = _parse_args(argv)
    GENERATED_POC_DIR = args.input_dir.resolve()
    OUTPUT_FILE = args.output_file.resolve()

    print("Generating consolidated exports from generated_poc modules...")

    if not GENERATED_POC_DIR.exists():
        print(f"Error: {GENERATED_POC_DIR} does not exist")
        return 1

    consolidation = generate_consolidated_exports()

    # Build guard: a bare name defined by several modules binds one winner in
    # ``_generated``, so the others reach adopters only through their qualified
    # names in ``disambiguated``. Both sides are derived from the module tree,
    # and the guard fails when the two together leave a class reachable under no
    # name (issues #911, #1080).
    name_to_modules = _scan_name_to_modules()
    _enforce_every_class_is_reachable(
        name_to_modules,
        consolidation.reachable_here,
        disambiguated_bindings(name_to_modules, consolidation.displaced),
    )

    write_generated_module(OUTPUT_FILE, consolidation.content)
    write_generated_module(
        DISAMBIGUATED_FILE, generate_disambiguated_exports(consolidation.displaced)
    )
    write_generated_module(ERROR_DETAILS_FILE, generate_error_details_exports())

    print("✓ Successfully generated consolidated exports")
    export_count = len(
        [
            name
            for name in consolidation.content.split("__all__ = [")[1]
            .split("]")[0]
            .strip("[]")
            .split(",")
            if name.strip()
        ]
    )
    print(f"  Total exports: {export_count}")

    return 0


if __name__ == "__main__":
    exit(main())
