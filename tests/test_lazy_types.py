"""Guards for the lazy type surface.

``adcp`` and ``adcp.types`` are lazy (PEP 562 ``__getattr__``):

- ``import adcp`` does not build the generated Pydantic schema graph or import
  the client / server / a2a stack.
- ``import adcp.types`` does not build the schema graph either; the graph is
  realized on first access to a type symbol.
- ``from adcp import ADCPError`` (a non-schema symbol) stays light; importing
  a schema symbol (``Product``) triggers the build.
- The curated partial modules (``adcp.types.media_buy`` etc.) are lazy facades
  over ``adcp.types`` that never touch the internal generated layer.

These tests run import-cost assertions in fresh subprocesses so a prior import
elsewhere in the suite can't mask a regression.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

SRC_TYPES = Path(__file__).parent.parent / "src" / "adcp" / "types"
# Upstream's own module paths, served from our surface by `survey/adapter_surface.py`.
# The set is derived from what upstream's kept machinery imports at module scope, and
# upstream carries no `adcp.types.seller` -- the word named no module to serve.
PARTIAL_MODULES = ("media_buy", "creative", "signals", "protocol", "buyer")


def _run(code: str) -> str:
    """Run ``code`` in a fresh interpreter; return stdout (asserts exit 0)."""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"subprocess failed:\n{result.stderr}"
    return result.stdout.strip()


# --------------------------------------------------------------------------- #
# Laziness (fresh-interpreter import cost)
# --------------------------------------------------------------------------- #


def test_import_adcp_does_not_build_schema_graph() -> None:
    """``import adcp`` must not import the generated schema graph or a2a stack."""
    out = _run(
        "import sys, adcp;"
        "heavy = [m for m in ('adcp.types._eager','adcp.types._generated',"
        "'adcp.client','adcp.testing','adcp.server','adcp.decisioning') if m in sys.modules];"
        "a2a = [m for m in sys.modules if m.startswith('a2a')];"
        "print(repr(heavy)); print(len(a2a))"
    )
    heavy, a2a_count = out.splitlines()
    assert heavy == "[]", f"import adcp eagerly loaded heavy modules: {heavy}"
    assert a2a_count == "0", "import adcp eagerly loaded the a2a stack"


def test_import_adcp_does_not_load_importlib_metadata() -> None:
    """``import adcp`` must defer ``importlib.metadata`` (the version lookup).

    ``importlib.metadata`` pulls in a sizable stdlib subtree (~15ms); the
    version is resolved lazily on first ``adcp.__version__`` access instead.
    """
    out = _run("import sys, adcp; print('importlib.metadata' in sys.modules)")
    assert out == "False", "import adcp eagerly imported importlib.metadata"


def test_version_resolves_lazily() -> None:
    """``adcp.__version__`` resolves on demand and only then loads the metadata API."""
    out = _run(
        "import sys, adcp;"
        "before = 'importlib.metadata' in sys.modules;"
        "v = adcp.__version__;"
        "print(before); print(isinstance(v, str) and len(v) > 0);"
        "print('importlib.metadata' in sys.modules)"
    )
    before, is_str, after = out.splitlines()
    assert before == "False", "metadata loaded before __version__ was accessed"
    assert is_str == "True", "__version__ should be a non-empty string"
    assert after == "True", "accessing __version__ should resolve via importlib.metadata"


def test_version_not_clobbered_by_version_submodule() -> None:
    """``adcp.__version__`` stays a string even after importing ``adcp._version``.

    Guards against the version cache being named ``_version`` (which collides
    with the ``adcp._version`` submodule and would make ``__version__`` resolve
    to the module object).
    """
    out = _run(
        "import adcp, adcp._version;"  # importing the submodule sets adcp._version
        "v = adcp.__version__;"
        "print(type(v).__name__); print(v)"
    )
    type_name, value = out.splitlines()
    assert type_name == "str", f"adcp.__version__ resolved to {type_name}, not str"
    assert value and value != "MISSING"


# Modules that cross-import other ``adcp`` modules and are realistically
# imported on their own (before ``adcp`` or each other). The eager ``import
# adcp`` used to mask import-order cycles by loading everything in a fixed
# order; under the lazy facade each must import standalone. Guards the
# webhooks <-> webhook_sender cycle (and any sibling) from regressing.
_STANDALONE_FIRST_IMPORT = [
    "adcp.webhook_sender",
    "adcp.webhooks",
    "adcp.webhook_supervisor",
    "adcp.webhook_supervisor_pg",
    "adcp.webhook_receiver",
    "adcp.simple",
    "adcp.feed_mirror",
    "adcp.client",
    "adcp.registry",
    "adcp.adagents",
    "adcp.server",
]


@pytest.mark.parametrize("module", _STANDALONE_FIRST_IMPORT)
def test_submodule_imports_standalone(module: str) -> None:
    """Each cross-importing submodule must import first in a fresh interpreter.

    A circular import only manifests when the module is imported *before* the
    module it cycles with, so each runs in its own subprocess.
    """
    result = subprocess.run(
        [sys.executable, "-c", f"import {module}"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"`import {module}` failed standalone:\n{result.stderr}"


def test_import_adcp_types_does_not_build_schema_graph() -> None:
    """``import adcp.types`` must not realize the eager graph."""
    out = _run(
        "import sys, adcp.types;"
        "print('adcp.types._eager' in sys.modules);"
        "print('adcp.types._generated' in sys.modules)"
    )
    eager, generated = out.splitlines()
    assert eager == "False" and generated == "False", out


def test_non_schema_symbol_stays_light() -> None:
    """``from adcp import ADCPError`` must not build the schema graph."""
    out = _run(
        "import sys; from adcp import ADCPError;"
        "print('adcp.types._generated' in sys.modules);"
        "print('adcp.client' in sys.modules)"
    )
    assert out.splitlines() == ["False", "False"], out


def test_schema_symbol_triggers_build() -> None:
    """Accessing a schema symbol realizes the graph — 'asking for schema symbols'.

    **The module a first access walks through is the EMITTED one.**
    ``adcp.types._generated`` was the flat internal namespace the previous
    layering routed every symbol through (``CLAUDE.md``'s import-architecture
    diagram, ``domains/`` → ``_generated`` → ``aliases`` → ``_eager``). The
    rebuild emits the tree at ``adcp.types._schemas/<domain>/<schema>.py``,
    where every class is DEFINED, and the facade resolves a name to its own
    module -- so what proves the graph was realized is the schema module that
    defines ``Product``, not a consolidation layer it no longer passes through.

    Both halves are asserted in one subprocess so the "before" is a fact of
    this interpreter rather than of the suite's import order.
    """
    out = _run(
        "import sys, adcp.types;"
        "module = 'adcp.types._schemas.core.product';"
        "print(module in sys.modules);"
        "from adcp import Product;"
        "print(module in sys.modules)"
    )
    assert out.splitlines() == ["False", "True"], out


# --------------------------------------------------------------------------- #
# Surface equivalence (every advertised name resolves)
# --------------------------------------------------------------------------- #


def test_unknown_attribute_fails_fast_without_building_graph() -> None:
    """A missing/typo'd name raises AttributeError without realizing the graph."""
    out = _run(
        "import sys, adcp.types;"
        "import pytest;"
        "exc=None;\n"
        "try:\n"
        "    adcp.types.NoSuchTypeXYZ\n"
        "except AttributeError as e:\n"
        "    exc=e\n"
        "print(exc is not None);"
        "print('adcp.types._eager' in sys.modules)"
    )
    raised, eager_loaded = out.splitlines()
    assert raised == "True", "expected AttributeError for unknown name"
    assert eager_loaded == "False", "unknown name should not build the eager graph"


