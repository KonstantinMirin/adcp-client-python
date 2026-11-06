"""§14 step 6's own gate: **the type checker IS the test** for the decision layer.

``docs/plan/architecture.md`` §14 step 6 is "Refusal as a value.  ``Refusal`` stops
subclassing ``Exception``; every handler returns ``Lowering | Refusal``; ``first_refusal``
replaces the try/except in ``lower_document``; ``lower_document`` returns a value to the
run.  **The type checker is the test.**"  §2 says what it tests: "The type checker
therefore refuses a caller that reads a ``Lowering`` field off a result without handling
the ``Refusal`` branch, which is the mechanical form of the semantics document's §9 rule
that a crash is not an outcome."

So the gate is not "the handlers were converted" -- that is what
``tests/test_import_rule.py``'s AST guard grades -- it is that NO CALLER anywhere in the
decision layer reads a decision off a result that may be a refusal.  No review and no
structural guard can say that: it is a question about every expression in 5,000 lines,
and a checker is the instrument for it.

**``mypy`` is an instrument and not a dependency**, which is why this skips rather than
fails where it is absent: the artifact this project produces is a function of the bundle
and of a PINNED compiler (D10), and a checker is in neither argument.  Where it IS
installed this is a hard gate -- the configuration it reads is ``[tool.mypy]`` in
``pyproject.toml``, which names the files and the two missing type surfaces it is allowed
not to know, so the run here and a run by hand grade the same thing.

**The second clause is what makes the first mean anything.**  A checker with every error
suppressed is green for free, so the three suppressions §14 step 6 names -- ``cast``,
``type: ignore`` and an ``assert isinstance`` standing in for a branch -- are counted over
the same files and asserted to be zero.  The third is counted by AST and not by grep,
because ``isinstance`` in an ``if`` IS the branch the design asks for and only an
``assert`` of one is the stand-in.

**THE OTHER HALF OF THIS FILE IS A DIFFERENT GATE WITH A DIFFERENT SUBJECT**, and the two
share nothing but the instrument.  ``docs/plan/final-state.md``'s reading 7 is about a
CONSUMER'S checker reading the SHIPPED PACKAGE, decided by three directions against an
environment holding only the installed wheel: correct use checks clean, a misuse of "a
field, an enum member and a constructor" reports one error per misuse, and unlinking
``py.typed`` from the INSTALLED copy makes every one of those errors vanish.  One clause
per misuse -- :func:`test_a_consumer_can_name_a_member_of_every_public_enum_the_wheel_exports`,
:func:`test_a_consumer_can_read_every_field_of_every_public_model_the_wheel_exports` and
:func:`test_a_consumer_can_construct_every_public_model_the_wheel_exports` -- each over a
population DERIVED from the domain surface rather than written down, sharing the installed
package through the ``installed`` fixture and :func:`_blind`.  Nothing about the decision
layer's own configuration reaches them: ``[tool.mypy]`` is what WE run, and
:func:`_consumer_errors` deliberately runs neither it nor our ``PYTHONPATH``.
"""

from __future__ import annotations

import ast
import collections
import contextlib
import enum
import importlib
import os
import pkgutil
import re
import shutil
import subprocess
import sys
import sysconfig
import tokenize
import tomllib
import typing
from collections.abc import Iterator
from pathlib import Path
from typing import NamedTuple

import pydantic
import pytest
from nodeset import claimed, ratchet

ROOT = Path(__file__).resolve().parents[1]

#: An inline suppression, by the spelling a checker reads: the pattern is anchored to the
#: START of a comment, which is where a checker looks for it.  ``type: ignore`` is mypy's
#: and ``pyright: ignore`` is the other checker's, named so that swapping instruments does
#: not swap which suppressions are counted.
#:
#: Anchored, and read off COMMENT TOKENS rather than off the text, because this repository
#: writes the rule down: a module explaining why it no longer carries one quotes the
#: spelling in prose, and a detector matching anywhere in a file reports the explanation
#: as the thing it forbids.  ``tokenize`` is what tells a comment from a docstring, and
#: the anchor is what tells a suppression from a sentence about one.
SUPPRESSIONS = (re.compile(r"^#\s*type:\s*ignore"), re.compile(r"^#\s*pyright:\s*ignore"))


def _graded() -> list[Path]:
    """The files ``[tool.mypy]`` ranges over, read from the configuration itself.

    Read rather than restated, so the checker's population and this test's cannot come
    apart: a row that adds a module to the gate adds it in one place.

    ``exclude`` is applied for the same reason ``files`` is read: it is the other half of
    the one statement of what the checker ranges over, and a population computed from
    ``files`` alone would report the emitted tree as graded when the checker does not
    crawl it.
    """
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())["tool"]["mypy"]
    excluded = re.compile(config["exclude"]) if "exclude" in config else None
    out: list[Path] = []
    for entry in config["files"]:
        path = ROOT / entry
        out.extend(sorted(path.rglob("*.py")) if path.is_dir() else [path])
    return [
        p
        for p in out
        if "__pycache__" not in p.parts
        and not (excluded and excluded.search(p.relative_to(ROOT).as_posix()))
    ]


