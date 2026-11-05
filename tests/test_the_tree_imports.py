"""The two halves of "a check may not be downstream of its own precondition".

``docs/plan/architecture.md`` (2026-10-29) decides both, and this file exists because
neither can live where the obligation lived:

    `tests/test_emit.py`'s `test_every_module_of_the_tree_imports_and_every_class_of_it_is_defined`
    is the obligation that an emitted tree builds, and its docstring names the failure
    mode it missed.  It could not run, for two independent reasons, and both are
    structural:

    * it lives in the file whose COLLECTION the defect disables -- ``graded()`` imports
      the tree at parametrize time, so an unimportable module errors the check that
      exists to report it;
    * its population is ``emit.TREE``, the COMMITTED tree, so a document absent from
      ``src/`` is invisible.  That is how the second of the two sites hid entirely.

    **A check whose precondition is the thing it checks is not a check.**  The import
    obligation ranges over the tree a fresh run EMITS, not the one committed, and it
    lives outside the module whose collection it would gate.  Both halves are required:
    fixing the population alone leaves it uncollectable, and moving the file alone
    leaves it blind to anything not yet committed.

**So this module imports NOTHING of the emitted tree and parametrizes over nothing.**
There is no ``graded()`` here, no ``adcp.types._schemas`` at module scope, and no
``pytest.mark.parametrize`` whose argument list is computed by importing anything.  A
tree that does not import reddens exactly the one named test below; it cannot error this
file's collection, because this file's collection reads the bundle and nothing else.

``adcp-client-python-10l.105`` measured the cost of the arrangement this replaces: at
``fc34707d``, **0 tests collected from** ``tests/test_emit.py`` -- 2,442 of the suite's
2,977 -- because ONE emitted module raised on import.  The obligation that exists to
report that module was one of the 2,442.

And the second half of the row, which is the compiler's own invariant: a base list naming
one class twice RAISES, at :meth:`codegen.ir.ClassDecl.__post_init__`.  Its perturbation
is here rather than in ``tests/test_emit.py`` for the same reason the import check is: a
duplicate base is one of the defects that takes a module's import down, so the check for
it may not sit behind an import of the tree.
"""

from __future__ import annotations

import dataclasses
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import fresh
import pytest
from compiled import compiled
from nodeset import claimed, partitions

from adcp.types._base import SchemaRef
from codegen import bundle, emit, ir
from codegen.refusal import BuildFailure

REPO = Path(__file__).resolve().parents[1]
BUNDLE = REPO / "schemas" / "cache" / "3.2"

#: The script the child runs, beside this file and NOT named ``test_*`` so pytest does
#: not collect it: it is a program, and its ``main`` is the obligation's body.
CHILD = Path(__file__).resolve().parent / "_imports_a_tree.py"

#: The hand-written half of ``src/adcp``, which a fresh tree needs beside it and which no
#: run emits.  Everything else under ``adcp/types`` is generated and is replaced by this
#: run's output -- which is the point: :func:`_a_fresh_package` must not leave one
#: committed generated file where the fresh tree expects its own.
GENERATED = ("_schemas", "constraints.py", "envelopes.py")


def _a_fresh_package(out: emit.Emitted, root: Path) -> Path:
    """``root/adcp``: the hand-written modules copied, every generated one FRESH.

    **Why a whole package and not just the tree.**  An emitted module says ``from
    adcp.types.constraints import StrMatchingA828669D`` -- an ABSOLUTE name -- so a fresh
    tree imported beside the committed package would resolve its aliases through the
    COMMITTED alias module, and an alias this run mints that the committed module does
    not carry is exactly the defect this check is here to report.  ``emit.write``'s own
    docstring states the same fact from the writer's side: ``beside`` is one file over the
    whole run, so the tree and the alias module are emitted together or not at all.

    Hand-written modules are COPIED rather than re-emitted because no run produces them:
    ``adcp/__init__.py``, ``adcp/types/__init__.py``, ``_base.py`` and ``_runtime.py``
    are the package the generated tree is written into (§7).
    """
    shutil.copytree(
        REPO / "src" / "adcp",
        root / "adcp",
        ignore=shutil.ignore_patterns("__pycache__", *GENERATED),
    )
    emit.write(out, root / "adcp" / "types" / "_schemas", root / "adcp" / "types")
    for rel in GENERATED:
        assert (root / "adcp" / "types" / rel).exists(), (
            f"{rel} is generated and this run did not write it; the child would import "
            "the committed one and grade a mix of two trees"
        )
    return root


