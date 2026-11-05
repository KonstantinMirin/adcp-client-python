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

# PYTHONPATH carries `.:src` in every invocation of this suite. Left in the consumer
# environment, `import adcp` resolves to the SOURCE TREE and every reading above passes
# while saying nothing about the wheel -- so the assertion that reads `adcp.__file__`
# has to redden on exactly this.
edit "import pathlib;p=pathlib.Path('$T');s=p.read_text();a='if k not in (\"PYTHONPATH\", \"VIRTUAL_ENV\", \"PYTHONHOME\")';assert s.count(a)==1;p.write_text(s.replace(a,'if k not in (\"VIRTUAL_ENV\", \"PYTHONHOME\")'))"
run "PYTHONPATH left in the consumer environment" "never_seen_this_repository"

# And the same leak reaching only `sys.path` and not the first import: `src` appended
# rather than prepended still resolves the NEXT module, and 1,054 of them are private.
edit "import pathlib;p=pathlib.Path('$T');s=p.read_text();a='import adcp\nimport adcp.types';assert s.count(a)==1;p.write_text(s.replace(a,'import sys as _s; _s.path.append(\"$(pwd)/src\")\nimport adcp\nimport adcp.types'))"
run "src appended to sys.path, losing the import race" "never_seen_this_repository"

echo
echo "=== THE DERIVATIONS THEMSELVES, so a shrinking set cannot read as green ==="

# A set that selects nothing passes every assertion over it. `tests/nodeset.py`'s
# `claimed` is what refuses one, and these two cases are what prove it is wired.
edit "import pathlib;p=pathlib.Path('$T');s=p.read_text();a='    exported[name] = [t for t in targets if not t.startswith(\"_\")]';assert s.count(a)==1;p.write_text(s.replace(a,'    exported[name] = []'))"
run "the module-level-assignment arm selects nothing" "does_not_grade"

edit "import pathlib;p=pathlib.Path('$T');s=p.read_text();a='        exported[name] = list(declared)';assert s.count(a)==1;p.write_text(s.replace(a,'        exported[name] = []'))"
run "every __all__ read as empty" "exports_imports_from_it"

edit "import pathlib;p=pathlib.Path('$T');s=p.read_text();a='        elif entry.name.endswith(\".json\"):\n            packaged.append(name)';assert s.count(a)==1;p.write_text(s.replace(a,'        elif False:\n            packaged.append(name)'))"
run "the packaged-record walk finds nothing" "is_a_record_the_wheel_packages"

echo
echo "every case above must print REDDENS; the two lines marked 'control' must print"
echo "STAYED GREEN for the copytree'd consumer check, which is the gap this file closes."
