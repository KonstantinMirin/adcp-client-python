"""WHICH BUNDLE A TEST MODULE READS, read off the modules themselves.

``adcp-client-python-lzzj.11``: nothing stopped a test module from naming a bundle path of
its own, and 36 under ``tests/`` did.  ``tests/fresh.py`` exists to be the ONE declaration
of each bundle, and this file is the reading that reddens when a module answers that
question for itself.

**WHAT GOES WRONG, and it is not untidiness.**  The tree every check imports is emitted
from ``tests/fresh.py``'s ``BUNDLE`` -- the published 3.2 bundle with ``patch.BUILD``
applied.  A module ranging over a DIFFERENT bundle grades that tree against a different
document set, and the two measured failures are the two directions of that:

* ``adcp-client-python-fr4r``: ``tests/test_fragment_ref.py`` held the published path, the
  tree carries a module for ``core/country-code.json`` -- a document ``patches/8525``
  ADDS -- and ``inlined[ref.document]`` raised ``KeyError``.  ``adcp-client-python-lzzj.9``
  fixed two more modules of exactly that shape, which ERRORED at setup.
* ``adcp-client-python-2mli``: ``tests/test_the_compile_store.py`` asserted that the two
  live entry points resolve to the published directory, and they resolve to the patched
  one, so a check about the store's KEY failed on the bundle's IDENTITY.

Measured here: the published bundle is portable over 1,054 documents and the patched one
over 1,059, and the five only the patched one holds are documents ``patches/8525`` adds.
They are two BUNDLES, not two spellings of one.

**IT IS A READING OF VALUES AND NOT OF SOURCE, deliberately.**  The question "which bundle
does this module read" has an answer at RUN TIME, so it is answered there:
:func:`bundles_held` walks an imported module's own namespace and :func:`bundle_of` decides
whether a value NAMES A BUNDLE by asking the directory -- a directory holding the bundle's
own ``manifest.json``, ``index.json`` and ``manifest.schema.json`` is one, which is
``tests/test_one_tree_is_graded.py``'s ``checkout_of`` shape ("``pyproject.toml`` is
what makes a directory this project's root").  A scan of the SOURCE for a string literal
would assert code structure instead, and would be wrong in both directions: it would
redden on a module that spells the path and hands it straight to ``fresh``, and it would
pass a module that reaches the wrong bundle through a variable, an ``os.environ`` lookup or
a join.  ``BUNDLE = fresh.BUNDLE`` and ``BUNDLE = REPO / "schemas" / "cache" / "3.2"`` are
indistinguishable to a reader of text and are two different bundles to a reader of values.

**IN A CHILD, because the reading imports every test module.**  22.0 s warm, measured on
this box, and one of those imports holds an 842 MB compile; a worker of the parallel run
that paid both would be reading a store, not a bundle.  So the census is taken once in a
child whose only input is this file, and the parent asserts over what it printed.

**AND THE RED DIRECTION IS CONSTRUCTED** (``tests/test_one_tree_is_graded.py``'s rule: a
green direction alone is satisfied by ``assert True``).
:func:`test_the_reading_reddens_on_a_module_that_names_its_own_bundle` builds a bundle in a
temporary directory, writes a module that names it, and requires the same function this
file's green direction calls to report it.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any

import fresh
from nodeset import claimed

from codegen import bundle

HERE = Path(__file__).resolve()
TESTS = HERE.parent

#: What makes a directory a BUNDLE: the three files a bundle describes itself with.  Read
#: off the directory and not off its path, so a bundle anywhere -- the checkout, the
#: patched materialisation under the cache, a directory built in a test -- answers the same
#: way, and a directory that merely looks like a version number does not.
MARKERS = ("manifest.json", "index.json", "manifest.schema.json")

#: **The modules that read a bundle OTHER than the one the run's tree came from, each with
#: the reason it must.**  Graded in both directions: an entry that no longer reads a second
#: bundle is red here too, so the set cannot hold a stale excuse.
BY_DESIGN = {
    "test_patch_8525": (
        "patch.additions REFUSES a row whose node already states the keyword, so the "
        "override table read against the patched bundle reports itself as empty"
    ),
    "test_judgment_table": (
        "the committed verdict table is the pass over the PUBLISHED bundle; re-run against "
        "the patched one it would judge nodes the patch already annotated"
    ),
    "judgment": (
        "the derivation behind patches/8735/judgment.json, imported by survey/judgment.py, "
        "and the pass is over the published bundle for test_judgment_table's reason.  "
        "adcp-client-python-lzzj.11 calls this constant dead; it is not -- "
        "survey/judgment.py:23 imports BUNDLE from here"
    ),
    "test_a_patch_set_reaches_the_tree": (
        "the two bundles ARE its subject: it reads the published one and the patched one "
        "and asserts what the patch set moved between them"
    ),
    "test_readme_executes": (
        "the bundle path is a literal INSIDE the README's own command strings, and what "
        "this module grades is that those strings run as written"
    ),
    "test_the_second_bundle": (
        "the goal is verified against a SECOND bundle (fresh.SECOND, 3.3), which has no "
        "patched derivation: the patch sets are written against 3.2's documents"
    ),
    "test_catalogue_homes": (
        "§3a's home rule is graded as a CONSTRUCTION that must hold for ANY bundle, so the "
        "two bundles are its subject: _bundles() is {published 3.2, patch.for_build(it)} and "
        "a property read over one of them would be the census the file exists not to be"
    ),
    "test_a_bundle_states_which_upstream_it_is": (
        "every PUBLISHED bundle is its subject -- BUNDLES is provenance.bundles(), and what "
        "it grades is that each one states which upstream it came from.  A patched "
        "materialisation has no provenance file of its own and is not a delivery"
    ),
}

#: **THE OWED SET: modules still ranging over the published 3.2 bundle while the tree they
#: grade came from the patched one.**  ``adcp-client-python-lzzj.11`` owns the move and
#: states its price -- each is a one-line change that moves the input of every test in the
#: module, so each wants its own run.
#:
#: **It may only SHRINK**, and it is graded in both directions like :data:`BY_DESIGN`: a
#: module that joins it reddens by NAME, and a module that has moved and is still listed
#: reddens by name too, so the set cannot be left behind by the work.
#:
#: The cost each entry carries is reported with it rather than argued: the documents
#: ``fresh.population()`` names that the module's own bundle does not carry.
OWED = frozenset(
    {
        "cells",
        "test_a_property_that_admits_nothing",
        "test_applied_schema",
        "test_catalogue",
        "test_conj_rule_beside_a_type",
        "test_decision_set",
        "test_dump_exemptions",
        "test_emit_product",
        "test_envelope_base",
        "test_immaterial_presence",
        "test_import_rule",
        "test_inner_facts",
        "test_nested_union_sibling",
        "test_ref_branch_union",
        "test_refuses_check",
        "test_reported_drop",
        "test_required_with_no_declaration",
        "test_the_declared_backlog",
        "test_the_export_census_store",
        "test_the_run_writes_its_verdicts",
        "test_the_tree_imports",
        "test_union_disjointness",
        "test_union_dispatch",
        "test_vocabularies",
    }
)


def bundle_of(value: Any) -> Path | None:
    """The bundle a value names: itself, or its nearest ancestor holding :data:`MARKERS`.

    ``None`` for everything else, which is almost every value a module holds.  The
    ancestor walk is what makes a DOCUMENT inside a bundle answer for its bundle, so a
    module holding ``<bundle>/core/pagination-request.json`` is reported against the bundle
    it reached into and not passed over.
    """
    if not isinstance(value, (str, Path)):
        return None
    try:
        resolved = Path(value).resolve()
    except (OSError, ValueError):
        return None
    for candidate in (resolved, *resolved.parents):
        try:
            if all((candidate / marker).is_file() for marker in MARKERS):
                return candidate
        except OSError:
            return None
    return None


def bundles_held(namespace: dict[str, Any]) -> dict[str, list[str]]:
    """Every bundle an imported module's own namespace reaches, by the name holding it.

    One level into a tuple, list, set or dict, because a bundle path inside a container is
    still a bundle the module reads -- ``tests/test_readme_executes.py``'s ``BASES`` is a
    pair and would otherwise be invisible.  Dunders are skipped: ``__file__`` and
    ``__path__`` are the import system's answers and not the module's.

    **ALL of them per name and not the last one**, which is a container holding two bundles
    (``tests/test_a_bundle_states_which_upstream_it_is.py``'s ``BUNDLES`` is
    ``provenance.bundles()``, both published versions) and a reading that kept one would
    report half of what the module reaches.
    """
    found: dict[str, set[str]] = {}
    for name, value in namespace.items():
        if name.startswith("__"):
            continue
        if isinstance(value, (tuple, list, set, frozenset)):
            members: list[Any] = list(value)
        elif isinstance(value, dict):
            members = [*value.keys(), *value.values()]
        else:
            members = [value]
        for member in members:
            held = bundle_of(member)
            if held is not None:
                found.setdefault(name, set()).add(str(held))
    return {name: sorted(paths) for name, paths in found.items()}


#: What the child does: import ``tests/conftest.py`` first -- which is the binding that
#: decides which tree is graded, and the order the suite itself runs in -- then every
#: module beside it, and print each one's bundles.  It imports THIS file for the predicate
#: rather than restating it; a restated predicate would prove that a copy of the reading
#: works, which is not the claim.
_THE_CENSUS = """
import json, sys
sys.path[:0] = [{tests!r}, {repo!r}, {src!r}]
import conftest  # noqa: F401  -- the binding, and it runs before every module below
import {this} as reading
from pathlib import Path