def test_the_tree_the_whole_suite_grades_is_one_a_fresh_run_wrote() -> None:
    """The precondition of every other check in this suite, reported here and nowhere.

    ``docs/plan/architecture.md`` (2026-10-29) puts the subject of grading at a fresh
    emission, and ``tests/fresh.py`` is the act: it writes that emission to disk and binds
    the GENERATED half of ``adcp.types`` in front of ``src/adcp/types``, with
    ``tests/conftest.py`` importing it so the binding precedes collection.  A compiler
    that RAISES therefore raises inside a conftest, where a raise errors the whole suite's
    collection -- the defect this epic's first row removed, arriving from the other side --
    so ``fresh`` records the reason instead and this test is what reads the record.

    Three clauses, and the middle one is what makes a green mark mean something:

    * a tree was built, and ``fresh.FAILURE`` is empty;
    * the three GENERATED children of ``adcp.types`` resolve inside it and the two
      HAND-WRITTEN ones do not, which is §7's split between the compile's inputs and its
      output read back off the import system.  ``_base.py`` and ``_runtime.py`` are
      nobody's output -- ``tests/compiled.py``'s key covers them as INPUTS -- so ``src/``
      is their source of truth and the fall-through to it is deliberate;
    * and the tree is not ``src/``.  If it were, every census in this suite would again
      be a reading of whenever the artifact was last regenerated.

    **Here and not in ``tests/test_emit.py``** for that file's own reason: this one's
    collection reads the bundle and nothing else, so a tree that does not exist reddens a
    named test rather than disabling 2,400.
    """
    import adcp.types._base
    import adcp.types._runtime
    import adcp.types._schemas
    import adcp.types.constraints
    import adcp.types.envelopes

    assert fresh.FAILURE == "", fresh.FAILURE
    generated = claimed(
        "generated children of adcp.types",
        (adcp.types._schemas, adcp.types.constraints, adcp.types.envelopes),
    )
    for module in generated:
        assert Path(module.__file__).is_relative_to(fresh.PACKAGE), module.__file__
    for module in (adcp.types._base, adcp.types._runtime):
        assert Path(module.__file__).is_relative_to(REPO / "src"), module.__file__
    assert fresh.TREE != REPO / emit.TREE, fresh.TREE


