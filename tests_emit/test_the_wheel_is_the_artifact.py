"""Reading 8: **the WHEEL is the artifact**, and nothing here reads the source tree.

``docs/plan/final-state.md`` reading 8:

    The wheel builds, installs into an environment that has never seen this repository,
    and every exported name imports from it.

    Until this holds, no claim about what ships is verified -- including readings 6 and
    7, which are otherwise measured against the source tree, and packaging decides which
    files a wheel contains.

    **Decided by** building, installing clean, and importing every exported name.

**WHY A COPYTREE IS NOT THIS READING, which is the gap this file closes.**
``tests/test_type_checker.py``'s ``_installed`` and ``tests/test_readme_executes.py``'s
``_consumer`` both put the package into a venv's ``site-packages`` with
``shutil.copytree(ROOT / "src" / "adcp", ...)``.  That is the right instrument for reading
7 -- PEP 561's marker is load-bearing for a checker whether the package arrived by wheel or
by copy -- and it cannot see a packaging decision AT ALL: a copytree copies whatever is in
the tree, so ``[tool.setuptools.packages.find]`` and ``[tool.setuptools.package-data]``
are unread by every check this suite had.  Those two declarations are the whole of what
decides which files ship, and reading 8's own sentence is the reason that matters:
"packaging decides which files a wheel contains."

**WHAT THE INSTALL ASSERTION IS FOR, and it is not ceremony.**  This suite runs with
``PYTHONPATH=.:src`` (``[tool.pytest.ini_options]``'s ``pythonpath``, and ``./check``'s
preamble), and the shared ``.venv`` carries an editable ``.pth`` naming
``/srv/ws/adcp-client-python/src``.  Either one makes ``import adcp`` resolve to a SOURCE
TREE inside a subprocess that inherits the environment, and then every import below passes
for free while saying nothing about the wheel.  So :func:`_probe` reads ``adcp.__file__``
and requires it under the consumer environment's own ``site-packages`` and NOT under this
repository -- and the subprocess is run with ``PYTHONPATH`` and ``VIRTUAL_ENV`` removed
rather than overwritten, because an inherited value is the leak.

**THE EXPORTED SET IS DERIVED FROM THE INSTALLED COPY and is not a list anybody wrote.**
``adcp.types.<domain>`` is reading 6's surface and each domain module carries its names as
a literal ``__all__``, written by the emitter from the run's own record -- so the installed
wheel states its own surface and this file reads it back.  One public module carries no
``__all__`` (``adcp.types.constraints``, D5's constrained types, which are
``Annotated[...]`` aliases and not classes), and for a module with no ``__all__`` the
exported names are its module-level ASSIGNMENT TARGETS, read by ``ast`` off the installed
module's own source.  That branch is a derivation and not a second list: it excludes the
names the module IMPORTS -- ``Annotated``, ``Field``, ``AnyUrl``, ``TypeVar`` are bound in
``vars()`` and are nobody's export -- which a reading of ``vars()`` cannot do.

**THE RECORDS ARE THE OTHER HALF, and they are the half a source-tree run cannot grade.**
``pyproject.toml``'s ``[tool.setuptools.package-data]`` says it in its own comment: "A
wheel without them imports and then raises on the first validation, which is the one
failure mode a test run from the source tree cannot see."  ``adcp.types._base._document``
resolves a record through ``importlib.resources.files("adcp.types._schemas")``, so the
reading is made through that resolver and not through the filesystem: every record the
wheel packages is READ and parsed, and every document a name the wheel exports names is
one of them.  A document named with no record is a class that cannot validate.

**THE OTHER DIRECTION IS MEASURED AND IS NOT EMPTY**, which is a finding and not a
tolerance: 39 of the packaged records are named by no name on the surface, every one under
``core/async-response-refs/``.  ``test_what_this_file_does_not_grade`` states that with its
members and asserts it is still non-empty, so the day it closes this file reddens rather
than quietly carrying a stale sentence.

**Nothing here asserts a code shape and nothing here is a count.**  Every assertion is a
set equality or a set difference between two derivations -- the wheel's own zip entries
against the repository's own ``git ls-files``, the exported names against what imports, the
named documents against the packaged resources -- and every set is named through
``tests/nodeset.py``'s ``claimed`` so an empty derivation fails rather than passes.

**SHOWN RED.**  ``perturb_the_wheel.sh`` is the banked evidence: it drops the
``package-data`` entry for the records, then the recursive half of its glob, then the one
for ``py.typed``, then narrows ``packages.find``, then leaks ``PYTHONPATH`` into the
consumer environment, then empties each derivation in turn -- rebuilding the wheel for
every case and requiring the matching test to redden.  It also runs the same ``py.typed``
perturbation against the two checks that COPYTREE the source tree, which stay green: that
pair of lines is the measurement of what this file adds.
"""

from __future__ import annotations

import atexit
import csv
import functools
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import pytest

from nodeset import claimed

ROOT = Path(__file__).resolve().parents[1]

#: One build per RUN and not one per test: :func:`_built` is cached per process, so the
#: whole file has to land on one worker or the suite pays the build once a worker.
pytestmark = pytest.mark.xdist_group("the_wheel")

#: The build and install commands, **as the README prints them**, so the gate and a reader
#: running the documented fence do the same thing.  ``README.md``'s "Build the wheel and
#: install it into an environment that has never seen this repository" names these three.
#:
#: ``uv`` rather than ``pip``: the project's shared ``.venv`` has no ``pip``, no
#: ``setuptools`` and no ``build`` in it (measured), because the pins are exact and the
#: build backend is resolved in an isolated environment by the builder.  ``uv`` is this
#: project's declared tool -- ``uv sync --all-extras`` is the first command in the README
#: -- and its absence FAILS here rather than skipping, which is the same choice
#: ``tests/test_type_checker.py`` makes about its own instrument and what the README says
#: happens without one.
UV = shutil.which("uv")