#: The documented invocation's environment, and it is LOAD-BEARING rather than a
#: convenience.  mypy builds its search path from ``sys.path``, so ``src`` on
#: ``PYTHONPATH`` is what makes ``adcp.*`` resolve to this checkout -- and this is a
#: worktree whose ``.venv`` carries an editable install pointing at a DIFFERENT one, so
#: without it the package the gate reads is not the package in the tree.  Measured both
#: ways on the same commit: with it, clean over 60 files; without it, 216 errors, all of
#: them in the emitted tree that ``exclude`` keeps out of the crawl.  Set here rather than
#: inherited from however pytest was launched, so the gate's verdict is a function of the
#: tree and not of the shell.
INVOCATION = {"PYTHONPATH": f".{os.pathsep}src"}


def test_the_decision_layer_type_checks_clean() -> None:
    """§14 step 6's gate, run.

    The invocation takes no arguments: ``[tool.mypy]`` carries the file list, so the
    command here is the command a reader runs and there is no second population.

    **An absent checker is an ERROR and not a skip**, and the sentence is
    ``docs/plan/final-state.md``'s: no check is marked expected-to-fail, skipped, or
    scoped away from the code it is about.  ``mypy`` is still not a dependency and is
    still not pinned -- the artifact is a function of the bundle and of a PINNED compiler
    (D10), and a checker is in neither argument -- but a gate that disappears together
    with its own instrument REPORTS GREEN, which is the one failure mode this project
    bans everywhere else.  The two statements are compatible: the checker is not needed
    to BUILD the artifact and is needed to GRADE it, so its absence is a missing
    instrument rather than a passing run.
    """
    mypy = subprocess.run(
        [sys.executable, "-m", "mypy", "--no-incremental"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, **INVOCATION},
    )
    assert "No module named mypy" not in mypy.stderr, (
        "no type checker installed, and §14 step 6's gate IS the checker: "
        "`pip install mypy` and run `PYTHONPATH=.:src python -m mypy --no-incremental`"
    )
    assert mypy.returncode == 0, mypy.stdout + mypy.stderr


def test_the_package_declares_its_types_to_a_consumer() -> None:
    """Reading 7: "The package declares its types to a consumer's type checker."

    PEP 561 is a two-part promise and BOTH parts are read here, because either one alone
    is worse than neither: a marker in the tree that packaging drops makes the promise to
    every reader of the repository and keeps it for no consumer, and a ``package-data``
    entry naming a file that does not exist builds a wheel with nothing in it.

    **IT CHECKS THE DECLARATION AND NOT THE BEHAVIOUR, DELIBERATELY, AND IT IS THE ONLY
    CLAUSE THAT COVERS ONE OF THE TWO HALVES.**  Reading 7's behaviour is graded three
    ways below -- enum member, field and constructor, each against an installed copy with
    the marker unlinked as the control -- and reading 8's
    ``test_the_marker_reading_7_promises_is_in_the_wheel`` reads the marker out of the
    BUILT WHEEL and the installed copy, so the artifact is covered too.  Neither reaches
    ``[tool.setuptools.package-data]``: :func:`_installed` COPIES ``src/adcp``, so it
    carries the marker whatever packaging would have done with it, and the three clauses
    stay green on a tree whose wheel ships without one.  That is the hole the second
    assertion here is the only instrument for, and it is why strengthening this into a
    fourth checker run would subtract rather than add.

    What the absence costs is measured by those clauses now rather than recorded here:
    ``Skipping analyzing "adcp.types.<domain>": module is installed, but missing library
    stubs or py.typed marker``, one per domain module, and every misuse passing
    unreported.  The source tree is readable with or without the marker, which is exactly
    why the gap survived every check this suite had before them.
    """
    assert (ROOT / "src" / "adcp" / "py.typed").is_file(), (
        "PEP 561's marker is absent, so a consumer's checker resolves every annotation "
        "this compiler derives to `Any`"
    )
    declared = tomllib.loads((ROOT / "pyproject.toml").read_text())["tool"]["setuptools"][
        "package-data"
    ]
    assert "py.typed" in declared.get("adcp", ()), (
        "`py.typed` is in the tree and not in [tool.setuptools.package-data], so the "
        "wheel is built without it and the promise is made to readers alone"
    )


