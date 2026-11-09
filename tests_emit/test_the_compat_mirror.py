"""``adcp.types.domains.*``: the compatibility mirror of the private tree, graded.

``codegen/mirror/domains.py`` is the artifact and carries the reading.  This file is the
four clauses it has to satisfy, and they fail differently, which is why there are four
tests and not one:

* **EVERY PATH THE KEPT MACHINERY IMPORTS RESOLVES.**  The population is re-derived HERE by
  AST over ``src/adcp/`` less ``src/adcp/types/`` -- module-scope ``ImportFrom`` only --
  rather than taken from a list, because a list of module paths is the one thing that goes
  stale on the first upstream release and the mirror exists precisely so that nobody keeps
  one.
* **A MIRROR NAME IS THE PRIVATE MODULE AND NOT A COPY.**  The object reached at
  ``adcp.types.domains.<domain>.<document>.<Name>`` ``is`` the object reached at
  ``adcp.types._schemas.<domain>.<document>.<Name>``.  Without this clause the mirror could
  satisfy the first by EXECUTING the private module a second time under the second name,
  which mints a second class per node with a second ``__adcp_schema__`` and an
  ``isinstance`` that is false against the class the runtime validates into.
* **THE MIRROR DECLARES NOTHING, so ``final-state.md`` reading 6 counts the same paths.**
  Reading 6 is "``from adcp.types.<domain> import <Name>`` reaches every class the tree
  declares ... at exactly one such path", and
  ``test_the_domain_surface.py::test_every_class_the_tree_declares_is_reachable_at_one_domain_path``
  is the gate on it.  The mirror is a COMPATIBILITY surface in the sense
  ``adcp.types.compat`` is one, so the gate must be TRUE OF IT rather than widened to
  tolerate it: the clause here is that nothing the mirror reaches was declared by the
  mirror, and that ``domains`` is not a domain on the compiler's export record -- which is
  the population that gate derives its paths from.
* **THE RESIDUE IS A WORD AND NEVER A PATH.**  After the mirror, a ``(module, name)`` pair
  the kept machinery writes against ``adcp.types.domains.*`` can still fail -- but only
  because the module carries a different WORD for the class (ours
  ``GetAdCPCapabilitiesResponse``, v9.6's ``GetAdcpCapabilitiesResponse``).  That is §4's
  naming decision and ``adcp-client-python-fwvm``'s to take; this clause is the boundary,
  and it stays green when that row shrinks the residue to nothing.

**WHY THE RED DIRECTION IS A SUBPROCESS AND NOT AN ARGUMENT.**  The mirror's finder is
INSERTED at the head of ``sys.meta_path``, and that is load-bearing rather than tidy: the
parent of ``adcp.types.domains.core.account`` is the module object
``adcp.types._schemas.core``, whose ``__path__`` is the REAL directory, so a ``PathFinder``
consulted first finds ``account.py`` sitting in it and executes it a second time under the
mirror name.  :func:`test_the_finder_in_front_of_the_path_finder_is_what_stops_a_second_class`
builds the arrangement in both orders and reads back how many class objects each produced,
so the ordering is a measurement and not a comment.  A process has one import system, so
each order gets its own interpreter.
"""

from __future__ import annotations

import ast
import importlib
import json
import subprocess
import sys
from pathlib import Path

import fresh
import pytest
from compiled import compiled
from nodeset import claimed

from codegen import emit, mirror

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src"

#: The private tree the mirror resolves into, and the public spelling of it.  Spelled once
#: here and read off :mod:`codegen.mirror` for the mirror's own half, so this file and the
#: artifact cannot name two different packages.
PRIVATE = "adcp.types._schemas"
MIRRORED = f"adcp.types.{mirror.PACKAGE}"


def _absolute(node: ast.ImportFrom, file: Path) -> str | None:
    """``node``'s target as an absolute dotted name, resolving ``level`` the way Python does.

    A relative import names a module without the string ``adcp.types`` appearing anywhere,
    so a reading that skipped them would under-count the population the mirror is for.
    """
    if node.level == 0:
        return node.module
    parts = file.relative_to(SRC).with_suffix("").parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
    base = parts[: len(parts) - (node.level - 1)]
    return ".".join([*base, node.module] if node.module else list(base))


