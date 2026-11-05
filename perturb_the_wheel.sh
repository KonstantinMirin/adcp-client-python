#!/bin/bash
# Break reading 8's gate on purpose, one packaging decision at a time.
#
# `docs/plan/final-state.md` reading 8 is "the wheel builds, installs into an
# environment that has never seen this repository, and every exported name imports
# from it", and the clause that says why a gate is needed at all is "packaging
# decides which files a wheel contains". So the perturbations are PACKAGING
# perturbations: every one edits `pyproject.toml`'s two declarations -- nothing in
# `src/` moves, and the committed tree stays byte-identical throughout.
#
# Before this file existed, nothing in the suite built a wheel. The two checks that
# look like they do (`tests/test_type_checker.py::_installed` and
# `tests/test_readme_executes.py::_consumer`) put the package into a venv with
# `shutil.copytree(src/adcp)`, which copies whatever is in the tree and therefore
# cannot redden for ANY of the cases below. That is measured here as the control: the
# same perturbations are run against those two files and they stay green.
#
# This is BANKED EVIDENCE and not a check: it is not collected by pytest, it is
# re-runnable, and `tests/test_the_wheel_is_the_artifact.py` is what the suite grades.
# Every case below names what it breaks and must print REDDENS.
#
#   ./perturb_the_wheel.sh
#
# It edits the two files in place and restores them with `git checkout --`, so it
# REQUIRES A CLEAN TREE: uncommitted work in either file is destroyed. It refuses to
# run otherwise.
#
# A COLLECTION ERROR IS NOT A GREEN RUN: the verdict matches "failed|error", because a
# malformed perturbation leaves a run that never executed and a scraper matching only
# "failed" records that as a guard that cannot redden.
set -u
cd "$(dirname "$0")" || exit 1

P=pyproject.toml
T=tests/test_the_wheel_is_the_artifact.py

if [ -n "$(git status --porcelain -- "$P" "$T")" ]; then
  echo "refusing to run: $P or $T has uncommitted changes, which this would destroy" >&2
  exit 1
fi

py() { CCM_INDEX_BYPASS=1 env -u VIRTUAL_ENV uv run --no-sync python "$@"; }

# `-n 0`: every test in the file reads ONE build (`_built` is cached per process), so a
# single process is both faster and the only way the verdict names one worker's run.
run() {  # run <label> <-k expression selecting the test it should redden>
  out=$(py -m pytest "$T" -q -n 0 -p no:randomly -k "$2" 2>&1 | tail -4)
  if echo "$out" | grep -qE "[0-9]+ (failed|error)"; then verdict=REDDENS; else verdict="STAYED GREEN"; fi
  printf '%-58s %-12s %s\n' "$1" "$verdict" "$(echo "$out" | grep -oE '[0-9]+ (passed|failed|error).*' | head -1)"
  git checkout -- "$P" "$T"
}

# The control: the same perturbation against the two checks that SIMULATE the install.
control() {  # control <label> <test file> <-k expression>
  out=$(py -m pytest "$2" -q -n 0 -p no:randomly -k "$3" 2>&1 | tail -4)
  if echo "$out" | grep -qE "[0-9]+ (failed|error)"; then verdict="REDDENS"; else verdict="STAYED GREEN"; fi
  printf '%-58s %-12s %s\n' "$1" "$verdict" "$(echo "$out" | grep -oE '[0-9]+ (passed|failed|error).*' | head -1)"
}

edit() { py -c "$1" || { echo "perturbation did not apply: $1" >&2; exit 1; }; }

echo "=== PACKAGING: the records ==="

# The whole of D4's acceptance half: without the records a wheel imports and raises on
# the first validation, which is the failure a source-tree run cannot see.
edit "import pathlib;p=pathlib.Path('$P');s=p.read_text();a='\"adcp.types._schemas\" = [\"*.json\", \"**/*.json\"]';assert s.count(a)==1;p.write_text(s.replace(a,''))"
run "every record dropped from package-data" "payload_is_the_packages_committed_files"

edit "import pathlib;p=pathlib.Path('$P');s=p.read_text();a='\"adcp.types._schemas\" = [\"*.json\", \"**/*.json\"]';assert s.count(a)==1;p.write_text(s.replace(a,''))"
run "every record dropped: the resource walk finds none" "is_a_record_the_wheel_packages"

# ONE level of the glob, which is the mistake a reader of the entry would actually make:
# `*.json` alone reaches `_schemas/*.json` and no subdirectory, so 1,054 records become
# however many sit at the top. A whole-set perturbation can be dismissed as unrealistic;
# this one cannot.
edit "import pathlib;p=pathlib.Path('$P');s=p.read_text();a='[\"*.json\", \"**/*.json\"]';assert s.count(a)==1;p.write_text(s.replace(a,'[\"*.json\"]'))"
run "the recursive half of the glob dropped" "payload_is_the_packages_committed_files"