out = {{}}
for path in sorted(Path({tests!r}).glob("*.py")):
    if path.stem in ("conftest", {this!r}):
        continue
    held = reading.bundles_held(vars(__import__(path.stem)))
    if held:
        out[path.stem] = held
print(json.dumps(out))
"""


def census() -> dict[str, dict[str, list[str]]]:
    """Every module under ``tests/`` that reaches a bundle, and which bundle, from a child.

    The child's return code is the first reading: a module that cannot be imported at all
    is reported as that rather than as an absence, which is the failure shape
    ``adcp-client-python-lzzj.9`` found (two modules ERRORED at setup) arriving one step
    earlier.
    """
    done = subprocess.run(
        [
            sys.executable,
            "-c",
            _THE_CENSUS.format(
                tests=str(TESTS), repo=str(TESTS.parent), src=str(TESTS.parent / "src"), this=HERE.stem
            ),
        ],
        capture_output=True,
        text=True,
        cwd=TESTS.parent,
        env={**os.environ, "PYTHONPATH": os.pathsep.join((str(TESTS.parent), str(TESTS.parent / "src")))},
        check=False,
    )
    assert done.returncode == 0, (
        "the census child could not import every module under tests/, so this reading "
        f"ranges over an unknown subset:\n{done.stdout[-2000:]}\n{done.stderr[-4000:]}"
    )
    return json.loads(done.stdout.splitlines()[-1])


def test_every_bundle_a_test_module_reads_is_one_tests_fresh_declares() -> None:
    """No module reaches a bundle ``tests/fresh.py`` does not declare.

    Derived on both sides, which is what makes it redden on a NAME: the left side is every
    bundle the modules actually reach, read off their own namespaces, and the right side is
    every bundle ``tests/fresh.py``'s own namespace holds -- so declaring a bundle in
    ``fresh`` permits it here and nothing else does.  A new bundle directory, a copy of one,
    a stale version, or a path assembled somewhere else all arrive as the same red.
    """
    held = census()
    reached = claimed("modules under tests/ that reach a bundle", set(held))
    declared = claimed(
        "the bundles tests/fresh.py declares",
        {path for paths in bundles_held(vars(fresh)).values() for path in paths},
    )

    foreign = sorted(
        (module, name, path)
        for module in reached
        for name, paths in held[module].items()
        for path in paths
        if path not in declared
    )
    assert not foreign, (
        "a module under tests/ reaches a bundle tests/fresh.py does not declare, so the "
        "suite has a bundle nothing owns and a reader of it grades a tree emitted from "
        f"another one; declare it in tests/fresh.py or take it from there: {foreign}\n"
        f"declared: {sorted(declared)}"
    )


def test_a_module_reading_a_bundle_other_than_the_run_s_is_named_with_its_reason() -> None:
    """The modules not on the run's own bundle are NAMED, with what each one costs.

    Both directions, which is what stops the inventory rotting: a module that starts
    reading a second bundle reddens by name, and a module that has stopped and is still
    listed reddens by name, so :data:`OWED` cannot be left behind by the work that empties
    it.  ``tests/test_import_rule.py``'s ``MODEL_LAYER_EXCEPTIONS`` is the same shape.

    The cost is reported rather than asserted: for each module, the documents the run's
    population names that the module's own bundle does not carry.  Those are the lookups
    that raise -- five of them at this writing, every one a document ``patches/8525`` adds.
    """
    held = census()
    claimed("modules under tests/ that reach a bundle", set(held))
    run_s_bundle = str(fresh.BUNDLE)
    named = claimed("the modules excused from the run's own bundle", set(BY_DESIGN) | OWED)

    elsewhere = {
        module: paths
        for module, paths in held.items()
        if module != "fresh"
        and any(path != run_s_bundle for held_paths in paths.values() for path in held_paths)
    }

    unnamed = sorted(set(elsewhere) - named)
    assert not unnamed, (
        "a module under tests/ reads a bundle other than the one the tree it grades was "
        "emitted from, and nothing names it: it will grade that tree against a different "
        "document set, which is adcp-client-python-fr4r's KeyError.  Take the bundle from "
        f"tests/fresh.py, or add it to BY_DESIGN with the reason: { {m: held[m] for m in unnamed} }"
    )

    stale = sorted(named - set(elsewhere) - {"fresh"})
    assert not stale, (
        "a module is named here as reading a second bundle and reads only the run's own, "
        "so the entry forces nothing; BY_DESIGN and OWED may only shrink, so drop it: "
        f"{stale}"
    )

    population = set(fresh.population())
    short = {
        module: sorted(population - set(bundle.portable(Path(path))))[:8]
        for module in sorted(OWED & set(elsewhere))
        for path in {p for ps in elsewhere[module].values() for p in ps} - {run_s_bundle}
    }
    assert all(short.values()), (
        "a module in OWED reads a bundle that carries every document the run's population "
        "names, so the entry records a cost it does not have and the move is free: "
        f"{sorted(module for module, missing in short.items() if not missing)}"
    )


def test_the_reading_reddens_on_a_module_that_names_its_own_bundle(tmp_path: Path) -> None:
    """The red direction, proved by construction and not by argument.

    A bundle is built in a temporary directory -- the three markers and one document, which
    is what makes a directory a bundle and nothing more -- and a module is written that
    names it.  The reading then has to find it, and the green direction's own assertion has
    to fail over it.  Two checkouts' worth of setup is avoided for
    ``tests/test_one_tree_is_graded.py``'s reason inverted: the construction here is the
    BUNDLE, so it does not depend on this box's layout either.
    """
    constructed = tmp_path / "a-bundle-no-declaration-names"
    constructed.mkdir()
    for marker in MARKERS:
        (constructed / marker).write_text("{}")
    (constructed / "core").mkdir()
    (constructed / "core" / "a-document.json").write_text('{"type": "object"}')

    module = tmp_path / "test_a_module_that_names_its_own_bundle.py"
    module.write_text(f"BUNDLE = {str(constructed)!r}\n")

    probe = textwrap.dedent(f"""
        import sys
        sys.path[:0] = [{str(tmp_path)!r}, {str(TESTS)!r}, {str(TESTS.parent)!r}]
        import {HERE.stem} as reading
        held = reading.bundles_held(vars(__import__({module.stem!r})))
        print("HELD", sorted(held.items()))
        assert held, "the reading did not see the constructed bundle at all"
        declared = {{p for ps in reading.bundles_held(vars(__import__("fresh"))).values() for p in ps}}
        reached = {{p for ps in held.values() for p in ps}}
        foreign = sorted(reached - declared)
        assert foreign == [{str(constructed)!r}], foreign
        print("REDDENED")
    """)
    ran = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True,
        text=True,
        cwd=TESTS.parent,
        env={**os.environ, "PYTHONPATH": os.pathsep.join((str(TESTS.parent), str(TESTS.parent / "src")))},
        check=False,
    )

    assert ran.returncode == 0, f"{ran.stdout[-2000:]}\n{ran.stderr[-4000:]}"
    assert "REDDENED" in ran.stdout, (
        "a module naming a bundle no declaration names was not reported, so this file's "
        f"green direction is satisfied by nothing happening: {ran.stdout!r}"
    )