def _installed(into: Path) -> Path:
    """``src/adcp`` as an INSTALLED package, and the interpreter that resolves it.

    A venv with no pip (``--without-pip``, 0.2 s) and the package copied into its
    ``site-packages``, which is what a wheel unpacks to.  Returns the interpreter, because
    that is how mypy is told where to look: ``--python-executable`` makes it read THAT
    environment's ``site-packages``, so ``py.typed`` is load-bearing exactly as it is for a
    consumer.  ``MYPYPATH`` would not do -- a package found there is analysed as SOURCE
    whatever its marker says, and "the source tree is readable with or without the marker"
    is the sentence this whole section exists because of.

    ``src/adcp`` and not a fresh emit, for the reason the test above reads the same path:
    the WHEEL is built from ``src``, so that is the artifact reading 7 is about.
    ``tests/test_emit.py``'s byte compare is what ties it to a fresh run, and a check that
    re-emitted here would be grading a different artifact from the one that ships.

    IT HOLDS THE PACKAGE AND NOTHING ELSE, which is right for the two gates that import
    it -- ``tests/test_readme_executes.py`` states the consequence it works around -- and
    is NOT sufficient for a checker.  :func:`_beside_the_wheel` is the other half and the
    fixture below composes them.
    """
    subprocess.run(
        [sys.executable, "-m", "venv", "--without-pip", str(into / "v")], check=True
    )
    (site,) = (into / "v").glob("lib/python*/site-packages")
    shutil.copytree(
        ROOT / "src" / "adcp", site / "adcp", ignore=shutil.ignore_patterns("__pycache__")
    )
    assert (site / "adcp" / "py.typed").is_file()
    return into / "v" / "bin" / "python"


def _beside_the_wheel(site: Path) -> None:
    """The package's DEPENDENCIES, mirrored in beside it, as installing the wheel would.

    **WITHOUT THEM EVERY MODEL IS ``Any`` AND TWO OF READING 7'S THREE MISUSES CANNOT BE
    SEEN AT ALL.**  :func:`_installed`'s venv is built ``--without-pip`` and holds nothing,
    and the shipped classes derive from ``pydantic.BaseModel`` -- so an unresolved base
    makes the whole class ``Any`` to a checker.  Measured on this commit without this
    call: ``reveal_type`` of a public model export read ``def (*args: Any, **data: Any) ->
    Any``, ``model_dump`` read ``Any``, and a consumer file calling a constructor with a
    wrong-typed argument, an undeclared keyword AND no required arguments at all reported
    **zero errors**.  The ENUM clause survived that because a ``StrEnum`` derives from the
    standard library and needs nothing installed, which is exactly why the gap outlived
    the row that built it.  With the dependencies present the same ``reveal_type`` reads
    ``def (*, literalString: str, path: str) -> ...`` -- a synthesised ``__init__``, from
    PEP 681 ``dataclass_transform`` on pydantic's own metaclass and no plugin of ours.

    Off the environment the suite is RUNNING in, because that is where ``[project]
    dependencies`` is already resolved -- and BY SYMLINK rather than by copy, because
    nothing here writes to them (the marker :func:`_blind` unlinks belongs to the copied
    package) and a copy would be the package's 84 MB plus its closure per run.

    ``.pth`` FILES ARE THE ONE EXCLUSION AND IT IS LOAD-BEARING: this project is installed
    editable, and ``__editable__.adcp_emit-0.0.0.pth`` is one line naming this
    repository's ``src``.  Mirrored, it would put the SOURCE TREE on the consumer's path
    and ``adcp`` would resolve there instead of to the copy -- the same failure
    :func:`_consumer_errors` scrubs ``PYTHONPATH`` for, arriving by a second door.

    No assertion of its own: the misuse counts in the clauses below are its instrument,
    measured to read 1,370 of 1,453 and 0 of 1,453 with this call disabled.
    """
    held = Path(sysconfig.get_paths()["purelib"])
    for entry in sorted(held.iterdir()):
        if entry.suffix == ".pth" or entry.name.startswith(("adcp", "__pycache__")):
            continue
        link = site / entry.name
        if not link.exists() and not link.is_symlink():
            link.symlink_to(entry)


@pytest.fixture(scope="session")
def installed(tmp_path_factory: pytest.TempPathFactory) -> Iterator[tuple[Path, Path]]:
    """One installed package for every clause of reading 7, and its ``site-packages``.

    Session-scoped because :func:`_installed` copies 84 MB and the three clauses ask the
    same question of the same artifact.  The ``site-packages`` path comes out with the
    interpreter because the BLIND direction is a change to the installed copy rather than
    to the consumer's file -- see :func:`_blind`, which puts the marker back so the next
    clause does not inherit a half-dismantled package.
    """
    into = tmp_path_factory.mktemp("installed")
    interpreter = _installed(into)
    (site,) = (into / "v").glob("lib/python*/site-packages")
    _beside_the_wheel(site)
    yield interpreter, site
    shutil.rmtree(into, ignore_errors=True)


@contextlib.contextmanager
def _blind(site: Path) -> Iterator[None]:
    """The installed package with PEP 561's marker gone, and then back.

    Reading 7's third direction: "removing the marker from the *installed* package makes
    every one of those errors vanish".  RESTORED on the way out, because the package is
    shared across the clauses now -- a direction that left it blind would hand the next
    clause an environment where nothing can fail, which is the one state this section is
    built to detect.
    """
    marker = site / "adcp" / "py.typed"
    text = marker.read_bytes()
    marker.unlink()
    try:
        yield
    finally:
        marker.write_bytes(text)