def test_every_module_a_fresh_run_emits_imports_and_every_class_of_it_is_defined(
    tmp_path: Path,
) -> None:
    """Every file a FRESH run emits imported, and every class of it resolved.

    **Measured at ``adcp-client-python-10l.21``, which is why the obligation exists.**
    ``render.klass`` filters the typed ``__pydantic_extra__`` annotation's reported
    imports by the names the rendered line uses, and the filter split the hint on four
    characters -- ``[``, ``]``, ``,`` and ``|`` -- so a CALL inside the annotation hid
    every name in it.  ``core/postal-area-support.json``'s extras store holds a
    ``uniqueItems`` array, which §2 renders as ``Annotated[…, Field(json_schema_extra={…}),
    AfterValidator(Distinct())]``, and none of ``Field``, ``AfterValidator`` or
    ``Distinct`` was imported: the module raised ``PydanticUserError: not fully defined``
    on first touch and 11 pairs reported ``harness_error`` three test files away.

    **Measured at ``adcp-client-python-10l.98``, which is why the POPULATION moved.**  One
    base list naming one class twice produced two unimportable modules and the committed
    tree held only one of them, so the old obligation found one defect and not two --
    purely because one of the two documents happened to be in ``src/``.  The second was
    ``media-buy/get-media-buys-response.json`` at
    ``/properties/media_buys/items/properties/packages/items/properties/creative_approvals/items``,
    whose module a fresh run emits and ``emit.TREE`` does not hold.

    **In a CHILD process, and that is a property of the question and not a convenience.**
    The suite's own interpreter has already bound ``adcp.types.constraints`` -- the
    committed one -- by the time any test runs, and :func:`_a_fresh_package` says what
    grading a fresh tree against it would mean.  One interpreter, one ``adcp``, and the
    tree it imports is the one the compiler just produced.

    ``model_json_schema()`` is what asks the second half: an unresolved forward reference
    survives the import and fails only when pydantic is asked to build the schema, which
    is exactly the shape ``__pydantic_extra__`` produced.
    """
    out = compiled(BUNDLE, sorted(bundle.portable(BUNDLE)))
    claimed("modules a fresh run emits", out.files)
    _a_fresh_package(out, tmp_path)

    done = subprocess.run(
        [sys.executable, str(CHILD)],
        capture_output=True,
        text=True,
        env={
            **os.environ,
            # ``tmp_path`` FIRST, so the child's ``adcp`` is the fresh one: PYTHONPATH
            # precedes the editable install's ``.pth`` on ``sys.path``, which is the same
            # reason ``./check`` spells ``PYTHONPATH=.:src``.
            "PYTHONPATH": os.pathsep.join((str(tmp_path), str(REPO))),
        },
        cwd=REPO,
        check=False,
    )
    assert done.returncode == 0, f"{done.stdout[-2000:]}\n{done.stderr[-4000:]}"
    report = json.loads(done.stdout)
    # The denominator, asserted before the failures and as an EQUALITY BETWEEN TWO
    # DERIVATIONS: a child that imported nothing reports no failure, which is the vacuous
    # pass ``nodeset.claimed`` exists to refuse.  Both sides are read off this run -- the
    # modules the child walked and the ``.py`` files ``emit.write`` just wrote -- so
    # neither is a number anybody re-points (``tests/test_every_check_names_its_set.py``'s
    # first rule).
    # **THE SAME BLINDNESS WAS ON THIS SIDE TOO**, and it is why the equality held while
    # the obligation did not.  ``not rel.endswith("__init__.py")`` dropped all 32 of the
    # package markers, and the child's ``if not info.ispkg`` dropped the 31 of them that
    # ``walk_packages`` yields -- so both derivations read 1,057 and agreed about a tree
    # of 1,088 modules.  Repairing the child alone reddens this at ``(1088, 1057)``, which
    # is the measurement: 31 modules and ``brand/__init__.py``'s 111 classes were outside
    # the obligation, discharged by nothing.
    #
    # ``rel != "__init__.py"`` and not a suffix test: the ONE file excluded is the tree's
    # own root, ``_schemas/__init__.py``, which ``walk_packages(pkg.__path__, ...)`` cannot
    # yield because it enumerates that package's CHILDREN and a package's ``__init__`` IS
    # the package.  Every other ``__init__.py`` is a module of the tree -- 30 of them the
    # empty layout markers, one of them a document's own body (``emit.module_file``'s
    # layout rule) -- and all of them must import.
    written = claimed(
        "modules a fresh run wrote",
        {rel for rel in out.files if rel.endswith(".py") and rel != "__init__.py"},
    )
    assert report["modules"] == len(written), (report["modules"], len(written))
    assert report["classes"] > len(written), (report["classes"], len(written))
    assert report["failures"] == [], report["failures"]


