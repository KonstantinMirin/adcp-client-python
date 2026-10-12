"""The adopter type-check fixtures are graded by the suite, not only by a Makefile.

WHY THIS EXISTS. ``tests/type_checks/`` is the adopter-pattern fixture set: it
encodes what a consumer of the published types is entitled to assume, and it is
the only thing in the tree that notices a public type-contract change. But
nothing ran it. ``make typecheck`` is ``mypy src/`` only; ``make typecheck-all``
does include the fixtures but is not what anyone runs while iterating; and the
fixtures were in no pytest suite at all, so no suite run could see them.

The consequence, measured: c045fe617 made ``Product.format_options`` and
``SyncCreativesRequest.creatives`` optional to match the pin, left
``canonical_override_field_types.py`` asserting the old required shape, and
shipped 4 ``mypy --strict`` errors. It merged, was reported verified, and sat in
the integrated tree THROUGH a graded baseline run — invisible, because that run
is pytest and these are mypy. The author ran ``mypy src/`` and not
``mypy --strict tests/type_checks/``: the right instrument, correctly used,
pointed at the wrong target (salesagent-8qela.87).

So the rule — a change to a public field's type or requiredness must run the
type-check fixtures — is enforced here instead of documented somewhere. The next
person to change a requiredness does not need to know it.

THE PRECEDENT is ``tests/test_canonical_removed_fields.py``, which already spawns
mypy AND pyright on snippets and asserts both refuse a removed keyword. A pytest
test that runs a type checker is established practice in this tree; this one
simply points it at the fixture directory.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_FIXTURE_DIR = _REPO_ROOT / "tests" / "type_checks"

#: Measured at d518308ea: ``mypy --strict tests/type_checks/`` reports exactly one
#: error, ``creative_asset_binding.py:82``, which asserts the readback manifest's
#: ``format_kind`` is ``str | None``. Clearing it needs ``_DeliveryCreativeManifest``
#: bound to the generated root, and binding it there makes it validate as the root's
#: UNION so a ``_DeliveryCreativeManifest`` instance is an instance of neither branch
#: class — measured, ``test_delivery_manifest_cannot_bypass_strict_input`` goes red
#: with ``type='model_type'``. That is the BranchDispatchMixin contract question,
#: tracked as salesagent-8qela.82.
#:
#: SHRINK-ONLY. This is the ratcheting-counter pattern this repo already uses, not an
#: allowlist of names: raising it admits a new, unexamined error, which is the exact
#: failure this file exists to catch. Lower it when salesagent-8qela.82 lands; never
#: raise it.
_MAX_STRICT_ERRORS = 1  # FIXME(#2255-adjacent): see salesagent-8qela.82

#: The file the single permitted error lives in. Pinned alongside the count because a
#: count alone would let a DIFFERENT error hide under the ceiling — a number is only
#: evidence for its own scope.
_EXPECTED_RESIDUAL_FILE = "creative_asset_binding.py"

_ERROR_LINE = re.compile(r"^(?P<path>[^:]+):(?P<line>\d+): error: (?P<message>.*)$")


def _fixtures() -> list[Path]:
    """Every fixture module, derived from the directory rather than listed.

    A hand-list would go stale exactly the way the gap this file closes did.
    """
    return sorted(p for p in _FIXTURE_DIR.glob("*.py") if p.name != "__init__.py")


@pytest.fixture(scope="module")
def strict_errors() -> list[tuple[str, int, str]]:
    """``mypy --strict`` over the fixture directory, as ``(file, line, message)``.

    Module-scoped: one mypy process for the whole file. Spawned the way
    ``test_canonical_removed_fields`` spawns its checkers, including ``MYPYPATH``,
    so the two tests agree about what they are grading.
    """
    result = subprocess.run(
        [sys.executable, "-m", "mypy", "--strict", str(_FIXTURE_DIR)],
        cwd=_REPO_ROOT,
        env=dict(os.environ, MYPYPATH=str(_REPO_ROOT / "src")),
        capture_output=True,
        text=True,
        timeout=600,
    )
    found = []
    for raw in result.stdout.splitlines():
        match = _ERROR_LINE.match(raw)
        if match:
            found.append((Path(match["path"]).name, int(match["line"]), match["message"]))
    assert found or "Success" in result.stdout, (
        "mypy produced neither an error line nor a success banner, so this test is "
        f"grading nothing. stdout:\n{result.stdout[-2000:]}\nstderr:\n{result.stderr[-2000:]}"
    )
    return found


def test_the_fixture_population_is_derived_and_not_empty() -> None:
    """The directory resolves, so the test below is checking something."""
    names = [p.name for p in _fixtures()]
    assert len(names) >= 40, (
        f"only {len(names)} fixture modules found under {_FIXTURE_DIR}, expected at "
        "least 40 — the directory has moved and this file no longer grades the "
        "adopter surface"
    )
    assert "canonical_override_field_types.py" in names, (
        "canonical_override_field_types.py is the module whose staleness this file "
        f"exists to catch and it is absent from the derived population: {names}"
    )


def test_the_adopter_fixtures_typecheck_under_strict(
    strict_errors: list[tuple[str, int, str]],
) -> None:
    """No NEW ``mypy --strict`` error in the adopter fixtures.

    This is the assertion c045fe617 needed and did not have. A change to a public
    field's type or requiredness that leaves a fixture asserting the old shape
    fails here, in the suite, rather than in a Makefile target nobody invoked.
    """
    unexpected = [e for e in strict_errors if e[0] != _EXPECTED_RESIDUAL_FILE]
    assert unexpected == [], (
        "mypy --strict reports errors in adopter fixtures other than the one known "
        f"residual in {_EXPECTED_RESIDUAL_FILE}:\n"
        + "\n".join(f"  {name}:{line}: {message}" for name, line, message in unexpected)
        + "\n\nThese fixtures encode what a consumer of the published types may "
        "assume. If a public type changed on purpose, update the fixture AND say in "
        "the commit why the assertion it carried is now stale. If it changed by "
        "accident, this is the regression."
    )
    assert len(strict_errors) <= _MAX_STRICT_ERRORS, (
        f"mypy --strict reports {len(strict_errors)} errors in the adopter fixtures, "
        f"over the shrink-only ceiling of {_MAX_STRICT_ERRORS}:\n"
        + "\n".join(f"  {name}:{line}: {message}" for name, line, message in strict_errors)
        + f"\n\nThe ceiling exists for one residual in {_EXPECTED_RESIDUAL_FILE} "
        "(salesagent-8qela.82). Do not raise it — a higher ceiling admits an "
        "unexamined error, which is what this file exists to prevent."
    )
    assert Counter(name for name, _, _ in strict_errors)[_EXPECTED_RESIDUAL_FILE] == len(
        strict_errors
    )