def _consumer_errors(interpreter: Path, file: Path) -> list[str]:
    """Every error a consumer's checker reports IN ``file``, checked against ``interpreter``.

    ``--follow-imports=silent`` is what makes this a reading of the CONSUMER'S code, which
    is the gate ``docs/plan/architecture.md`` states -- "a checker running over a
    consumer's code does not re-check the internals of an installed package; it reads the
    package's annotations and reports errors in the consumer's own file".  Without it mypy
    crawls the generated tree and reports the internal errors that section calls "a defect
    we own and not a bar to shipping the marker", which would make this gate red for
    something it is not about.

    **THE ENVIRONMENT IS SCRUBBED, and it is as load-bearing here as ``PYTHONPATH`` is in
    the opposite direction for :data:`INVOCATION`.**  This suite runs with
    ``PYTHONPATH=.:src``, and mypy builds its search path from it -- so an inherited
    environment resolves ``adcp`` to ``src/adcp`` as SOURCE, where ``py.typed`` means
    nothing, and the gate would be reading the directory instead of the installed package.
    Measured: with the variable inherited, deleting the marker from the installed copy
    changed no answer at all.  ``cwd`` moves off the repository for the same reason --
    ``[tool.mypy]`` is the DECISION layer's configuration and names its own files and
    exclusions, which is not what a consumer runs.
    """
    done = subprocess.run(
        [
            sys.executable,
            "-m",
            "mypy",
            "--no-incremental",
            "--follow-imports=silent",
            "--python-executable",
            str(interpreter),
            str(file),
        ],
        cwd=file.parent,
        capture_output=True,
        text=True,
        check=False,
        env={k: v for k, v in os.environ.items() if k != "PYTHONPATH"},
    )
    assert "No module named mypy" not in done.stderr, done.stderr
    # ERRORS and not every line: mypy writes a ``note:`` beside an ``import-untyped``
    # pointing at its own documentation, which is advice and not a finding.
    return [
        line
        for line in done.stdout.splitlines()
        if line.startswith(f"{file.name}:") and ": error:" in line
    ]


#: An error's own code, as the checker writes it at the end of the line.  Counted by code
#: rather than matched by message, because the message is prose a checker release may
#: reword and the code is the thing its documentation is indexed by.
ERROR_CODE = re.compile(r"\[([a-z-]+)\]$")


def _codes(errors: list[str]) -> collections.Counter[str]:
    """What a consumer's checker reported, counted by its own error code."""
    counted = collections.Counter(
        found.group(1) for line in errors if (found := ERROR_CODE.search(line))
    )
    assert sum(counted.values()) == len(errors), [
        line for line in errors if not ERROR_CODE.search(line)
    ]
    return counted


def _opaque(annotation: object, seen: frozenset[int] = frozenset()) -> bool:
    """Is this annotation one a checker CANNOT refuse a wrong value for.

    ``Any`` and ``object`` accept every value, so a misuse of a field annotated with
    either reports nothing -- which is indistinguishable from the BLIND direction, the one
    reading this section exists to keep separable.  A field so annotated is therefore not
    a misusable one, and the derivation reaches past it to the model's next field rather
    than dropping the model.

    Recursive through ``typing.get_args`` because a union or a container carries the
    permissive arm inside it: ``list[Any]`` and ``str | Any`` are each as unrefusable as
    ``Any``.  ``seen`` is identity-keyed, because a schema reference can make an
    annotation hold itself.
    """
    if annotation is typing.Any or annotation is object:
        return True
    if id(annotation) in seen:
        return False
    within = seen | {id(annotation)}
    return any(_opaque(arg, within) for arg in typing.get_args(annotation))


class Surface(NamedTuple):
    """One public model export as a consumer's checker meets it.

    ``misusable`` is the first field a wrong value can be refused for, or ``None`` where
    the model has none -- see :func:`_opaque`.
    """

    fields: tuple[str, ...]
    required: tuple[str, ...]
    misusable: str | None


def _public_models() -> dict[tuple[str, str], Surface]:
    """``(domain, exported name) -> its fields``, for every PUBLIC model export with one.

    DERIVED from each domain module's own ``__all__``, for the reason
    :func:`_public_enum_members` states and derives the same way: §1 fixes the export set
    and ``emit.domain_modules`` writes it, so a model that joins the surface joins this
    population with nothing edited.  The FIELDS are read off pydantic's own
    ``model_fields`` in declaration order rather than written here.

    A model with NO field is not in the population: there is no field to read and no
    argument to pass, so both clauses below would range over it vacuously.  61 of the
    1,520 public model exports are such a model today.
    """
    import adcp.types

    out: dict[tuple[str, str], Surface] = {}
    for info in pkgutil.iter_modules(adcp.types.__path__):
        if info.ispkg or info.name.startswith("_"):
            continue
        module = importlib.import_module(f"adcp.types.{info.name}")
        for name in getattr(module, "__all__", ()):
            held = getattr(module, name, None)
            if not (isinstance(held, type) and issubclass(held, pydantic.BaseModel)):
                continue
            declared = held.model_fields
            if not declared:
                continue
            out[(info.name, name)] = Surface(
                fields=tuple(declared),
                required=tuple(f for f, spec in declared.items() if spec.is_required()),
                misusable=next(
                    (f for f, spec in declared.items() if not _opaque(spec.annotation)),
                    None,
                ),
            )
    return out