def test_the_import_obligation_reports_both_halves_of_a_defect_it_is_shown(
    tmp_path: Path,
) -> None:
    """The instrument, on the three shapes it exists to report, over a package of FIVE.

    §9: a rule nothing can break is a finding about the rule -- and the check above is
    green, so without this nothing says it could ever be red.  The population is a
    hand-built ``_schemas`` and not the bundle's, because what is being graded here is the
    CHILD and not the compiler: a five-module tree runs in a second where the real one
    costs three minutes, and the three defects are ones this epic actually produced.

    * **a name the module does not import** -- ``10l.21``'s shape, where ``render.klass``'s
      import filter hid every name inside a call.  The module IMPORTS and the class
      resolves nothing, which is why ``model_json_schema()`` is the second question;
    * **a base list naming one class twice** -- ``10l.98``'s shape, which is
      ``TypeError: duplicate base class`` and takes the module's IMPORT down.  Reported as
      that module's failure and NOT as the whole run's, which is the property the decision
      turns on: the clean module is reached and the child still reports it;
    * **a defect in a module that is a PACKAGE** -- ``adcp-client-python-bxu``'s shape, and
      the one the gate above cannot say anything about.  ``emit.module_file``'s layout rule
      writes a document whose own path is also a DIRECTORY of the bundle to
      ``<path>/__init__.py``, so ``brand.json``'s module is ``adcp.types._schemas.brand``
      and ``pkgutil`` reports it as a package; the child screened ``ispkg`` and 31 of the
      tree's 1,088 modules -- ``brand/__init__.py``'s 111 classes among them -- were
      outside the obligation.  **Graded here and not above because the gate above is green
      either way**: both its derivations dropped the package markers, so the equality held
      over a tree the walk could not see all of, and a fix to a blind gate is unverifiable
      by that gate's own green.  Here the package module carries a DEFECT, so the walk
      either names it or does not, and the ``rooted/under.py`` beside it says the loss was
      never recursion -- ``walk_packages`` descends into a package whatever the caller does
      with its ``ispkg`` entry, and what the screen dropped is the ``__init__.py`` body.

    **By behaviour and never by inspection**: nothing here reads the child's source or
    asks how it walks.  The claim is that a known package module's classes are REACHED,
    and what says so is a failure reported from inside one.
    """
    shutil.copytree(
        REPO / "src" / "adcp",
        tmp_path / "adcp",
        ignore=shutil.ignore_patterns("__pycache__", "_schemas"),
    )
    schemas = tmp_path / "adcp" / "types" / "_schemas"
    schemas.mkdir()
    (schemas / "__init__.py").write_text("")
    (schemas / "unresolved.py").write_text(
        "from __future__ import annotations\n"
        "from adcp.types._base import AdCPBaseModel\n"
        "class Unresolved(AdCPBaseModel):\n"
        "    a: Annotated[str, Field(description='x')]\n"
    )
    (schemas / "duplicated.py").write_text(
        "from adcp.types._base import AdCPBaseModel\n"
        "class Indicator(AdCPBaseModel):\n    pass\n"
        "class Twice(Indicator, Indicator):\n    pass\n"
    )
    (schemas / "clean.py").write_text(
        "from adcp.types._base import AdCPBaseModel\n"
        "class Clean(AdCPBaseModel):\n    a: str\n"
    )
    # ``rooted/`` is ``brand/``'s shape: a DOCUMENT's module written to the package's own
    # ``__init__.py``, carrying classes, with the directory's documents as its submodules.
    # The unresolved annotation is ``10l.21``'s again, placed here so the only thing that
    # can name ``...rooted.Rooted`` is a walk that imported the package itself.
    rooted = schemas / "rooted"
    rooted.mkdir()
    (rooted / "__init__.py").write_text(
        "from __future__ import annotations\n"
        "from adcp.types._base import AdCPBaseModel\n"
        "class Rooted(AdCPBaseModel):\n"
        "    a: Annotated[str, Field(description='x')]\n"
    )
    (rooted / "under.py").write_text(
        "from adcp.types._base import AdCPBaseModel\n"
        "class Under(AdCPBaseModel):\n    a: str\n"
    )

    done = subprocess.run(
        [sys.executable, str(CHILD)],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": os.pathsep.join((str(tmp_path), str(REPO)))},
        cwd=REPO,
        check=False,
    )
    assert done.returncode == 0, done.stderr[-2000:]
    report = json.loads(done.stdout)
    # The modules BY NAME and not by count, read off the directory as POSIX paths so the
    # package root is distinguishable from a plain module -- ``rooted/__init__.py`` and
    # ``rooted/under.py`` are two files and one of them is the package's own body.
    assert {
        str(m.relative_to(schemas).as_posix()) for m in schemas.rglob("*.py")
    } == {
        "__init__.py",
        "unresolved.py",
        "duplicated.py",
        "clean.py",
        "rooted/__init__.py",
        "rooted/under.py",
    }
    # Minus ONE and not minus the ``__init__.py`` count: the single file outside the walk
    # is the tree's own root, which ``walk_packages(pkg.__path__, ...)`` cannot yield
    # because it enumerates that package's children.  ``rooted`` is one of those children.
    assert report["modules"] == len(list(schemas.rglob("*.py"))) - 1, report
    named = {name for name, _ in report["failures"]}
    assert named == {
        "adcp.types._schemas.unresolved.Unresolved",
        "adcp.types._schemas.duplicated",
        # **THE PACKAGE MODULE'S CLASS WAS REACHED**, and this entry is the only thing in
        # the suite that says so.  A walk screening ``ispkg`` imports ``rooted.under`` and
        # never ``rooted`` itself, so it reports two failures here and this set is short by
        # one -- which is ``brand/__init__.py``'s 111 classes, in miniature and red.
        "adcp.types._schemas.rooted.Rooted",
    }, report["failures"]
    why = dict(report["failures"])
    assert "not fully defined" in why["adcp.types._schemas.unresolved.Unresolved"], why
    assert "duplicate base class" in why["adcp.types._schemas.duplicated"], why
    assert "not fully defined" in why["adcp.types._schemas.rooted.Rooted"], why
    # And the clean modules WERE reached -- including ``rooted/under.py``, the submodule
    # under the package root, which is what says recursion was never what the ``ispkg``
    # screen cost.  As an EQUALITY BETWEEN TWO DERIVATIONS and not a pinned count
    # (``tests/test_every_check_names_its_set.py``'s first rule): every ``class``
    # statement of the modules that IMPORTED, which is the fixture minus ``duplicated``.
    # That one fails at IMPORT, so neither of its two classes is ever reached -- the
    # difference between the shape that takes a module down and the shape that does not.
    declared = sum(
        1
        for path in sorted(schemas.rglob("*.py"))
        if path.stem != "duplicated"
        for line in path.read_text().splitlines()
        if line.startswith("class ")
    )
    assert report["classes"] == declared, (report, declared)