#: ``git`` by absolute path, because the repository's own list of the files under ``src``
#: that are the package is what :func:`test_the_wheels_payload_is_the_packages_committed_files`
#: compares the wheel against -- and ``.gitignore`` is where the build leftovers are already
#: declared, so a second ignore list here would be a second place to go stale.
GIT = shutil.which("git")


def _clean_env() -> dict[str, str]:
    """This environment with every variable that could resolve ``adcp`` to a tree REMOVED.

    ``PYTHONPATH`` carries ``.:src`` in every invocation of this suite, and ``VIRTUAL_ENV``
    names the shared ``.venv`` whose editable ``.pth`` points at the MAIN checkout's
    ``src``.  Either one resolves ``import adcp`` to a tree nobody installed, and the
    subprocess would then report green about the wrong artifact -- which is the failure
    ``tests/test_one_tree_is_graded.py`` exists for, arriving here through an inherited
    environment instead of through a ``.pth``.

    Removed and not overwritten: ``PYTHONPATH=""`` is an empty entry on ``sys.path``,
    which is the current directory on some spellings, and the current directory of a run
    of this suite is the repository.
    """
    return {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "VIRTUAL_ENV", "PYTHONHOME")}


#: What :func:`_probe` runs INSIDE the consumer environment, written to a file there.
#:
#: A string and not a module of this suite, for the reason ``tests/test_type_checker.py``
#: writes its consumer and its control the same way: the file has to be importable by an
#: interpreter that has ONLY the wheel and its declared dependencies, and anything under
#: ``tests/`` imports ``codegen`` or ``pytest``.  It prints one JSON object on stdout, so
#: the reading below is of a VALUE and not of scraped text -- an errored run is a non-zero
#: exit and unparseable output, never a green one.
PROBE = '''
"""Read the INSTALLED adcp back: where it is, what it exports, what it packages."""

import ast
import importlib
import json
import pkgutil
import sys
from importlib import resources
from pathlib import Path

import adcp
import adcp.types
from adcp.types import _base

# The provenance key, by the spelling a CONSUMER reads it at: ``_base``'s own module
# docstring names it and ``SchemaRef``'s calls it "the other class attribute a consumer
# reads".  ``_base`` exports a constant for ``__adcp_approximations__`` and none for this
# one, so the name is spelled here rather than invented as a second constant.
SCHEMA = "__adcp_schema__"

out = {}
out["file"] = str(Path(adcp.__file__).resolve())
out["sys_path"] = [str(Path(p).resolve()) for p in sys.path if p]
out["py_typed"] = (Path(adcp.__file__).parent / "py.typed").is_file()

children = sorted(m.name for m in pkgutil.iter_modules(adcp.types.__path__))
out["children"] = children
out["flat_all"] = list(getattr(adcp.types, "__all__", []) or [])

exported = {}
how = {}
origin = {}
for name in children:
    if name.startswith("_"):
        continue
    module = importlib.import_module("adcp.types." + name)
    # Where each binding came FROM, read off this module's own ``from ... import X as X``
    # statements.  A D2 alias is ``Annotated[...]`` or ``A | B``, whose ``__module__`` is
    # ``typing`` and which therefore cannot be traced to its document any other way; the
    # re-export statement is the installed artifact's own record of the declaring module.
    for node in ast.parse(Path(module.__file__).read_text()).body:
        if isinstance(node, ast.ImportFrom):
            where = "adcp.types" + ("." + node.module if node.module else "")
            for alias in node.names:
                origin[f"{name}.{alias.asname or alias.name}"] = where
    declared = getattr(module, "__all__", None)
    if declared is not None:
        exported[name] = list(declared)
        how[name] = "__all__"
        continue
    # No ``__all__``: the exports are the module-level ASSIGNMENT TARGETS, read off the
    # installed module's own source.  This excludes what the module IMPORTS, which a
    # reading of ``vars()`` cannot do.
    tree = ast.parse(Path(module.__file__).read_text())
    targets = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets += [t.id for t in node.targets if isinstance(t, ast.Name)]
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            targets.append(node.target.id)
        elif isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            targets.append(node.name)
    exported[name] = [t for t in targets if not t.startswith("_")]
    how[name] = "module-level assignment"
out["exported"] = exported
out["how"] = how
out["origin"] = origin

# **A REAL IMPORT STATEMENT, one per name**, so what is measured is the import system and
# not a ``getattr`` over a module object that is already bound.
failed = {}
documents = {}
undocumented = []
for module_name, names in exported.items():
    for one in names:
        namespace = {}
        try:
            exec(f"from adcp.types.{module_name} import {one}", namespace)
        except BaseException as error:  # noqa: BLE001 -- the payload is the report
            failed[f"adcp.types.{module_name}.{one}"] = f"{type(error).__name__}: {error}"
            continue
        obj = namespace[one]
        # THREE HOPS, and each exists because the hop before it cannot reach a whole KIND
        # of thing this tree emits (the bd memory on provenance keys measured it):
        #  1. the object's own attribute, which a pydantic model carries;
        #  2. the module the object says it came from -- an Enum member-ises class
        #     attributes, so a StrEnum subclass cannot hold the key;
        #  3. the module this domain's own ``from ... import`` statement names -- a typing
        #     alias reports ``__module__`` as ``typing`` and has no ``__dict__`` of ours,
        #     so only the re-export statement says where it was declared.
        ref = None
        for candidate in (
            obj,
            sys.modules.get(getattr(obj, "__module__", "") or ""),
            sys.modules.get(origin.get(f"{module_name}.{one}") or ""),
        ):
            try:
                ref = getattr(candidate, SCHEMA, None)
            except BaseException:  # noqa: BLE001 -- a typing alias proxies getattr
                ref = None
            if ref is not None and getattr(ref, "document", None):
                break
            ref = None
        if ref is not None:
            documents.setdefault(ref.document, []).append(
                f"adcp.types.{module_name}.{one}"
            )
        else:
            undocumented.append(f"adcp.types.{module_name}.{one}")
out["failed"] = failed
out["documents"] = sorted(documents)
out["undocumented"] = sorted(undocumented)

# **READING 10's FLAT NAMESPACE, as the import an application has already written.**  The
# loop above asks every name at the module it is DECLARED at; this asks the same names at
# ``adcp.types`` itself, which is the spelling reading 10 calls "the compatibility
# surface" and the one the word drop-in is defined by.  A real import statement per name
# for the same reason, and ``is`` beside it: a flat surface built by COPYING would resolve
# every name here and hand a consumer an object whose ``isinstance`` is false against
# every instance the runtime builds.
# THE OWED SET IS THE ALIAS MODULE'S OWN TWO STATEMENTS OF IT, not a list here: ``__all__``
# is what that module DECLARES, and ``__adcp_flat_only__`` names the ``PRESENT`` rows, which
# owe the flat spelling and owe no path there (reading 10, amended 2026-11-06).  Their
# declaring module is the mapping's value and their name of ours is the upstream word
# itself, which is what ``PRESENT`` means.
_compat = importlib.import_module("adcp.types.compat")
flat_only = dict(_compat.__adcp_flat_only__)
# **AND UPSTREAM'S OWN STATEMENT DECIDES THE FLAT WORD WHERE THEY MAKE ONE** (`y34k`).  Their
# `_eager.py` writes `Format = _canonical_creative.Format`, so the flat spelling is their
# hand-written class and the alias table's object -- `core/format.json`'s root -- keeps the
# DOMAIN spelling.  `adcp.types._restored.STATED` is that set, derived from upstream's own
# statements, and read here off the INSTALLED package so what is graded is still the
# artifact.  The identity below is then asserted against the module upstream NAMES; nothing
# is exempted from having to be one object under two spellings.
stated = {
    word: "adcp.types." + module
    for word, module in importlib.import_module("adcp.types._restored").STATED.items()
}
out["flat_stated"] = sorted(stated)
flat_owed = sorted(set(exported.get("compat", [])) | set(flat_only))
flat_resolved = []
flat_failed = {}
flat_not_identical = {}
for one in flat_owed:
    namespace = {}
    try:
        exec(f"from adcp.types import {one}", namespace)
    except BaseException as error:  # noqa: BLE001 -- the payload is the report
        flat_failed[one] = f"{type(error).__name__}: {error}"
        continue
    where = stated.get(one) or flat_only.get(one, "adcp.types.compat")
    declared = {}
    try:
        exec(f"from {where} import {one}", declared)
    except BaseException as error:  # noqa: BLE001
        flat_not_identical[one] = f"{where}.{one} does not import: {type(error).__name__}: {error}"
        continue
    if namespace[one] is not declared[one]:
        flat_not_identical[one] = f"adcp.types.{one} is not {where}.{one}"
        continue
    flat_resolved.append(one)
out["flat_owed"] = flat_owed
out["flat_only"] = sorted(flat_only)
out["flat_resolved"] = sorted(flat_resolved)
out["flat_failed"] = flat_failed
out["flat_not_identical"] = flat_not_identical
# **A ``PRESENT`` NAME MUST NOT GAIN A PATH AT THE ALIAS MODULE**, which is the other half of
# the amendment: it owes the ONE namespace an application imports from and not a second
# canonical module.
out["flat_only_also_at_compat"] = sorted(one for one in flat_only if hasattr(_compat, one))

# ``isinstance`` across the three spellings, for the models among them.  Asked of the
# INSTALLED tree because that is the artifact: a consumer's ``isinstance`` is what the
# word drop-in means operationally, and a source-tree run cannot see packaging.
#
# THE THIRD SPELLING is the domain one, and only the alias module's own ``from
# adcp.types.<domain> import <OurName> as <UpstreamName>`` statement says which name that
# is -- a D2 alias reports ``__module__`` as ``typing``, so the re-export statement is the
# installed artifact's own record of it.  Read here rather than taken from the survey
# table, because what is being graded is the artifact.
spellings = {}
for node in ast.parse(Path(_compat.__file__).read_text()).body:
    if isinstance(node, ast.ImportFrom):
        for alias in node.names:
            spellings[alias.asname or alias.name] = (node.module, alias.name)
for one, where in flat_only.items():
    spellings[one] = (where, one)
# The same re-pointing as above, for the same reason: a word upstream's own `_eager` takes
# from a restored file is that file's at the flat spelling, so the triple's third member is
# `adcp.types.<restored module>.<word>` and `isinstance` is asserted against IT.
for one, where in stated.items():
    if one in spellings:
        spellings[one] = (where, one)

flat_isinstance = {}
flat_isinstance_checked = []
flat_three_spellings = {}
for one in sorted(flat_resolved):
    at_flat = getattr(adcp.types, one)
    where, ours = spellings.get(one, (None, None))
    if where is not None:
        at_domain = getattr(importlib.import_module(where), ours)
        if at_flat is not at_domain:
            flat_isinstance[one] = f"adcp.types.{one} is not {where}.{ours}"
            continue
        flat_three_spellings[one] = f"{where}.{ours}"
    if not (isinstance(at_flat, type) and hasattr(at_flat, "model_construct")):
        continue
    fields = getattr(at_flat, "model_fields", {}) or {}
    try:
        held = at_flat.model_construct(root=None) if "root" in fields else at_flat.model_construct()
    except BaseException as error:  # noqa: BLE001
        flat_isinstance[one] = f"could not construct: {type(error).__name__}: {error}"
        continue
    if not isinstance(held, at_flat):
        flat_isinstance[one] = "an instance built through the flat name is not one of it"
        continue
    if where is not None and not isinstance(held, at_domain):
        flat_isinstance[one] = f"an instance built through adcp.types.{one} is not a {where}.{ours}"
        continue
    flat_isinstance_checked.append(one)
out["flat_isinstance"] = flat_isinstance
out["flat_isinstance_checked"] = sorted(flat_isinstance_checked)
out["flat_three_spellings"] = len(flat_three_spellings)

# Every record the wheel actually packages, found through ``importlib.resources`` -- the
# same resolver ``_base._document`` uses -- so the right-hand side of the equality below is
# a derivation and not a manifest.
root = resources.files(_base.PACKAGE)
packaged = []
stack = [(root, "")]
while stack:
    here, prefix = stack.pop()
    for entry in here.iterdir():
        name = prefix + entry.name
        if entry.is_dir():
            stack.append((entry, name + "/"))
        elif entry.name.endswith(".json"):
            packaged.append(name)
out["packaged"] = sorted(packaged)

# **EVERY PACKAGED RECORD IS READ AND PARSED**, through the resolver and not through the
# filesystem.  An entry in the zip is not a readable resource, and the first failure this
# would catch is a record shipped empty.
unreadable = {}
for document in sorted(packaged):
    try:
        resource = resources.files(_base.PACKAGE)
        for part in document.split("/"):
            resource = resource.joinpath(part)
        json.loads(resource.read_text())
    except BaseException as error:  # noqa: BLE001
        unreadable[document] = f"{type(error).__name__}: {error}"
out["unreadable"] = unreadable

print(json.dumps(out))
'''