#: What the consumer file calls the type NO annotation of ours admits.  A class declared
#: in the consumer's own file, so nothing the package exports is assignable to it and
#: nothing it exports can be built from it -- which makes one misuse out of any field,
#: whatever that field's type, with no table of wrong values per annotation to go stale.
ALIEN = "class _Alien:\n    pass\n\n\n_ALIEN = _Alien()\n"


def _public_enum_members() -> dict[tuple[str, str], str]:
    """``(domain, exported name) -> one member name``, for every PUBLIC enum export.

    **DERIVED from each domain module's own ``__all__``, so it cannot go stale**: §1 fixes
    the export set and ``emit.domain_modules`` writes it, so an enumeration that joins the
    surface joins this population with nothing edited.  The MEMBER is the class's own
    first one, read off ``__members__`` -- not a name written here, which would be the
    pinned list the derivation exists to avoid.

    The domains are enumerated off ``adcp.types``' own package path rather than listed,
    for ``tests/test_the_domain_surface.py``'s reason: "a test carrying the list of
    domains would be the second place that derivation lives, and the first to go stale".
    """
    import adcp.types

    out: dict[tuple[str, str], str] = {}
    for info in pkgutil.iter_modules(adcp.types.__path__):
        if info.ispkg or info.name.startswith("_"):
            continue
        module = importlib.import_module(f"adcp.types.{info.name}")
        for name in getattr(module, "__all__", ()):
            held = getattr(module, name, None)
            if isinstance(held, type) and issubclass(held, enum.Enum) and held.__members__:
                out[(info.name, name)] = next(iter(held.__members__))
    return out


def test_a_consumer_can_name_a_member_of_every_public_enum_the_wheel_exports(
    tmp_path, installed: tuple[Path, Path]
) -> None:
    """Reading 7 at the one place it was measured to fail: an ENUM MEMBER.

    ``docs/plan/architecture.md``: "**The gate is the consumer's checker, not ours.**  A
    file outside the package that misuses a field and an enum member must FAIL a check
    against the installed wheel ... Checking our own tree proves nothing about this."
    This is the other direction of the same sentence -- a file outside the package that
    uses an enum member CORRECTLY must pass -- and it is the direction nothing held.

    **WHAT GOT PAST EVERY EXISTING GATE, which is why this one is derived.**  §3a's shared
    value list was first emitted as ``<Name> = StrEnum('<Name>', _VALUES)``, which runs
    correctly and is opaque to a checker: ``CatalogAction.CREATED`` reported ``error:
    "type[CatalogAction]" has no attribute "CREATED"  [attr-defined]``.  Nothing reddened,
    for two reasons that were each correct on their own -- our own ``[tool.mypy]``
    excludes the generated tree by name (§5: the tree is an artifact and a defect in it is
    fixed in ``render.py``), and the consumer-side reading next door was hand-written over
    a handful of names and so was blind to the other 1,951.  So the population here is
    DERIVED from each domain module's ``__all__``: **232 public enum exports over 11
    domains** today, and a new one joins with nothing edited.

    It read 242 until §1's one-path rule landed (``adcp-client-python-82m.41``), and the
    10 it lost are the measurement that matters to this test: every one was a name BOUND
    to an enumeration another position declares, and the declaring position's own export
    carries the same members -- so a name leaving the surface left no public enum member
    unnameable by a consumer's checker, which is the one way that repair could have
    broken this one.

    Three directions, because the first alone can pass for the wrong reason:

    * every public enum export's first member is NAMEABLE -- the gate;
    * a member no enumeration has is an ``[attr-defined]`` error, so the checker is
      actually reading the class and not resolving it to ``Any``;
    * and with ``py.typed`` removed from the installed copy the checker goes blind,
      which is what makes the marker the test above asserts load-bearing here too.
    """
    exported = _public_enum_members()
    claimed("public enum exports of the domain surface", exported)
    interpreter, site = installed

    lines = []
    for i, ((domain, name), member) in enumerate(sorted(exported.items())):
        lines.append(f"from adcp.types.{domain} import {name} as _{i}")
        lines.append(f"held_{i}: _{i} = _{i}.{member}")
    consumer = tmp_path / "consumer.py"
    consumer.write_text("\n".join(lines) + "\n")
    assert _consumer_errors(interpreter, consumer) == []

    # The control: a member no enumeration carries.  ``_0`` is whichever export sorts
    # first, so this names no enumeration either.
    (domain, name), _ = sorted(exported.items())[0]
    control = tmp_path / "control.py"
    control.write_text(
        f"from adcp.types.{domain} import {name}\n\nbad = {name}.NOT_A_MEMBER_ANY_RULE_MINTS\n"
    )
    reported = _consumer_errors(interpreter, control)
    assert len(reported) == 1 and "attr-defined" in reported[0], reported

    # And the marker, which is what makes the two readings above about an INSTALLED
    # package rather than about a directory of source: without it the control's error
    # becomes `import-untyped` on the module, so every annotation resolves to `Any` and
    # the misuse passes unreported.
    with _blind(site):
        blind = _consumer_errors(interpreter, control)
    assert len(blind) == 1 and "import-untyped" in blind[0], blind