echo
echo "=== PACKAGING: py.typed, which is reading 7's whole promise ==="

edit "import pathlib;p=pathlib.Path('$P');s=p.read_text();a='\"adcp\" = [\"py.typed\"]';assert s.count(a)==1;p.write_text(s.replace(a,''))"
run "py.typed dropped from package-data" "marker_reading_7_promises"

# The CONTROL, and it is the reason this file exists: reading 7's own gate reads
# `src/adcp/py.typed` and the `[tool.setuptools.package-data]` DECLARATION, so it
# reddens on this one -- and reading 7's consumer checks, which copytree the source
# tree, do not. Both are run, because "the declaration" and "the artifact" are
# different claims and only one of them is what a consumer installs.
edit "import pathlib;p=pathlib.Path('$P');s=p.read_text();a='\"adcp\" = [\"py.typed\"]';assert s.count(a)==1;p.write_text(s.replace(a,''))"
control "  control: the declaration check" tests/test_type_checker.py "declares_its_types_to_a_consumer"
control "  control: the copytree'd consumer check" tests/test_type_checker.py "member_of_every_public_enum"
git checkout -- "$P"

echo
echo "=== PACKAGING: packages.find, which decides which MODULES ship ==="

# A subpackage excluded. 40 documents of `core/async-response-refs/` stop shipping as
# modules, and the committed tree still holds them -- so this is exactly "a file the
# repository calls part of the package and packaging does not ship".
edit "import pathlib;p=pathlib.Path('$P');s=p.read_text();a='[tool.setuptools.packages.find]\nwhere = [\"src\"]';assert s.count(a)==1;p.write_text(s.replace(a,a+'\nexclude = [\"adcp.types._schemas.core.async_response_refs*\"]'))"
run "a subpackage excluded from packages.find" "payload_is_the_packages_committed_files"

# The same exclusion against the IMPORT clause: a domain module re-exports from the
# excluded subpackage, so `from adcp.types.<domain> import <Name>` raises inside the
# consumer environment.
edit "import pathlib;p=pathlib.Path('$P');s=p.read_text();a='[tool.setuptools.packages.find]\nwhere = [\"src\"]';assert s.count(a)==1;p.write_text(s.replace(a,a+'\nexclude = [\"adcp.types._schemas.core*\"]'))"
run "the core subtree excluded: exported names stop importing" "exports_imports_from_it"

echo
echo "=== THE INSTALL ASSERTION, which is what makes the rest mean anything ==="

# PYTHONPATH carries `.:src` in every invocation of this suite, and the shared `.venv`
# carries an editable `.pth` naming another checkout's `src`. Either one resolves `import
# adcp` to a SOURCE TREE, and then every reading above passes while saying nothing about
# the wheel -- so the assertion that reads `adcp.__file__` has to redden on exactly this.
#
# The leak is spelled ABSOLUTELY here, and the reason is itself a measurement: the first
# version of this case merely KEPT the inherited `PYTHONPATH`, which is the relative
# `.:src`, and it stayed green -- the probe runs with `cwd` set to the consumer
# environment, so neither entry resolved to anything. A leak that happens not to resolve
# is not the leak the assertion is about.
edit "import pathlib;p=pathlib.Path('$T');s=p.read_text();a='    return {k: v for k, v in os.environ.items() if k not in (\"PYTHONPATH\", \"VIRTUAL_ENV\", \"PYTHONHOME\")}';assert s.count(a)==1;p.write_text(s.replace(a,'    out = {k: v for k, v in os.environ.items() if k not in (\"PYTHONPATH\", \"VIRTUAL_ENV\", \"PYTHONHOME\")}\n    out[\"PYTHONPATH\"] = str(ROOT / \"src\")\n    return out'))"
run "PYTHONPATH leaking this repository's src, absolute" "never_seen_this_repository"

# And the same leak reaching only `sys.path` and not the first import: `src` appended
# rather than prepended still resolves the NEXT module, and 1,054 of them are private.
edit "import pathlib;p=pathlib.Path('$T');s=p.read_text();a='import adcp\nimport adcp.types';assert s.count(a)==1;p.write_text(s.replace(a,'import sys as _s; _s.path.append(\"$(pwd)/src\")\nimport adcp\nimport adcp.types'))"
run "src appended to sys.path, losing the import race" "never_seen_this_repository"

echo
echo "=== THE STALE BUILD DIRECTORY, which made every case above green once ==="

