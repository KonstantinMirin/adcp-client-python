"""Every public types package imports first, in a fresh interpreter (#1784).

``from adcp.types.domains.formats.canonical._base import SlotsItem`` used to
raise ``ImportError`` when it was the first adcp import in a process: the domain
roots imported every schema module eagerly, so ``formats/canonical/_base.py``'s
``from ...core import <module>`` ran ``core/__init__``, which pulled in every
response union, one of which reached back into ``formats/canonical`` while
``_base`` was half built. Whether a script failed depended on which unrelated
import came first.

Nothing is imported until a MODULE is, now. ``adcp.types.domains`` is a mirror
of the module paths under ``adcp.types._schemas`` and its own docstring states
the whole of what it owes -- *"what is owed is a second NAME for a module, not a
second module"* -- so a domain root is the private package object itself, bound
in ``sys.modules`` under the second name, declaring whatever that package
declares and nothing more. These tests import each public types package first in
a fresh interpreter, which is the only way to grade an import-order defect, and
pin the behaviours the mirror has to keep.

**WHAT THE ROOTS BIND, measured.** 22 of the 24 mirrored roots are PACKAGES
whose ``__init__`` declares nothing -- a class is reached at the module that
declares it (``adcp.types.domains.core.account_ref.AccountReference``) or on the
flat surface (``adcp.types.AccountReference``), never off the package root. The
other two, ``adagents`` and ``brand``, are single-document MODULES at the top of
the tree and declare their own ``__all__``. So the name half below is derived
from the root rather than listed, and it grades 51 names across those two.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

import adcp.types.domains as domains

_FRESH = [sys.executable, "-I", "-c"]

#: The tree the mirror names a second time. One prefix substitution is the whole
#: of the mapping, so every assertion below states both spellings of one module.
_DECLARED_ROOT = "adcp.types._schemas"


def _fresh_import(statement: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*_FRESH, statement + "\nprint('imported')"],
        capture_output=True,
        text=True,
        check=False,
        timeout=600,
    )


@pytest.mark.parametrize(
    "statement",
    [
        "from adcp.types.domains.formats.canonical._base import SlotsItem",
        "import adcp.types.domains.formats.canonical",
        "import adcp.types; from adcp.types.domains.formats.canonical._base import SlotsItem",
        "from adcp.types.domains.core import error; error.Error",
        "from adcp.types.domains.creative.list_creative_formats_response import "
        "ListCreativeFormatsResponseCreativeAgent",
    ],
)
def test_the_reported_entry_points_import_first(statement: str) -> None:
    """#1784's own entry points, at the names the documents give them.

    ``formats/canonical/_base.json`` states ``slots`` and the compiler names its
    item ``SlotsItem`` (rebuild-plan §4 Names: ``<Property>Item`` for an array
    element), declared in the module the document compiles to. The reported
    import was spelled ``from adcp.types.domains.formats import Slot`` -- a
    class read off a PACKAGE root, which is the previous generator's eager-root
    surface and not something a mirror of module paths ever answered.
    """
    result = _fresh_import(statement)
    assert result.returncode == 0, result.stderr[-2000:]
    assert result.stdout.strip() == "imported"


@pytest.mark.parametrize("domain", domains.mirrored())
def test_each_domain_root_imports_first_and_is_the_module_it_mirrors(domain: str) -> None:
    """The root imports first, and resolves to the module it is a second name for.

    Identity is the mirror's load-bearing claim: a loader that executed the
    package a second time under the mirror name would mint a second class for
    every node of every document below it, with an ``isinstance`` false against
    the class the runtime validates into. It is asserted here in the fresh
    interpreter, where a mis-ordered import would be what broke it.
    """
    statement = (
        "import sys\n"
        f"import adcp.types.domains.{domain} as root\n"
        f"import {_DECLARED_ROOT}.{domain} as declared\n"
        "assert root is declared, (root, declared)\n"
        f"assert sys.modules['adcp.types.domains.{domain}'] is declared\n"
        "for name in getattr(root, '__all__', ()):\n"
        "    getattr(root, name)\n"
        "assert not hasattr(root, 'NoSuchName')"
    )
    result = _fresh_import(statement)
    assert result.returncode == 0, result.stderr[-2000:]


def test_a_domain_root_imports_no_schema_module_and_one_module_pulls_in_no_sibling() -> None:
    """#1784 stated as what is in ``sys.modules``, which is what the defect was.

    Importing the root brings in nothing below it; importing ONE module brings
    in that module and its own ``$ref`` closure, and not the rest of the domain.
    ``core/format.json`` is the sibling the eager root used to drag in.
    """
    statement = (
        "import sys\n"
        "import adcp.types.domains.core as core\n"
        f"before = {{m for m in sys.modules if m.startswith('{_DECLARED_ROOT}.core.')}}\n"
        "assert before == set(), sorted(before)[:5]\n"
        "import adcp.types.domains.core.account_ref\n"
        f"after = {{m for m in sys.modules if m.startswith('{_DECLARED_ROOT}.core.')}}\n"
        f"assert '{_DECLARED_ROOT}.core.account_ref' in after\n"
        f"assert '{_DECLARED_ROOT}.core.format' not in after, "
        "'importing one module imported the domain'"
    )
    result = _fresh_import(statement)
    assert result.returncode == 0, result.stderr[-2000:]


def test_a_name_reached_through_the_mirror_is_the_declaring_modules_object() -> None:
    """Both spellings reach one module, and that module's class is one class.

    Stated as identity rather than as a ``sys.modules`` entry: the mirror name
    is registered when the import system is ASKED for it, and a process that
    already holds ``adcp.types._schemas.core`` reaches ``account_ref`` as an
    attribute of the package the mirror root IS, with no import at all.
    """
    from adcp.types.domains.core import account_ref as mirrored

    from adcp.types._schemas.core import account_ref as declared

    assert mirrored is declared
    assert mirrored.AccountReference is declared.AccountReference