def test_a_consumer_can_read_every_field_of_every_public_model_the_wheel_exports(
    tmp_path, installed: tuple[Path, Path]
) -> None:
    """Reading 7's FIELD misuse, the half ``architecture.md`` names first.

    "**The gate is the consumer's checker, not ours.**  A file outside the package that
    misuses a field and an enum member must FAIL a check against the installed wheel ...
    Checking our own tree proves nothing about this."  The enum member was gated by the
    clause above; this is the field, in the same three directions and against the same
    installed package.

    The misuse is an ASSIGNMENT and not a misspelled name, and the difference is the whole
    content of the reading.  ``src.not_a_field`` asks only whether the attribute EXISTS;
    ``held: _Alien = src.<field>`` asks what the field's TYPE is, which is the thing
    ``py.typed`` promises a consumer can use.  Measured on the same commit with the
    installed environment empty of dependencies, the two come apart exactly:
    ``not_a_field`` reported nothing at all (the class derives from an unresolved base, so
    every unknown attribute is ``Any``) while the assignment still reported ``str``.

    Three directions, and the middle one carries reading 7's "ONE ERROR PER MISUSE" as an
    exact count over the whole derived set rather than over one control -- a checker that
    stopped at the first misuse, or a configuration that collapsed them, would report a
    non-empty list and fail this.
    """
    surface = _public_models()
    claimed("public model exports of the domain surface with a field", surface)
    misusable = claimed(
        "public model exports with a field a wrong value can be refused for",
        {key: holds for key, holds in surface.items() if holds.misusable is not None},
    )
    interpreter, site = installed

    # Every field of every public model export, read by a consumer -- the gate.
    lines = [ALIEN]
    for i, (domain, name) in enumerate(sorted(surface)):
        lines.append(f"from adcp.types.{domain} import {name} as _{i}")
        lines.append(f"def _read{i}(src: _{i}) -> None:")
        lines.extend(
            f"    held_{j} = src.{field}"
            for j, field in enumerate(surface[(domain, name)].fields)
        )
    correct = tmp_path / "field_ok.py"
    correct.write_text("\n".join(lines) + "\n")
    assert _consumer_errors(interpreter, correct) == []

    # The control, one misuse per export: the field's value read as a type no annotation
    # of ours admits.
    lines = [ALIEN]
    for i, key in enumerate(sorted(misusable)):
        lines.append(f"from adcp.types.{key[0]} import {key[1]} as _{i}")
        lines.append(f"def _bad{i}(src: _{i}) -> None:")
        lines.append(f"    held: _Alien = src.{surface[key].misusable}")
    control = tmp_path / "field_bad.py"
    control.write_text("\n".join(lines) + "\n")
    reported = _consumer_errors(interpreter, control)
    assert _codes(reported) == {"assignment": len(misusable)}, _codes(reported)

    # And the marker.  The count is DERIVED and not 1 as it is for the single-module
    # control above: the notice is per installed MODULE, and this file imports from every
    # domain module that exports a model.  What matters is the other half of the equality
    # -- `assignment` is absent, so every one of the misuses above passes unreported.
    with _blind(site):
        blind = _consumer_errors(interpreter, control)
    assert _codes(blind) == {"import-untyped": len({key[0] for key in misusable})}, blind