# --------------------------------------------------------------------------- #
# §2's other half of the row: a duplicate base is OURS, so it raises
# --------------------------------------------------------------------------- #
def _decl(*bases: str) -> ir.ClassDecl:
    return ir.ClassDecl(
        name="CreativeApprovalsItemIndicatorsItem",
        ref=SchemaRef(document="media-buy/get-media-buys-response.json", pointer="#"),
        fields=(),
        bases=tuple(ir.TypeRef(b, local=True) for b in bases),
    )


def test_a_base_list_naming_one_class_twice_raises() -> None:
    """``architecture.md``: "a base list naming one class twice RAISES".

    §2 decides WHICH of the two it is -- "a refusal is the document's and a broken
    invariant is ours" -- and the clause applied is that nothing a document can state
    produces a duplicate base, so the reader of such a report would go to ``codegen/``.
    An exception at the pointer is loud and honest where a refusal is quiet and wrong.

    **The shape is the one ``adcp-client-python-10l.98`` had**, named here so the check is
    known to fire on a defect this epic actually suffered rather than on an invention:
    ``class CreativeApprovalsItemIndicatorsItem(Indicator, Indicator)``, which is
    ``TypeError: duplicate base class`` at IMPORT -- three test files away from the walk
    that built it, reported as ``harness_error`` on every pair of the module, and charged
    to a document that stated nothing wrong.

    Three cells, and the middle one is what makes the chokepoint the right one:

    * the duplicate raises, and the message names the class, the whole list and the
      document, because those are what a reader goes to ``codegen/`` with;
    * a list naming two DIFFERENT classes does not -- including the two-base shape §4's
      union row builds (the dispatch mixin beside the model base), which is every union
      base of the tree;
    * **and it fires through ``dataclasses.replace``**, which is the half a guard at the
      call sites cannot have: a base travels as a POINTER until ``lower/names.py`` binds
      it, so two DISTINCT pointers naming one class are a duplicate only after binding,
      and ``names._bound`` rebuilds the declaration with ``replace``.  That is exactly
      ``10l.98``'s own shape -- two pointers, one symbol.
    """
    whole = BuildFailure
    with pytest.raises(whole) as raised:
        _decl("Indicator", "Indicator")
    said = str(raised.value)
    assert "CreativeApprovalsItemIndicatorsItem" in said, said
    assert "'Indicator' twice" in said, said
    assert "media-buy/get-media-buys-response.json" in said, said

    # Two different classes: the union row's own base list, which no clause here may
    # refuse.
    _decl("BranchDispatchMixin", "AdCPBaseModel")

    # And through the naming pass's rebuild, which is where the live defect landed.
    bound = _decl("#/definitions/a", "#/definitions/b")
    with pytest.raises(whole):
        dataclasses.replace(
            bound, bases=(ir.TypeRef("Indicator", local=True), ir.TypeRef("Indicator", local=True))
        )