def test_star_import_from_adcp_types_resolves_all() -> None:
    """``from adcp.types import *`` resolves every advertised name (no dead entries)."""
    import adcp.types

    ns: dict[str, object] = {}
    exec("from adcp.types import *", ns)  # noqa: S102
    missing = [n for n in adcp.types.__all__ if n not in ns]
    assert not missing, f"star-import did not resolve: {missing}"


def test_partial_module_names_all_resolve_via_adcp_types() -> None:
    """Each partial module exposes exactly its ``__all__``, sourced from adcp.types."""
    import importlib

    import adcp.types

    for mod_name in PARTIAL_MODULES:
        module = importlib.import_module(f"adcp.types.{mod_name}")
        assert module.__all__, f"{mod_name} has empty __all__"
        for name in module.__all__:
            assert getattr(module, name) is getattr(
                adcp.types, name
            ), f"adcp.types.{mod_name}.{name} is not the same object as adcp.types.{name}"


@pytest.mark.parametrize("mod_name", PARTIAL_MODULES)
def test_partial_modules_never_import_generated_layer(mod_name: str) -> None:
    """Partial modules must not import the internal generated layer (item 4)."""
    tree = ast.parse((SRC_TYPES / f"{mod_name}.py").read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith(
                ("adcp.types._generated", "adcp.types.domains")
            ), f"{mod_name}.py imports the internal generated layer: {node.module}"


@pytest.mark.parametrize("mod_name", PARTIAL_MODULES)
def test_partial_modules_avoid_numbered_codegen_names(mod_name: str) -> None:
    """Curated partials must not expose codegen-numbered names (e.g. ``*Response1``).

    These trailing-digit names are datamodel-code-generator artifacts that churn
    on schema regen; where a name like ``CreateMediaBuyResponse1`` is exposed, the
    curated surface should use its semantic alias (``CreateMediaBuySuccessResponse``)
    instead. They remain available on the full ``adcp.types`` surface.
    """
    import importlib
    import re

    module = importlib.import_module(f"adcp.types.{mod_name}")
    numbered = [n for n in module.__all__ if re.search(r"[A-Za-z]\d+$", n)]
    assert not numbered, (
        f"adcp.types.{mod_name} exposes codegen-numbered names {numbered}; "
        "use the semantic alias instead (these churn on schema regen)."
    )


# --------------------------------------------------------------------------- #
# Behavior preserved by the lazy facade
# --------------------------------------------------------------------------- #


def test_dir_includes_all() -> None:
    """``dir()`` covers ``__all__`` for tooling/autocomplete."""
    import adcp
    import adcp.types

    assert set(adcp.__all__) <= set(dir(adcp))
    assert set(adcp.types.__all__) <= set(dir(adcp.types))


def test_star_import_from_adcp_resolves_all() -> None:
    """``from adcp import *`` resolves every advertised name."""
    import adcp

    ns: dict[str, object] = {}
    exec("from adcp import *", ns)  # noqa: S102
    missing = [n for n in adcp.__all__ if n not in ns]
    assert not missing, f"star-import did not resolve: {missing}"


def test_a_word_with_no_document_behind_it_is_refused_with_the_reason() -> None:
    """``GeoPostalArea`` is not bound, and the refusal says where to look instead.

    There is no deprecating-alias layer in this emission: a word the walk did
    not derive from a document gets no class and no DeprecationWarning, it gets
    an ``AttributeError`` naming the domain surface. ``core/postal-area.json``'s
    fused-system branch is still there, under the name its own position derives
    (``adcp.types.core.PostalAreaWithFusedSystem``); what is gone is the word.

    What stood here asserted ``adcp.types.GeoPostalArea`` resolved to
    ``PostalArea2`` behind a warn-once-then-cache shim -- the previous
    generator's alias layer, which binds nothing now.
    """
    import adcp.types

    with pytest.raises(AttributeError) as raised:
        adcp.types.GeoPostalArea

    assert "adcp.types.<domain>" in str(raised.value)
    assert "docs/migration-from-upstream.md" in str(raised.value)
    assert "GeoPostalArea" not in vars(adcp.types)


def test_removed_v4_names_take_precedence_over_lazy() -> None:
    """Removed-in-4.0 names raise ImportError even though __getattr__ is lazy."""
    import adcp

    removed = (
        "BrandManifest",
        "FormatCategory",
        "DeliverTo",
        "PromotedProducts",
        "PromotedOfferings",
        "Pricing",
        "PackageStatus",
    )
    for name in removed:
        with pytest.raises(ImportError) as exc:
            getattr(adcp, name)
        assert "MIGRATION_v3_to_v4.md" in str(exc.value)