def test_a_consumer_can_construct_every_public_model_the_wheel_exports(
    tmp_path, installed: tuple[Path, Path]
) -> None:
    """Reading 7's CONSTRUCTOR misuse, and it is the one the other two cannot see.

    These are pydantic models, so a consumer's first contact is ``Model(field=value)`` and
    the ``__init__`` signature is SYNTHESISED from the field declarations -- by PEP 681
    ``dataclass_transform`` on pydantic's own metaclass, with no plugin of ours and none of
    the consumer's.  Naming ``EnumClass.MEMBER`` exercises a class attribute and reading
    ``src.field`` exercises one too; neither reaches a model's ``__init__``, where the
    annotations either arrive as a callable contract or quietly do not.

    **A CORRECTLY-TYPED VALUE FOR EVERY FIELD COMES OFF A PARAMETER OF THE MODEL'S OWN
    TYPE**, which is what makes this derivable at all: ``def f(src: M) -> M: return
    M(a=src.a, ...)`` names a right value for every annotation without this file holding a
    table of values per type -- the table that would go stale on the first constraint
    upstream changes.

    Three directions, as the two clauses above, plus the one thing the first direction
    does NOT come out clean on.  Two RATCHETS stand where it does not, each a measured
    count with its own row, because the residue is a defect in the shipped annotations and
    not a property of this check:

    * ``adcp-client-python-82m.52`` -- 90 fields whose constructed default sits inside
      ``Annotated[...]``, which pydantic reads and PEP 681 does not, so a checker calls
      them required;
    * ``adcp-client-python-82m.53`` -- 5 exports re-declaring ``__pydantic_extra__`` as a
      bare annotation, which puts a dunder back into the synthesised ``__init__`` as a
      required keyword-only argument.

    So reading 7's first direction -- "a consumer module using the package correctly checks
    clean" -- is FALSE for 95 of the 1,459 model exports with a field, every one of them
    for a reason only a consumer's checker can see.  Stated as a ceiling rather than left
    in prose: the two rows drive it to zero and nothing may raise it.
    """
    surface = _public_models()
    claimed("public model exports of the domain surface with a field", surface)
    misusable = claimed(
        "public model exports whose constructor a wrong value can be refused by",
        {key: holds for key, holds in surface.items() if holds.misusable is not None},
    )
    interpreter, site = installed

    # Direction one: the arguments a consumer MUST name, each a value of the field's own
    # type.  Every error this reports is a `Missing named argument`, and the split below
    # is by the two causes, both ours.
    lines = [ALIEN]
    for i, key in enumerate(sorted(surface)):
        lines.append(f"from adcp.types.{key[0]} import {key[1]} as _{i}")
        lines.append(f"def _ctor{i}(src: _{i}) -> _{i}:")
        named = ", ".join(f"{f}=src.{f}" for f in surface[key].required)
        lines.append(f"    return _{i}({named})")
    correct = tmp_path / "ctor_ok.py"
    correct.write_text("\n".join(lines) + "\n")
    reported = _consumer_errors(interpreter, correct)
    # A SUBSET AND NOT AN EQUALITY, because the two rows below take this to the empty set
    # and an equality against a count would then be the thing that fails.  Anything other
    # than a missing argument is a different finding and is not ratcheted anywhere: an
    # `Unexpected keyword argument` would say our own derivation named something that is
    # not a parameter, and an `arg-type` would say `src.<field>` is not a value the field
    # accepts -- neither is reading 7 being false, it is this check being wrong.
    assert _codes(reported).keys() <= {"call-arg"}, _codes(reported)
    assert all("Missing named argument" in line for line in reported), reported
    dunder = [line for line in reported if "__pydantic_extra__" in line]
    ratchet(
        "exports demanding the __pydantic_extra__ dunder as an argument",
        len(dunder),
        at_most=5,
        because="adcp-client-python-82m.53 re-declares it with the field specifier the "
        "base carries, which takes this to zero; a new typed `additionalProperties` "
        "emitted the present way would raise it",
    )
    ratchet(
        "defaulted fields a consumer's checker reads as required",
        len(reported) - len(dunder),
        at_most=90,
        because="adcp-client-python-82m.52 emits a constructed default as the field's "
        "assigned value, which takes this to zero; a new one emitted inside "
        "`Annotated[...]` would raise it",
    )

    # Direction two, one misuse per export: a value of a type no annotation of ours admits,
    # for the first field that can refuse one.  EVERY OTHER FIELD IS NAMED CORRECTLY, so
    # the misuse is the only thing wrong with the call and the count is the reading's own
    # "one error per misuse" -- not a non-emptiness.
    lines = [ALIEN]
    for i, key in enumerate(sorted(misusable)):
        holds = surface[key]
        lines.append(f"from adcp.types.{key[0]} import {key[1]} as _{i}")
        lines.append(f"def _ctorbad{i}(src: _{i}) -> _{i}:")
        named = ", ".join(
            [f"{holds.misusable}=_ALIEN"]
            + [f"{f}=src.{f}" for f in holds.fields if f != holds.misusable]
        )
        lines.append(f"    return _{i}({named})")
    control = tmp_path / "ctor_bad.py"
    control.write_text("\n".join(lines) + "\n")
    reported = _consumer_errors(interpreter, control)
    codes = _codes(reported)
    assert codes["arg-type"] == len(misusable), codes
    # The residue is `adcp-client-python-82m.53`'s again and nothing else: every field is
    # named here, so a `Missing named argument` can only be the dunder that is not one.
    assert codes.keys() <= {"arg-type", "call-arg"}, codes
    ratchet(
        "constructor misuses whose call also demands the __pydantic_extra__ dunder",
        codes["call-arg"],
        at_most=5,
        because="adcp-client-python-82m.53 takes this to zero with the line above it",
    )

    # And the marker: the one direction that says the two above are about an INSTALLED
    # package.  `arg-type` is gone, so every one of the misuses passes unreported.
    with _blind(site):
        blind = _consumer_errors(interpreter, control)
    assert _codes(blind) == {"import-untyped": len({key[0] for key in misusable})}, blind