def test_no_document_of_the_bundle_reaches_the_duplicate_base_guard() -> None:
    """The guard is on every class declaration, so a whole-population run CLEARS it.

    §9's rule that "a rule nothing can break is a finding about the rule" has a second
    half for a rule that can break everything: a guard on the one chokepoint every base
    list passes through either holds over the whole bundle or stops the build, and there
    is no third outcome to report.

    **THE READING, which is what ``./check`` prints:** the run completes, all 1,054
    portable documents emit, and no document is refused -- *emitted 1054 / refused 0
    (deferred 0, verdict 0); accounted 1054*.  Refusal is read off ``Refusal.kind``
    (``codegen/refusal.py``) and never off a sentence and never summed, which is the
    directive's own reading of the figures.

    **THE WHOLE IS THE POPULATION AND NOT THE REFUSED SET**, and that is this check's own
    history rather than a preference.  It used to partition ``set(out.refusals)`` into two
    literal sets of two and five documents, against a docstring reading of "1,047 documents
    emit and the 7 refusals are the same 7" -- the eighth stale census found in this code.
    The compiler refuses nothing now, so the whole was EMPTY and :func:`nodeset.partitions`
    rejected the call on its own precondition: *"empty whole -- the partition below holds
    vacuously"*.  The instrument caught the stale pin rather than passing over it, which is
    the behaviour it exists for.

    The pins could not be repaired by re-pointing their sets: a partition over an empty
    whole is vacuous however its parts are spelled, so emptying the literals would have
    produced a gate that passes when nothing happens.  The claim needs a real whole, and
    there is one -- the 1,054 portable documents, non-empty whatever the compiler decides
    about them.  Both parts are then READ off this run, so a document that arrives, leaves
    or starts being refused reddens with the document NAMED, which is what the old comment
    said it wanted and what no count can do.
    """
    out = compiled(BUNDLE, sorted(bundle.portable(BUNDLE)))
    portable = claimed("the bundle's portable documents", bundle.portable(BUNDLE))
    # Total and disjoint over a whole that cannot be empty: every portable document is
    # emitted or refused and not both, with the unaccounted and the double-counted reported
    # BY NAME rather than as a difference of two totals.
    partitions(portable, emitted=out.emitted, refused=out.refusals)
    # And the refused part is empty, grouped BY KIND so that the thing reported is the
    # document and its kind.  ``primary`` and ``chained`` are the two halves ``./check``
    # prints; a document refused under either, or under a kind nothing here anticipates,
    # arrives in this mapping and reddens with its own name.  An empty mapping is the
    # reading, where ``len(out.refusals) == 0`` would say only that a number has not moved.
    by_kind: dict[str, set[str]] = {}
    for document, refusal in out.refusals.items():
        by_kind.setdefault(str(refusal["kind"]).split(".")[-1], set()).add(document)
    assert by_kind == {}, {kind: sorted(named) for kind, named in by_kind.items()}