def _imported() -> dict[tuple[str, str], list[str]]:
    """Every MODULE-SCOPE ``(module, name)`` the kept machinery imports from the mirror,
    with the files that write it.

    **MODULE SCOPE means executed when the file is imported** -- an ``ImportFrom`` in the
    module body or inside a top-level ``if``/``try``/``with`` -- because that is the scope
    at which one absent module takes the whole importing file and every name it carried.
    An import inside a function body fails at the call and is a different defect.

    ``src/adcp/types/`` is excluded: it is the type surface the mirror is OF, and a
    statement in it is this project's own artifact rather than something upstream wrote
    against v9.6's layout.
    """
    out: dict[tuple[str, str], list[str]] = {}
    for file in sorted(SRC.rglob("*.py")):
        if str(file).startswith(str(SRC / "adcp" / "types")):
            continue
        wanted: dict[int, ast.ImportFrom] = {}
        for statement in ast.parse(file.read_text()).body:
            if isinstance(statement, ast.ImportFrom):
                wanted[id(statement)] = statement
            elif isinstance(statement, (ast.If, ast.Try, ast.With)):
                for inner in ast.walk(statement):
                    if isinstance(inner, ast.ImportFrom):
                        wanted.setdefault(id(inner), inner)
        for node in wanted.values():
            module = _absolute(node, file)
            if module is None or not module.startswith(f"{MIRRORED}."):
                continue
            for alias in node.names:
                if alias.name != "*":
                    out.setdefault((module, alias.name), []).append(str(file.relative_to(REPO)))
    return out


@pytest.fixture(scope="module")
def imported() -> dict[tuple[str, str], list[str]]:
    """The census, read once per process."""
    assert not fresh.FAILURE, fresh.FAILURE
    return _imported()


def test_every_mirror_module_the_kept_machinery_imports_resolves(
    imported: dict[tuple[str, str], list[str]],
) -> None:
    """The clause the 91 absent modules were: every ``adcp.types.domains.*`` module the kept
    machinery names at module scope imports.

    Measured before the mirror on ``dropin/mirror``: of 1,423 module-scope ``(module, name)``
    occurrences from ``adcp.types*`` over this population, 792 resolved, and **91 distinct
    modules under ``adcp.types.domains.*`` did not exist** -- blocking 92 distinct pairs and,
    through module scope, every name the importing file carried.  All 91 had an exact
    counterpart under ``_schemas``, 91 of 91, so what was owed was a second NAME for a
    module and never a second module.

    Reported BY NAME: the question a reader of a failure asks is which path does not
    resolve, and only the list answers it.
    """
    modules = claimed("mirror modules the kept machinery imports", {m for m, _ in imported})
    absent = {}
    for module in sorted(modules):
        try:
            importlib.import_module(module)
        except Exception as raised:  # noqa: BLE001 -- the reason is what the reader wants
            absent[module] = f"{type(raised).__name__}: {raised}"
    assert absent == {}, {
        "mirror modules that do not import": absent,
        "the mapping": f"{MIRRORED}.<rest> -> {PRIVATE}.<rest>, one prefix substitution",
    }


def test_a_mirror_name_is_the_private_module_and_not_a_copy(
    imported: dict[tuple[str, str], list[str]],
) -> None:
    """**THE SAME OBJECT**, asserted over every mirrored module and every name reached
    through one.

    An alias is a NAME and never a second type, so this is the clause that says the mirror
    did not satisfy the test above by executing the private tree a second time.  It is
    asserted at two levels because the first implies the second and the second is what a
    consumer touches:

    * the MODULE bound at the mirror name ``is`` the module bound at the private name, in
      ``sys.modules`` and as an attribute -- which is the structural form of the property
      and cannot be half true;
    * and every name the kept machinery imports through a mirror module, where it resolves
      at all, ``is`` the object the private module carries under that word.

    The second is the pair-level reading, so the names that resolve at NO word are not this
    test's subject -- they are
    :func:`test_the_residue_after_the_mirror_is_a_word_and_never_a_path`'s.
    """
    modules = claimed("mirror modules the kept machinery imports", {m for m, _ in imported})
    not_the_same_module = {}
    for module in sorted(modules):
        private = f"{PRIVATE}{module[len(MIRRORED):]}"
        if importlib.import_module(module) is not importlib.import_module(private):
            not_the_same_module[module] = private
        elif sys.modules[module] is not sys.modules[private]:
            not_the_same_module[module] = f"{private} (sys.modules disagrees)"
    assert not_the_same_module == {}, {
        "mirror modules that are not the private module": not_the_same_module,
        "why it matters": "a second execution mints a second class per node, with a "
        "second __adcp_schema__ and an isinstance false against the class the runtime "
        "validates into",
    }

    pairs = claimed("names the kept machinery imports through a mirror module", set(imported))
    not_the_same_object = {}
    for module, name in sorted(pairs):
        public = importlib.import_module(module)
        private = importlib.import_module(f"{PRIVATE}{module[len(MIRRORED):]}")
        if hasattr(public, name) and getattr(public, name) is not getattr(private, name):
            not_the_same_object[f"{module}.{name}"] = "not the private module's object"
    assert not_the_same_object == {}, not_the_same_object