def test_the_decision_layer_holds_no_suppression_the_gate_would_hide() -> None:
    """The control: a clean checker over suppressed code says nothing.

    Three spellings, each one §14 step 6 names:

    * ``cast`` -- asserting a type the checker cannot see, which is how a ``Refusal``
      branch gets asserted away rather than handled.  Counted as a CALL, so the word in
      a docstring or in a comment about the rule is not a hit.
    * ``type: ignore`` / ``pyright: ignore`` -- an error declared uninteresting.
    * ``assert isinstance(...)`` -- the branch written as an assertion.  An ``if
      isinstance(...)`` is the branch the design asks for and is not counted; an
      ``assert`` of one says "this cannot be the other branch", which is the claim §9
      forbids ("a crash is not an outcome": an assertion that fails names nothing).
    """
    casts: dict[str, int] = {}
    ignores: dict[str, int] = {}
    asserted: dict[str, list[int]] = {}
    for path in _graded():
        rel = str(path.relative_to(ROOT))
        text = path.read_text()
        with path.open("rb") as handle:
            comments = [
                token.string
                for token in tokenize.tokenize(handle.readline)
                if token.type is tokenize.COMMENT
            ]
        found = sum(
            1 for comment in comments for pattern in SUPPRESSIONS if pattern.match(comment)
        )
        if found:
            ignores[rel] = found
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                named = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(
                    node.func, "id", ""
                )
                if named == "cast":
                    casts[rel] = casts.get(rel, 0) + 1
            if (
                isinstance(node, ast.Assert)
                and isinstance(node.test, ast.Call)
                and getattr(node.test.func, "id", "") == "isinstance"
            ):
                asserted.setdefault(rel, []).append(node.lineno)

    assert casts == {}, f"{casts}: §14 step 6 admits no cast over the decision layer"
    assert ignores == {}, f"{ignores}: §14 step 6 admits no inline suppression"
    assert asserted == {}, (
        f"{asserted}: an `assert isinstance` stands in for the branch §2 asks for -- a "
        "handler that may have been handed a Refusal returns it, and an assertion that "
        "it was not names no document, pointer or keyword when it fails"
    )


def test_the_gate_ranges_over_the_decision_layer_and_not_a_corner_of_it() -> None:
    """The second control: a checker over three files is green for free too.

    So the configured population is asserted to CONTAIN the layer the row is about --
    ``codegen/refusal.py``, the one dispatch, every handler under ``codegen/lower/``, the
    parser, the shared machinery and the run.  By path and not by count, because the
    handlers are a closed set (§4's node table) and a count would go stale the first time
    one is added.
    """
    graded = {str(p.relative_to(ROOT)) for p in _graded()}
    required = {
        "codegen/refusal.py",
        "codegen/compiler.py",
        "codegen/emit.py",
        "codegen/schema/parse.py",
        "codegen/schema/nodes.py",
        "codegen/lower/decide.py",
        *(
            f"codegen/lower/{m}.py"
            for m in (
                "composition",
                "const",
                "containers",
                "enum",
                "objects",
                "references",
                "rules",
                "scalars",
                "union",
            )
        ),
    }
    assert required <= graded, sorted(required - graded)


def test_the_gate_ranges_over_the_shipped_PACKAGE_and_cannot_be_narrowed_back() -> None:
    """The third control, and it is the one the configuration failed.

    ``[tool.mypy] files`` omitted ``src/adcp`` ENTIRELY while the test above asserted a
    required set naming only ``codegen`` paths -- so a guard written against exactly this
    evasion left the shipped package free to sit outside the gate, which it did.  **The
    shipped package is in scope by definition: it is the artifact every reading is
    about**, and an annotation a consumer's checker cannot be shown to read is not a
    derived type, it is a comment.

    Computed from the TREE and not restated, for the reason the ``codegen`` set gives and
    one more: a domain module per bundle domain is a closed set the bundle decides, so a
    list here would go stale the first time upstream adds a domain, and the module would
    enter the package OUTSIDE the gate -- which is the same hole one level down.

    ``src/adcp/types/_schemas`` is the one subtraction and it is not a corner of the
    package, it is the EMITTED TREE: ``architecture.md``'s "The subject of grading is a
    FRESH EMIT, never the committed tree" -- "The committed tree is an ARTIFACT, verified
    by one byte-compare, and is never the subject."  A type error in a generated module is
    a defect of ``codegen/render.py``, which IS graded here, and ``pyproject.toml``
    carries the count, the breakdown and the row that owns it rather than treating the
    exclusion as free.
    """
    graded = {str(p.relative_to(ROOT)) for p in _graded()}
    emitted = ROOT / "src" / "adcp" / "types" / "_schemas"
    required = {
        str(p.relative_to(ROOT))
        for p in (ROOT / "src" / "adcp").rglob("*.py")
        if "__pycache__" not in p.parts and emitted not in p.parents
    }
    assert required, "src/adcp holds no hand-written module, which cannot be right"
    assert required <= graded, sorted(required - graded)