@functools.cache
def _built() -> dict:
    """**The wheel, built and installed into an environment outside this repository.**

    Cached for the process, because the three commands are the expensive part (measured:
    about 4 s to build, 0.03 s for the venv, 0.5 s to install warm) and every test below
    reads the SAME install -- which is also the honest thing: reading 8 is one artifact,
    not one per assertion.

    **The venv is created under ``TMPDIR`` and not under the repository**, which is reading
    8's own clause "an environment that has never seen this repository".  ``tmp_path``
    would do as well; a module-scoped build cannot take a function-scoped fixture.

    **AND IT IS REMOVED AT EXIT, because one per invocation is 102 MB.**  Measured on this
    lane: 68 directories and 6.5 GB of them, on a box at 93% full -- a wheel plus a venv
    holding the installed package, kept by every run and every xdist worker.  Nothing needs
    them afterwards: every assertion below prints the NAMES it failed on, and the README's
    three-command fence is how a reader rebuilds the artifact by hand.

    Returns the parsed :data:`PROBE` output plus the wheel path and the environment root.
    """
    assert UV, (
        "`uv` is not on PATH, and it is what README.md's own fence uses to build and "
        "install the wheel: `uv build --wheel`, `uv venv`, `uv pip install`. The shared "
        ".venv carries no pip, no setuptools and no build, so there is no second route "
        "from this tree to a wheel. Install uv; this fails rather than skips for the "
        "reason tests/test_type_checker.py gives about its own instrument."
    )
    # ONE DIRECTORY PER PROCESS.  Measured: with the suite's ``-n auto`` every xdist
    # worker ran this and all but one failed, because a shared directory was being
    # rmtree'd under the others.  ``xdist_group`` keeps the tests of this file on one
    # worker; the pid is what makes a second worker -- or a second lane on this box --
    # harmless rather than a race that reads as six defects.
    where = Path(tempfile.mkdtemp(prefix=f"reading8-{os.getpid()}-"))
    atexit.register(shutil.rmtree, where, ignore_errors=True)
    # **THE BUILD DIRECTORY IS REMOVED FIRST, AND THAT IS NOT TIDINESS.**  ``setuptools``
    # stages the wheel's contents in ``build/lib`` and does not prune files it no longer
    # intends, so a second build over a CHANGED configuration packages the union of the
    # two -- and this gate was green for every packaging perturbation in
    # ``perturb_the_wheel.sh`` until this line existed, which is the "a gate that passes
    # when nothing happens is not a gate" failure arriving as a stale directory.  It is
    # the same shape as the bd memory on an untracked file making a guard green: the
    # evidence of the defect is a directory that happens to be there.
    #
    # Both are build output and both are gitignored (``build/``, ``*.egg-info/``), so
    # removing them moves nothing the repository holds -- and ``git ls-files src/`` is
    # what the payload is compared against precisely because it does not see them.
    shutil.rmtree(ROOT / "build", ignore_errors=True)
    for stale in (ROOT / "src").glob("*.egg-info"):
        shutil.rmtree(stale, ignore_errors=True)
    env = _clean_env()
    subprocess.run(
        [UV, "build", "--wheel", "--out-dir", str(where / "dist")],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    (wheel,) = sorted((where / "dist").glob("*.whl"))
    subprocess.run(
        [UV, "venv", "--python", "3.12", str(where / "consumer-venv")],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    interpreter = where / "consumer-venv" / "bin" / "python"
    subprocess.run(
        [UV, "pip", "install", "--python", str(interpreter), str(wheel)],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    probe = where / "probe.py"
    probe.write_text(PROBE)
    # ``cwd`` is the environment's own directory and NOT the repository, so a bare ``""``
    # on ``sys.path`` cannot reach ``src`` even if one arrived some other way.
    done = subprocess.run(
        [str(interpreter), str(probe)],
        cwd=where,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert done.returncode == 0, (
        f"the installed wheel's own probe exited {done.returncode}, so every reading "
        f"below is about nothing.\n--- stdout ---\n{done.stdout}\n--- stderr ---\n"
        f"{done.stderr}"
    )
    out = json.loads(done.stdout)
    out["wheel"] = str(wheel)
    out["where"] = str(where)
    return out


def _payload() -> list[str]:
    """Every entry the built wheel carries that is not ``dist-info`` metadata.

    The wheel's ``RECORD`` is what ``pip`` unpacks, so this is the artifact's own
    statement of what it contains -- read off the zip rather than off a manifest template.
    """
    with zipfile.ZipFile(_built()["wheel"]) as archive:
        return [name for name in archive.namelist() if not name.startswith("adcp_emit-") and not name.endswith("/")]


def test_the_wheel_installs_into_an_environment_that_has_never_seen_this_repository() -> None:
    """**Reading 8's first clause, and the one assertion that makes the rest mean anything.**

    Three readings, each over a leak that has actually happened in this repository:

    * ``adcp.__file__`` is under the consumer environment's own ``site-packages``.  Not
      "somewhere outside the repo": a package resolved from a third tree would satisfy that
      and be no more the wheel than the source is.
    * it is NOT under this repository at all -- ``src`` reached through ``PYTHONPATH`` or
      through the shared ``.venv``'s editable ``.pth`` is exactly how this reading passes
      for free (``tests/test_one_tree_is_graded.py``'s subject, and the bd memory on
      sibling worktrees mixing two trees).
    * no entry on the probe's ``sys.path`` is inside this repository, which is the
      direction the first two cannot see: a leaked entry that merely lost the race still
      resolves the NEXT import, and the private ``_schemas`` tree is 1,054 of those.
    """
    out = _built()
    file = Path(out["file"])
    site = claimed(
        "site-packages directories on the installed interpreter's path",
        {p for p in out["sys_path"] if p.endswith("site-packages")},
    )
    assert any(Path(p) in file.parents for p in site), (
        f"the import resolved {file}, which is under none of {sorted(site)} -- so the "
        "names below were read off something other than the installed wheel"
    )
    assert ROOT not in file.parents, (
        f"the import resolved {file}, which is INSIDE {ROOT}: PYTHONPATH or the shared "
        ".venv's editable .pth reached the source tree, and reading 8 is then being "
        "answered by the tree it is about rather than by the artifact"
    )
    leaked = sorted(p for p in out["sys_path"] if Path(p) == ROOT or ROOT in Path(p).parents)
    assert leaked == [], (
        f"the consumer interpreter's sys.path reaches this repository at {leaked}: the "
        "first import happened to win, and the next one need not"
    )


def test_every_name_the_installed_wheel_exports_imports_from_it() -> None:
    """**Reading 8's second clause: "every exported name imports from it."**

    The set is the installed copy's OWN statement of its surface -- reading 6's
    ``adcp.types.<domain>`` modules, each carrying its names as a literal ``__all__``
    written by the emitter from the run's record -- plus, for the one public module that
    declares no ``__all__``, that module's module-level assignment targets.  Named here,
    never counted: "the question a reader of a failure asks is which name can I not use,
    and only the list answers it."

    Each name is imported with a real ``from adcp.types.<module> import <Name>``
    statement inside the consumer interpreter, so what is graded is the import system
    against the installed tree.  A ``getattr`` over an already-bound module object would
    be green on a package whose submodules are unreachable.
    """
    out = _built()
    names = claimed(
        "names the installed wheel exports from adcp.types",
        {f"adcp.types.{module}.{one}" for module, exports in out["exported"].items() for one in exports},
    )
    failed = out["failed"]
    assert failed == {}, (
        f"{sorted(failed)} do not import from the installed wheel, out of "
        f"{len(names)} the wheel itself says it exports:\n"
        + "\n".join(f"  {k}: {v}" for k, v in sorted(failed.items()))
    )


def test_every_upstream_spelling_is_on_the_installed_surface() -> None:
    """**Reading 10, asked of the artifact**: the alias layer SHIPS, or it does not exist.

    ``final-state.md`` reading 10 is "decided by installing the wheel into an environment
    that has never seen this repository and resolving every name in the cross-check's
    present, renamed and relocated sets" -- which is reading 8's own environment, so the
    question is asked here, of the install :func:`_built` already made, rather than in a
    second venv built by a second file.

    **The population is ``survey/alias-surface-9.6.1.tsv``**, written by
    ``survey/alias_surface.py`` from upstream's own 9.6.1 wheel and ours, and committed --
    the generator and its output both, because the readings this layer was briefed from
    lived under ``.adcp-cache/`` and three of their four files are already gone.
    ``tests/test_the_alias_layer_is_names.py`` asks the behavioural half of the same table
    (``is`` and ``isinstance``) against the source tree; this asks whether the names are on
    the surface the INSTALLED wheel states, which packaging decides and a source-tree run
    cannot see.

    An alias that resolves only from the source tree is not shipped.  The set difference is
    both ways, because a name in the table that the wheel does not export is an unshipped
    alias and a name the wheel exports under this module that the table does not decide is
    a surface nothing derived.
    """
    out = _built()
    lines = [
        line
        for line in (ROOT / "survey" / "alias-surface-9.6.1.tsv").read_text().splitlines(True)
        if not line.startswith("#")
    ]
    owed = {
        (row["declared_at"], row["name"])
        for row in csv.DictReader(lines, delimiter="\t")
        if row["bucket"] in ("PRESENT", "RELOCATED", "RENAMED")
    }
    claimed("the upstream spellings the alias surface declares", owed)
    installed = {
        (f"adcp.types.{module}", one)
        for module, exports in out["exported"].items()
        for one in exports
    }
    unshipped = owed - installed
    assert unshipped == set(), (
        f"{len(unshipped)} of {len(owed)} upstream spellings are not on the installed "
        f"wheel's own surface, so they are not shipped:\n"
        + "\n".join(f"  {where}.{name}" for where, name in sorted(unshipped))
    )
    undecided = {
        (where, name) for where, name in installed if where == "adcp.types.compat"
    } - owed
    assert undecided == set(), (
        f"{sorted(undecided)} are exported by the installed adcp.types.compat and are "
        "decided by no row of the table, so nothing derived them"
    )


def test_every_upstream_spelling_imports_from_the_flat_namespace() -> None:
    """**Reading 10's own spelling of the compatibility surface, asked of the artifact.**

    ``final-state.md`` reading 10 names three layers and the third is
    "``adcp.types`` flat -- the compatibility surface: **an alias for every name an
    application actually imports today**, pointing at the generated class", and the
    standing goal calls the layer a DROP-IN for the v9.6 classes.  A drop-in is defined by
    the import an application has already written, so the question
    :func:`test_every_upstream_spelling_is_on_the_installed_surface` asks of
    ``adcp.types.compat`` is asked here of ``adcp.types`` itself.

    **THIS IS THE EXPERIMENT adcp-client-python-2m5.6 ASKS FOR AND NOT A SETTLED
    OBLIGATION.**  The row states three options -- MOVE the aliases here, RE-EXPORT them
    here, or amend reading 10 to name ``compat`` as the surface -- and the decision is the
    owner's.  What this grades is option (b): the aliases stay declared at ``compat`` and
    ``adcp.types.__getattr__`` reaches them, measured from an environment that has never
    seen this repository, with ``is`` beside the import so that a flat surface built by
    copying cannot read green.
    """
    out = _built()
    owed = claimed("the upstream spellings the flat namespace owes", set(out["flat_owed"]))
    claimed("the PRESENT rows the flat namespace alone carries", set(out["flat_only"]))
    assert out["flat_failed"] == {}, (
        f"{len(out['flat_failed'])} of {len(owed)} upstream spellings do not import from "
        f"the installed adcp.types, so `from adcp.types import <Name>` is not a drop-in:\n"
        + "\n".join(f"  {k}: {v}" for k, v in sorted(out["flat_failed"].items()))
    )
    assert out["flat_not_identical"] == {}, {
        "a second object wearing the flat spelling": out["flat_not_identical"],
    }
    assert out["flat_isinstance"] == {}, {
        "isinstance does not hold through the flat spelling": out["flat_isinstance"],
    }
    assert sorted(out["flat_resolved"]) == sorted(owed), {
        "resolved": len(out["flat_resolved"]),
        "owed": len(owed),
    }
    # **AND THE WORDS UPSTREAM'S OWN STATEMENT RE-POINTS ARE A REAL SET IN THE ARTIFACT**
    # (`y34k`).  Asserted non-empty and overlapping what this layer owes, so the exception
    # the two loops above make for them cannot go quiet on a wheel that stopped shipping
    # `adcp.types._restored` -- which would read green by having nothing to except.
    stated = claimed(
        "flat words upstream's own _eager takes from a restored file", set(out["flat_stated"])
    )
    assert stated, "the installed package states no such word"
    assert stated & owed, {"stated": len(stated), "owed": len(owed)}


def test_every_flat_spelling_consumer_code_writes_resolves_or_carries_a_verdict() -> None:
    """**Reading 10's denominator: what consumer code WRITES, not what the table decides.**

    ``final-state.md`` reading 10, amended 2026-11-06: "**the clause is graded over what
    consumer code actually writes, not over the table's own rows.**  A table can be
    complete against itself and leave the written import failing -- so the measurement is
    the set of flat spellings appearing in upstream's own examples, scripts and
    documentation, resolved from an environment holding only the installed wheel."

    **THIS IS THE CLAUSE THAT WAS MISSING, AND THE STATE IT WOULD HAVE CAUGHT IS TRUNK'S**:
    959 of 959 aliases resolving at ``adcp.types.compat`` from a clean venv, and 0 of the
    written flat imports resolving.  It is the same shape as the
    ``DAASTTrackerConstraintsDaastTarget`` defect one layer out -- a derivation complete
    against itself while an import fails -- which is why it is a standing gate and not a
    one-off measurement in a bead.

    **THE POPULATION IS COMMITTED** (``survey/consumer-flat-spellings-9.2.0.tsv``, written
    by ``survey/consumer_imports.py --flat-table``), because a gate reading upstream's
    checkout out of ``/srv/ws`` is a dangling pointer the moment that directory moves --
    the lesson ``survey/alias-surface-9.6.1.tsv`` is already in the repository for.

    **AND BOTH VERSIONS ARE NAMED, because they are not the same release**: the corpus is
    upstream's 9.2.0 checkout, the alias surface is derived against 9.6.1, and the two
    verdicts that exist only because of that gap -- ``NOT-ON-UPSTREAM`` and
    ``NOT-DELIBERATE-UPSTREAM`` -- say which name each covers rather than being folded into
    "absent".
    """
    out = _built()
    lines = [
        line
        for line in (ROOT / "survey" / "consumer-flat-spellings-9.2.0.tsv").read_text().splitlines(True)
        if not line.startswith("#")
    ]
    rows = list(csv.DictReader(lines, delimiter="\t"))
    written = claimed(
        "flat spellings upstream's own consumer code writes", {row["name"] for row in rows}
    )
    owed = {row["name"] for row in rows if row["verdict"] in ("PRESENT", "RELOCATED", "RENAMED")}
    refused = {row["name"]: row["verdict"] for row in rows if row["name"] not in owed}
    claimed("the flat spellings this layer owes a consumer", owed)
    resolved = set(out["flat_resolved"])
    unmet = sorted(owed - resolved)
    assert unmet == [], (
        f"{len(unmet)} of {len(owed)} flat spellings upstream's own consumer code writes do "
        f"not resolve from the installed wheel, out of {len(written)} written:\n"
        + "\n".join(f"  from adcp.types import {name}" for name in unmet)
    )
    # **A REFUSAL WITH NO REASON IS AN OVERSIGHT WEARING A VERDICT'S CLOTHES**, so every
    # name this layer does NOT resolve carries one of the declared buckets and a sentence.
    unexplained = sorted(
        row["name"] for row in rows if row["name"] in refused and not row["why"].strip()
    )
    assert unexplained == [], {"refused with no reason given": unexplained}
    # Asserted NON-EMPTY in both directions, the discipline the rest of this file uses: a
    # census where nothing is owed grades nothing, and one where nothing is refused means
    # the buckets above have gone stale rather than that the work is done.
    assert owed, "no flat spelling is owed, so this gate ranges over nothing"
    assert refused, (
        "every flat spelling consumer code writes now resolves, so the refusal buckets in "
        "survey/consumer_imports.py's FLAT_VERDICTS are dead: assert the equality "
        "owed == written and delete this sentence"
    )


def test_every_document_an_exported_name_names_is_a_record_the_wheel_packages() -> None:
    """**Packaging decides which files a wheel contains**, and these are the files.

    ``pyproject.toml``'s ``[tool.setuptools.package-data]`` states the obligation in its
    own comment: "``strict_validate`` reads the one its own class names
    (``__adcp_schema__``) to decide acceptance (D4).  A wheel without them imports and then
    raises on the first validation, which is the one failure mode a test run from the
    source tree cannot see."

    Two derivations, both made INSIDE the consumer environment:

    * the documents the exported names name, read off ``__adcp_schema__`` through the
      three-hop chain :data:`PROBE` spells out -- the object, then the module it came from,
      then the module the domain's own re-export statement names.  Three hops because each
      reaches a KIND the one before it cannot: a model carries the key, a ``StrEnum``
      cannot (an Enum member-ises class attributes), and a typing alias has neither the
      attribute nor a ``__module__`` of ours.
    * the records ``importlib.resources`` finds under ``adcp.types._schemas``, which is the
      resolver ``_base._document`` uses to validate.

    **The direction asserted is the one that is a defect**: a document an exported name
    names with no record in the wheel is a class that cannot validate.  The other direction
    is measured and is NOT empty, which ``test_what_this_file_does_not_grade`` states with
    its members -- asserting it here would be asserting a defect away.

    **And every packaged record is READ and parsed**, not merely listed: an entry in the
    zip is not a readable resource, and a record shipped empty is the failure that reading
    makes visible.
    """
    out = _built()
    named = claimed(
        "documents the names the wheel exports name through __adcp_schema__",
        out["documents"],
    )
    packaged = claimed("records the wheel packages under adcp.types._schemas", out["packaged"])
    assert out["unreadable"] == {}, (
        "the wheel packages a record the package's own resolver cannot read, so "
        "strict_validate raises on its first payload against that document:\n"
        + "\n".join(f"  {k}: {v}" for k, v in sorted(out["unreadable"].items()))
    )
    assert named - packaged == set(), (
        f"{sorted(named - packaged)} are named by a name the wheel exports and are not "
        "in the wheel: packaging dropped the record and the class cannot validate"
    )


def test_the_marker_reading_7_promises_is_in_the_wheel() -> None:
    """Reading 7's claim is about a tree nobody installs unless the marker SHIPS.

    ``tests/test_type_checker.py`` reads ``src/adcp/py.typed`` and the ``package-data``
    declaration that is supposed to carry it; this reads the file out of the built wheel
    and out of the installed copy.  The declaration and the artifact are different claims
    -- a ``package-data`` entry naming a file that does not exist builds a wheel with
    nothing in it, which is that file's own sentence -- and reading 8 is the one that
    settles which of the two a consumer gets.
    """
    assert "adcp/py.typed" in _payload(), (
        "py.typed is not in the wheel, so every annotation this compiler derives resolves "
        "to Any for a consumer's checker and reading 7 is a promise to readers of this "
        "repository alone"
    )
    assert _built()["py_typed"], (
        "py.typed is in the wheel and not in the installed package: the install dropped "
        "it, which no reading of the built archive can see"
    )


def test_the_wheels_payload_is_the_packages_committed_files() -> None:
    """**What the wheel contains against what the source tree holds**, in both directions.

    Two derivations, neither of them a list: the wheel's own zip entries minus its
    ``dist-info`` metadata, and ``git ls-files src/`` -- the REPOSITORY's statement of which
    files under ``src`` are the package.  ``git`` and not a glob with an ignore list,
    because the ignore list is already written in ``.gitignore`` and a second copy of it
    here is a second place to go stale: ``src/adcp_emit.egg-info/`` and every
    ``__pycache__`` are build leftovers by that file's own declaration, and a glob that
    forgot one would report the wheel as missing files it is right not to carry.

    The failing direction that matters is ``committed - payload``: a file the repository
    calls part of the package and packaging does not ship.  ``payload - committed`` is the
    other one and is not symmetry for its own sake -- a wheel carrying a file no checkout
    has is a wheel built from something other than this tree.
    """
    payload = claimed("entries the built wheel carries", _payload())
    listed = subprocess.run(
        [GIT, "ls-files", "src/"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()
    committed = claimed(
        "files the repository commits under src/",
        {str(Path(one).relative_to("src")) for one in listed},
    )
    assert committed - payload == set(), (
        f"{sorted(committed - payload)} are committed under src/ and are NOT in the "
        "wheel: [tool.setuptools.packages.find] or [tool.setuptools.package-data] does "
        "not reach them, and a consumer never gets them"
    )
    assert payload - committed == set(), (
        f"{sorted(payload - committed)} are in the wheel and are not committed under "
        "src/: the wheel was built over something this checkout does not hold"
    )


def test_what_this_file_does_not_grade() -> None:
    """The gaps, named with the measurement, so a green run is not read as more than it is.

    **THE EXPORTED SET IS THE WHEEL'S OWN CLAIM, not an independent one.**  A wheel whose
    ``__all__``s were all empty would pass the import clause above over an empty set --
    which is why ``claimed`` is on it, and why that is only half an answer: the set is
    non-empty, and nothing HERE says it is the surface reading 6 decided.
    ``tests/test_the_domain_surface.py`` is the check that ties the surface to the run's
    own record (``emit.surface``), over the source tree, and reading 8's own sentence says
    why that is the right division of labour: this file is what makes that reading "about
    the artifact" at all, and it is not a second implementation of it.

    **ONE PUBLIC MODULE DECLARES NO ``__all__`` AND THE CONSEQUENCE IS REPORTED HERE
    RATHER THAN REPAIRED.**  Measured on this wheel: ``adcp.types.constraints``, D5's
    constrained types.  Its names are ``Annotated[...]`` aliases, so the module-level
    assignment branch above is what exports them -- and because there is no ``__all__``,
    ``from adcp.types.constraints import *`` also hands a consumer ``Annotated``,
    ``Field``, ``AnyUrl`` and ``TypeVar``, which are pydantic's and typing's and not this
    package's surface.  That is a defect in the EMITTED module and the emitted tree is
    byte-compared against a fresh run (``tests/test_emit.py``), so it is filed
    (``adcp-client-python-p6my``'s sibling row) rather than edited here; this file's
    derivation is written so it does not depend on which way that is settled.

    **A DEPENDENCY RESOLUTION IS NOT GRADED.**  ``uv pip install`` resolves the four
    runtime dependencies ``[project]`` declares, and this file reads none of them back: a
    pin's correctness is ``pyproject.toml``'s own claim and the import clause above would
    redden if one were missing, which is the only part of it reading 8 is about.

    **A FIGURE IS NOT GRADED.**  No count appears in any assertion above; every one is a
    set equality or a set difference, for the reason
    ``tests/test_every_check_names_its_set.py`` states about a census.

    **AND TWO GAPS ARE MEASURED HERE RATHER THAN ASSERTED AWAY**, because each is a real
    finding and an assertion that they were empty would be an assertion that the finding
    does not exist:

    * **records the wheel packages that no exported name names.**  Measured on this wheel:
      every one is under ``core/async-response-refs/``, a family whose class is declared in
      the private tree and re-declared under its own domain -- so the record ships, a
      private class names it, and no name on reading 6's surface reaches it.  Filed on
      ``adcp-client-python-tjc5``.
    * **exported names for which no document can be reached at all.**  These are D5's
      constrained types (``adcp.types.constraints``, whose types belong to no document by
      decision) and the D2 aliases a ``_schemas`` module declares without a module-level
      provenance key.  For them "the record resolves" is unasked, not answered -- and that
      is the shortfall the bd memory on provenance keys names: the package ships no
      declared-name provenance dump, so a reader of the INSTALLED wheel alone cannot
      attribute every exported name to a document.

    Both are asserted NON-EMPTY, so the day either is closed this docstring reddens
    instead of going quietly stale.
    """
    out = _built()
    without = sorted(m for m, how in out["how"].items() if how != "__all__")
    # **THIS CLAUSE USED TO ASSERT ``out["flat_all"] == []`` AND THAT WAS READING 10's
    # THIRD LAYER ASSERTED AWAY** (adcp-client-python-2m5.6).  It was written off
    # ``adcp/types/__init__.py``'s own sentence "this module exports no type: a `from
    # adcp.types import PaginationRequest` would be the second path §1 forbids" -- true of
    # the SCHEMA-DERIVED surface, which is what §1 ranges over, and false of reading 10,
    # whose third layer is "``adcp.types`` flat -- the compatibility surface: an alias for
    # every name an application actually imports today".  Two readings, one namespace, and
    # the gate carried only the first, so the flat namespace was green while the drop-in
    # clause was unmet at 959 names.
    #
    # What it asserts instead is the thing that distinguishes the two: the flat namespace
    # declares NO name of its own and carries exactly the alias layer's, so a generated
    # class never acquires a second path while the import an application has already
    # written resolves.  ``test_every_upstream_spelling_imports_from_the_flat_namespace``
    # is the obligation; this is the boundary on it.
    flat = set(out["flat_all"])
    owed = set(out["flat_owed"])
    assert flat - owed == set(), (
        "adcp.types exports a name the alias layer does not decide, so it is a second "
        f"path to a generated class and not reading 10's alias: {sorted(flat - owed)}"
    )
    assert owed - flat == set(), (
        "the flat namespace does not carry every spelling the alias layer decides, so "
        f"`from adcp.types import <Name>` raises for {len(owed - flat)} of them: "
        f"{sorted(owed - flat)[:10]}"
    )
    assert out["flat_only_also_at_compat"] == [], (
        "a PRESENT name has gained a path at adcp.types.compat as well as the flat one, "
        "which is the second path to an already-resolving name reading 10 refuses: "
        f"{out['flat_only_also_at_compat']}"
    )
    assert without, (
        "every public module now declares __all__, so this docstring's measurement is "
        "stale and the module-level-assignment branch of the derivation is dead: delete "
        "it, or the derivation carries an arm nothing exercises"
    )
    unreached = set(out["packaged"]) - set(out["documents"])
    assert unreached, (
        "every packaged record is now named by an exported name, so the first gap above "
        "is closed: assert the equality in test_every_document_an_exported_name_names_"
        "is_a_record_the_wheel_packages and delete this sentence"
    )
    assert out["undocumented"], (
        "every exported name now reaches a document, so the second gap above is closed: "
        "assert that and delete this sentence"
    )


if __name__ == "__main__":  # pragma: no cover
    sys.exit(pytest.main([__file__, "-q"]))