def test_the_mirror_declares_nothing_so_reading_6_counts_the_same_paths(
    imported: dict[tuple[str, str], list[str]],
) -> None:
    """Reading 6 is TRUE OF the mirror rather than widened to tolerate it.

    ``final-state.md`` reading 6: "``from adcp.types.<domain> import <Name>`` reaches every
    class the tree declares -- roots, union branches and aliases alike -- at exactly one
    such path."  The gate on it
    (``test_the_domain_surface.py::test_every_class_the_tree_declares_is_reachable_at_one_domain_path``)
    derives its population from the compiler's own export record, ``emit.surface``, keyed on
    the modules the run WROTE under ``_schemas``.  So the two halves of "this is a
    compatibility surface and not a second public path" are both facts and both asserted:

    * ``domains`` is not a domain on that record, so the mirror contributes no
      ``adcp.types.<domain>.<Name>`` path for the gate to count.  Asserted off the record
      and not off a list of domain names, which is where the gate reads it.
    * no class reached through a mirror module was DECLARED there: every one carries a
      ``__module__`` under ``_schemas``.  A mirror that declared its own would satisfy
      "the module resolves" and move reading 6's count of declarations, which is the
      arithmetic ``test_one_node_is_one_declaration.py`` holds.
    """
    held = compiled(fresh.BUNDLE, fresh.population())
    domains = claimed(
        "domains on the compiler's export record",
        {emit.module_domain(module) for module, exported in held.surface.items()},
    )
    assert mirror.PACKAGE not in domains, {
        "the mirror's package is a domain on the export record": mirror.PACKAGE,
        "why it matters": "reading 6's gate counts adcp.types.<domain>.<Name> paths over "
        "this set, so a mirror that joined it would be a second public path",
    }

    pairs = claimed("names the kept machinery imports through a mirror module", set(imported))
    declared_by_the_mirror = {}
    for module, name in sorted(pairs):
        found = getattr(importlib.import_module(module), name, None)
        if isinstance(found, type) and not found.__module__.startswith(f"{PRIVATE}."):
            declared_by_the_mirror[f"{module}.{name}"] = found.__module__
    assert declared_by_the_mirror == {}, {
        "classes reached through the mirror that the private tree did not declare": declared_by_the_mirror
    }


def test_the_residue_after_the_mirror_is_a_word_and_never_a_path(
    imported: dict[tuple[str, str], list[str]],
) -> None:
    """The boundary of this lane: a pair the kept machinery writes against the mirror fails
    only because the WORD differs, never because the PATH is absent.

    Measured on ``dropin/mirror`` after the mirror: 92 distinct pairs were blocked by an
    absent module and are not; 76 of them resolve, and **16 moved to the other bucket** --
    the module exists and carries the class under a different word.  All 16 are acronym
    casing or number (ours ``GetAdCPCapabilitiesResponse``, ``SIGetOfferingRequest``,
    ``MCPWebhookPayload``, ``ProductResponseFields``; v9.6's ``GetAdcpCapabilitiesResponse``,
    ``SiGetOfferingRequest``, ``McpWebhookPayload``, ``ProductResponseField``).

    §4 forbids a lane choosing a word, so those 16 are ``adcp-client-python-fwvm``'s and the
    alias layer's, not this one's.  What IS this lane's is the clause asserted here, and it
    stays green when that row shrinks the residue to nothing: **every residual failure is a
    missing name inside a module that imports**, so no file is taken down by a path.

    The residue is reported by name and never counted, so the row that fixes it does not
    have to come back and edit a literal here.
    """
    pairs = claimed("names the kept machinery imports through a mirror module", set(imported))
    blocked_by_a_path, blocked_by_a_word = {}, {}
    for module, name in sorted(pairs):
        try:
            found = importlib.import_module(module)
        except Exception as raised:  # noqa: BLE001
            blocked_by_a_path[f"{module}.{name}"] = f"{type(raised).__name__}: {raised}"
            continue
        if not hasattr(found, name):
            blocked_by_a_word[f"{module}.{name}"] = sorted(imported[(module, name)])
    assert blocked_by_a_path == {}, {
        "pairs blocked because the PATH does not resolve": blocked_by_a_path
    }
    # NOT an assertion that the other bucket is empty: §4's word decision is not this
    # lane's and the residue is reported so a reader can see it without this file
    # pretending to own it.  ``adcp-client-python-fwvm`` is where it is decided.
    if blocked_by_a_word:
        rows = "\n".join(
            f"  {pair}  <- {sorted(set(where))}"
            for pair, where in sorted(blocked_by_a_word.items())
        )
        print(
            f"\n{len(blocked_by_a_word)} pairs resolve to a module and not to a name "
            f"(adcp-client-python-fwvm's word decision):\n{rows}"
        )