# `setuptools` stages the wheel in `build/lib` and prunes nothing, so a second build over
# a changed configuration packages the union of the two. Every packaging perturbation
# above printed STAYED GREEN until `_built` removed that directory. This case is the
# regression: take the removal out and the gate stops seeing packaging at all.
edit "import pathlib;p=pathlib.Path('$T');s=p.read_text();a='    shutil.rmtree(ROOT / \"build\", ignore_errors=True)';assert s.count(a)==1;p.write_text(s.replace(a,'    pass  # perturbed: the stale build directory is kept'))"
py -c "import pathlib,shutil;shutil.rmtree('build',ignore_errors=True)"
out=$(py -m pytest "$T" -q -n 0 -p no:randomly -k "payload_is_the_packages_committed_files" 2>&1 | tail -4)
edit "import pathlib;p=pathlib.Path('$P');s=p.read_text();a='\"adcp.types._schemas\" = [\"*.json\", \"**/*.json\"]';assert s.count(a)==1;p.write_text(s.replace(a,''))"
out=$(py -m pytest "$T" -q -n 0 -p no:randomly -k "payload_is_the_packages_committed_files" 2>&1 | tail -4)
if echo "$out" | grep -qE "[0-9]+ (failed|error)"; then verdict=REDDENS; else verdict="STAYED GREEN"; fi
printf '%-58s %-12s %s\n' "the records dropped, build/ kept from the run before" "$verdict" "$(echo "$out" | grep -oE '[0-9]+ (passed|failed|error).*' | head -1)"
git checkout -- "$P" "$T"
py -c "import shutil;shutil.rmtree('build',ignore_errors=True)"

echo
echo "=== THE DERIVATIONS THEMSELVES: a set that selects nothing ==="

# A derivation that selects nothing passes every assertion over it, and
# `tests/nodeset.py`'s `claimed` is what refuses one. These three prove it is wired to
# each of the three sets this file ranges over.
edit "import pathlib;p=pathlib.Path('$T');s=p.read_text();a='out[\"exported\"] = exported';assert s.count(a)==1;p.write_text(s.replace(a,'out[\"exported\"] = {k: [] for k in exported}'))"
run "every exported list read as empty" "exports_imports_from_it"

edit "import pathlib;p=pathlib.Path('$T');s=p.read_text();a='out[\"documents\"] = sorted(documents)';assert s.count(a)==1;p.write_text(s.replace(a,'out[\"documents\"] = []'))"
run "no document read off any exported name" "is_a_record_the_wheel_packages"

edit "import pathlib;p=pathlib.Path('$T');s=p.read_text();a='        elif entry.name.endswith(\".json\"):\n            packaged.append(name)';assert s.count(a)==1;p.write_text(s.replace(a,'        elif False:\n            packaged.append(name)'))"
run "the packaged-record walk finds nothing" "is_a_record_the_wheel_packages"

echo
echo "=== THE STATED GAPS, which redden when they close rather than going stale ==="

edit "import pathlib;p=pathlib.Path('$T');s=p.read_text();a='out[\"undocumented\"] = sorted(undocumented)';assert s.count(a)==1;p.write_text(s.replace(a,'out[\"undocumented\"] = []'))"
run "every exported name reaches a document after all" "does_not_grade"

edit "import pathlib;p=pathlib.Path('$T');s=p.read_text();a='    how[name] = \"module-level assignment\"';assert s.count(a)==1;p.write_text(s.replace(a,'    how[name] = \"__all__\"'))"
run "every public module declares __all__ after all" "does_not_grade"

echo
echo "=== AND A RECORD THAT IS PRESENT BUT NOT READABLE ==="

# An entry in the zip is not a readable resource. The resolver is what decides, so the
# perturbation points it one segment wrong rather than deleting a file.
edit "import pathlib;p=pathlib.Path('$T');s=p.read_text();a='        for part in document.split(\"/\"):\n            resource = resource.joinpath(part)\n        json.loads(resource.read_text())\n    except BaseException as error:  # noqa: BLE001\n        unreadable';assert s.count(a)==1;p.write_text(s.replace(a,'        for part in document.split(\"/\"):\n            resource = resource.joinpath(part + \".absent\")\n        json.loads(resource.read_text())\n    except BaseException as error:  # noqa: BLE001\n        unreadable'))"
run "the record resolver reaches a path that is not there" "is_a_record_the_wheel_packages"

echo
echo "=== NOT CAUGHT, AND SAID SO: a surface that SHRINKS ==="
echo "The exported set is the WHEEL'S OWN claim about itself. A wheel whose __all__s lost"
echo "names still imports every name it still claims, so this file reads green on it --"
echo "which is why it is stated in test_what_this_file_does_not_grade rather than left for"
echo "a reader to find. tests/test_the_domain_surface.py is the check that ties the surface"
echo "to emit.surface, the run's own record, and it is what reddens on that perturbation."

edit "import pathlib;p=pathlib.Path('$T');s=p.read_text();a='        exported[name] = list(declared)';assert s.count(a)==1;p.write_text(s.replace(a,'        exported[name] = list(declared)[:1]'))"
run "every __all__ truncated to its first name" "exports_imports_from_it"

echo
echo "every case above must print REDDENS except the line under NOT CAUGHT and the control"
echo "marked 'copytree', which must print STAYED GREEN: those two are the measurement of"
echo "what this file does and does not add."