#: The probe the red direction runs, in its own interpreter because a process has one
#: import system.  It builds the arrangement the mirror actually sits in -- a private
#: package with a document module one level down, and a mirror package beside it whose
#: ``__init__`` is the emitted artifact -- then imports the document through the mirror
#: name and reports how many distinct class objects the two names reached.
#:
#: ``front`` inserts the finder at the head of ``sys.meta_path``, which is what the artifact
#: does; ``back`` appends it, which is what a reader would call equivalent.
PROBE = """
import json, sys
from pathlib import Path

root = Path(sys.argv[1])
order = sys.argv[2]
sys.path.insert(0, str(root))

if order == "back":
    text = (root / "probe" / "domains" / "__init__.py").read_text()
    (root / "probe" / "domains" / "__init__.py").write_text(
        text.replace("sys.meta_path.insert(0, _Mirror())", "sys.meta_path.append(_Mirror())")
    )

import probe.domains.dom.doc as through_the_mirror
import probe._schemas.dom.doc as private

print(json.dumps({
    "order": order,
    "same module": through_the_mirror is private,
    "class objects": len({id(through_the_mirror.Subject), id(private.Subject)}),
    "mirror module name": through_the_mirror.__name__,
}))
"""


def test_the_finder_in_front_of_the_path_finder_is_what_stops_a_second_class(
    tmp_path: Path,
) -> None:
    """The ordering is a MEASUREMENT: appending the finder mints a second class object.

    The parent of a mirrored document module is the PRIVATE package object, whose
    ``__path__`` is the real directory -- so ``PathFinder``, consulted first, finds the
    document's own ``.py`` sitting there and executes it a second time under the mirror
    name.  Both orders are run here over the same tiny arrangement and the artifact's own
    text is what is perturbed, so the instrument reads the shipped file rather than a
    restatement of it.

    This is the one clause of the mirror that no assertion over the real tree can show
    failing, because the real tree is only ever imported with the artifact's own ordering.
    """
    package = tmp_path / "probe"
    (package / "_schemas" / "dom").mkdir(parents=True)
    (package / "domains").mkdir(parents=True)
    (package / "__init__.py").write_text("")
    (package / "_schemas" / "__init__.py").write_text("")
    (package / "_schemas" / "dom" / "__init__.py").write_text("")
    (package / "_schemas" / "dom" / "doc.py").write_text("class Subject:\n    pass\n")
    (package / "domains" / "__init__.py").write_text(mirror.SOURCE.read_text())
    probe = tmp_path / "probe.py"
    probe.write_text(PROBE)

    answers = {}
    for order in ("front", "back"):
        done = subprocess.run(
            [sys.executable, str(probe), str(tmp_path), order],
            capture_output=True,
            text=True,
            check=False,
        )
        assert done.returncode == 0, done.stdout + done.stderr
        answers[order] = json.loads(done.stdout.strip().splitlines()[-1])

    assert answers["front"] == {
        "order": "front",
        "same module": True,
        "class objects": 1,
        "mirror module name": "probe._schemas.dom.doc",
    }, answers["front"]
    assert answers["back"]["class objects"] == 2, {
        "the instrument resolves nothing": answers["back"],
        "expected": "PathFinder reached the private file under the mirror name and "
        "declared a second Subject",
    }
    assert answers["back"]["same module"] is False, answers["back"]


def test_the_shipped_mirror_is_the_text_the_run_writes() -> None:
    """The committed ``adcp/types/domains/__init__.py`` is what ``emit.write`` puts there,
    and it is Python.

    ``tests_emit/test_emit.py``'s byte-compare of what a run writes beside the tree against
    the checkout is the gate; this is the local clause, so a reader of this file does not
    have to go and find it -- and the ``compile`` is what says the verbatim artifact is
    still a module and not a text file that happens to be committed.
    """
    written = claimed("files the mirror writes beside the tree", set(mirror.beside()))
    for rel in sorted(written):
        text = mirror.beside()[rel]
        compile(text, rel, "exec")
        assert (REPO / "src" / "adcp" / "types" / rel).read_text() == text, rel
