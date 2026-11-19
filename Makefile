.PHONY: help check-uv bootstrap format lint lint-all typecheck typecheck-all test test-type-checks check-type-ignore-contract regenerate-schemas pre-push ci-local clean install-dev check-schema-drift gate emit-suite

# Detect Python and use venv if available
PYTHON := $(shell if [ -f .venv/bin/python ]; then echo .venv/bin/python; else echo python3; fi)
PIP := $(shell if [ -f .venv/bin/pip ]; then echo .venv/bin/pip; else echo pip3; fi)
PYTEST := $(shell if [ -f .venv/bin/pytest ]; then echo .venv/bin/pytest; else echo pytest; fi)
BLACK := $(shell if [ -f .venv/bin/black ]; then echo .venv/bin/black; else echo black; fi)
RUFF := $(shell if [ -f .venv/bin/ruff ]; then echo .venv/bin/ruff; else echo ruff; fi)
# INVOKED AS A MODULE, BECAUSE A CONSOLE SCRIPT CARRIES A SHEBANG AND A SHEBANG GOES STALE.
# The previous `-f .venv/bin/mypy` test passed on a file that could not execute: this
# project's `.venv` is hardlink-shared across its worktrees, and `.venv/bin/mypy` carried
# `#!/srv/ws/wt-10l6/.venv/bin/python3` -- a worktree that has been deleted. `make` then
# reported `.venv/bin/mypy: No such file or directory` about the INTERPRETER while the
# script itself sat right there, so the existence test could never catch it. `dmypy` is
# broken the same way. `python -m` resolves the module through the interpreter already
# chosen above and has no second path to go stale.
MYPY := $(PYTHON) -m mypy
UV := uv

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

STORAGE := packages/adcp-reporting-storage
STORAGE_SRC := $(STORAGE)/src/adcp_reporting_storage

install-dev: ## Legacy pip-only install; bootstrap is preferred for contributors
	$(PIP) install -e ".[dev]" -e "./$(STORAGE)[pg,gcs,s3,azure]"

check-uv:
	@command -v $(UV) >/dev/null || { \
		echo "uv is required for bootstrap and pre-commit hooks. Install it from https://docs.astral.sh/uv/"; \
		exit 1; \
	}

bootstrap: check-uv ## Recommended contributor setup: uv-managed deps and git hooks
	$(UV) run --extra dev --group dev pre-commit install
	$(UV) run --extra dev --group dev pre-commit install --hook-type commit-msg

format: ## Format code with black (excludes generated files)
	$(BLACK) src/ tests/ scripts/ $(STORAGE)/src/
	@echo "✓ Code formatted successfully (_generated.py excluded via pyproject.toml)"

lint: ## Run linter (ruff) on source code (both distributions)
	$(RUFF) check src/ $(STORAGE)/src/
	@echo "✓ Linting passed"

lint-all: ## Run linter (ruff) on source and tests
	$(RUFF) check src/ $(STORAGE)/src/ tests/
	@echo "✓ Source and test linting passed"

typecheck: ## Run type checker (mypy) on source code (both distributions)
	$(MYPY) src/adcp/ $(STORAGE_SRC)/
	@echo "✓ Type checking passed"

typecheck-all: typecheck test-type-checks test-type-checks-pyright check-type-ignore-contract ## Run all type-check contracts
	@echo "✓ All type-check contracts passed"

# THE TWO SUITES WRITE TO SEPARATE ARTIFACT PATHS, because `addopts` names ONE and the
# last run therefore wins. Measured 2026-11-17: the emission gate ran after the SDK suite
# and `test-results/report.json` held 2,609 pairs where a reader expected 17,000 tests --
# so the SDK figure had to be read off a terminal log, which is the thing artifacts exist
# to stop. A fixed path is a footgun whenever two suites exist.
gate: ## THE emission gate: a schema-valid payload is accepted, an invalid one refused, the dump valid
	$(PYTEST) tests_emit/test_the_grade_is_green.py::test_this_pair_meets_the_contract \
		--junitxml=test-results/gate/junit.xml \
		--json-report-file=test-results/gate/report.json

# THE EMISSION SUITE: 94 files of emission invariants, and until this target nothing ran
# them. `make test` is `tests/` only, `gate` above names ONE node id of ONE file, and
# `ci-local` named neither -- so every merge in this project was approved against gates that
# did not cover what was being changed. It cost twice in two days: `domains.mirrored()` was
# deleted by the next whole re-emission with
# `test_emit.py::test_the_committed_tree_is_what_a_fresh_run_emits` sitting right there
# covering it, and `8e64bafe5` took `test_union_dispatch.py` from 15 passed to 2 failed, 13
# passed with `make test` and `make gate` both green.
#
# ONE PROCESS PER FILE, AND THAT IS THE WHOLE OF WHY IT TERMINATES. Measured 2026-11-19:
# as ONE pytest process the suite reached 26% of its 11,970 items in 50 m 40 s and printed
# nothing for a 20 m 33 s stretch at exactly the 25% mark, because two of its tests are
# unbounded and a PER-TEST backstop cannot be trusted to cut them --
# `pytest-timeout`'s default `signal` method arms a one-shot ITIMER_REAL that
# `hypothesis`'s GC callback can swallow and that `codegen.harness.within` clears in its
# own `finally`. Sharded, every file is bounded twice by something OUTSIDE the interpreter
# being bounded: `--timeout-method=thread` (a timer thread, which neither failure mode
# reaches) and `timeout(1)` around the process. A hang is then one file's, named in one
# `.status` file, with the other 93 still reported.
#
# THE SUBJECT IS A WILDCARD, so a file added later is run without anyone remembering --
# which is the half `test_union_dispatch.py` did not have. NOTHING IS EXEMPT: the one node
# this suite does not run is `tests_emit/conftest.py`'s `UNBOUNDED`, which is a bound and not
# an allowlist, and it is reported as `XFAIL [NOTRUN]` with its measurement rather than
# deselected.
#
# THIS TARGET IS RED TODAY AND IS NOT IN `ci-local`. 493 nodes over 53 files fail at
# `6263d7b2e`, and an enumerated list of 493 is a second backlog rather than a ratchet, so
# they are TRIAGED BY CAUSE in `FINDINGS-runner.md` -- with the short list `ci-local` should
# carry, and what has to be fixed or scoped first, named there.
#
# `test_the_grade_is_green.py` is split between the two targets on purpose: `gate` owns
# `test_this_pair_meets_the_contract` (2,570 pairs, 7 failed / 2,563 passed) and must not
# move, so this target takes the OTHER half -- `test_this_pair_has_no_undeclared_approximation`,
# 2,570 pairs that no target ran before this one.
EMIT_OUT := test-results/emit/suite
# THE TWO LONG POLES FIRST, because `xargs` starts the subjects in the order it is given
# them and the last one started decides the wall clock. Measured: `test_emit.py` is 19 min
# and the approximation half 17 min, against 2,344 s of CPU for the other 92 files together.
# It is a scheduling order and not an exemption -- every subject still runs.
EMIT_FIRST := tests_emit/test_emit.py \
	tests_emit/test_the_grade_is_green.py::test_this_pair_has_no_undeclared_approximation
EMIT_SUBJECTS := $(EMIT_FIRST) \
	$(filter-out tests_emit/test_emit.py tests_emit/test_the_grade_is_green.py,$(wildcard tests_emit/test_*.py))
# BOTH BOUNDS ARE SET BY ONE TEST, measured rather than chosen.
# `test_emit.py::test_the_output_is_a_function_of_its_inputs_and_of_nothing_else` is
# **1,012.3 s and green** -- it emits the whole 1,059-document bundle twice in child
# processes and compares -- and `test_emit.py` whole is 1,200.8 s. The next slowest test
# anywhere in the 93 files is 17.7 s and the next slowest file is 211 s. So the per-test
# bound has to clear 1,012 s with room for a 6-way contended run, and a hang in a small file
# therefore costs up to half an hour before it is cut. A lane that wants the tight bound back
# has it one flag away: `make emit-suite EMIT_TEST_TIMEOUT=60 EMIT_SUBJECTS=<file>`.
# A cut is a red with the file named, never a skip.
EMIT_TEST_TIMEOUT ?= 1800
EMIT_FILE_TIMEOUT ?= 2700
# Six, because the box this was measured on has 24 cores and the suite's own children take
# more: `test_emit.py` and three others spawn a whole `python -m codegen` emission each.
EMIT_JOBS ?= 6

# THE REPORT, which is what makes a sharded run readable as one result. It fails on a
# subject that left no report (a kill, which is what a hang looks like once it is bounded),
# on a nonzero exit, and on any failure -- and it names every failing node, grouped by file,
# because the next thing anyone does with this run is triage it.
define EMIT_REPORT
import json, pathlib, sys

out = pathlib.Path(sys.argv[1])
subjects = sys.argv[2:]
killed, counts, red, seen, slow = [], {}, [], set(), []
for status in sorted(out.glob("*.status")):
    rc, secs, subject = status.read_text().split(None, 2)
    subject = subject.strip()
    seen.add(subject)
    slow.append((int(secs), subject))
    report, log = status.with_suffix(".json"), status.with_suffix(".log")
    if not report.exists():
        killed.append(
            f"{subject}: exit {rc} and NO REPORT -- killed before teardown, which is what a"
            f" hang looks like once it is bounded; the stack is in {log}"
        )
        continue
    data = json.loads(report.read_text())
    for key, value in data["summary"].items():
        counts[key] = counts.get(key, 0) + value
    for test in data["tests"]:
        if test["outcome"] not in ("passed", "skipped", "xfailed"):
            red.append(test["nodeid"])
for subject in subjects:
    if subject not in seen:
        killed.append(f"{subject}: no shard ran it, so this run ranges over an unknown subset")
print("emission suite over " + str(len(seen)) + " of " + str(len(subjects)) + " subjects: " + ", ".join(
    str(counts[key]) + " " + key for key in sorted(counts) if counts[key]
))
print("slowest subjects: " + ", ".join(s + " " + str(n) + "s" for n, s in sorted(slow, reverse=True)[:3]))
byfile = {}
for node in red:
    byfile[node.split("::")[0]] = byfile.get(node.split("::")[0], 0) + 1
(out / "_red.txt").write_text("\n".join(sorted(red)) + "\n")
print(str(len(red)) + " failing nodes over " + str(len(byfile)) + " files, every one of them named in " + str(out / "_red.txt"))
for name in sorted(byfile, key=lambda f: -byfile[f]):
    print("  " + str(byfile[name]).rjust(4) + "  " + name)
for line in killed:
    print("  KILLED " + line)
sys.exit(1 if (red or killed) else 0)
endef
export EMIT_REPORT

emit-suite: ## THE emission suite: one bounded pytest process per file, with every failure named and attributed
	@mkdir -p $(EMIT_OUT)
	@# EVERY ARTIFACT OF THE PREVIOUS RUN GOES, not just the statuses: a shard that is
	@# killed leaves no report, and a STALE report under that name would be read as this
	@# run's and called green -- the one failure the reconciliation may not have.
	@rm -f $(EMIT_OUT)/*.status $(EMIT_OUT)/*.json $(EMIT_OUT)/*.xml $(EMIT_OUT)/*.log
	@printf '%s\n' $(EMIT_SUBJECTS) | xargs -P $(EMIT_JOBS) -I{} sh -c 'subject="{}"; \
		name=$$(printf %s "$$subject" | sed -e "s|^tests_emit/||" -e "s|\.py$$||" -e "s|::|--|g"); \
		started=$$(date +%s); \
		timeout -k 10 $(EMIT_FILE_TIMEOUT) $(PYTEST) "$$subject" -q -p no:cacheprovider \
			--timeout=$(EMIT_TEST_TIMEOUT) --timeout-method=thread \
			--junitxml=$(EMIT_OUT)/$$name.xml --json-report-file=$(EMIT_OUT)/$$name.json \
			> $(EMIT_OUT)/$$name.log 2>&1; \
		rc=$$?; \
		printf "%s %s %s\n" "$$rc" "$$(( $$(date +%s) - started ))" "$$subject" > $(EMIT_OUT)/$$name.status'
	@# `rc=$$?` IS TAKEN OFF THE COMMAND AND NOT OFF A PIPELINE, which is the one way this
	@# harness can lie: a `pytest ... | tail` records `tail`'s status, every file reports
	@# rc=0, and a suite with 493 failures reads as green. Measured on another lane's slice
	@# script on 2026-11-19. Nothing here pipes, and EMIT_REPORT grades the JSON report as
	@# well as the exit code, so a wrong rc cannot carry a run on its own.
	@$(PYTHON) -c "$$EMIT_REPORT" $(EMIT_OUT) $(EMIT_SUBJECTS)

test: ## Run SDK test suite with coverage
	$(PYTEST) tests/ -v --cov=src/adcp --cov-report=term-missing \
		--junitxml=test-results/sdk/junit.xml \
		--json-report-file=test-results/sdk/report.json
	@echo "✓ All tests passed"

test-fast: ## Run SDK tests without coverage (faster)
	$(PYTEST) tests/ -v \
		--junitxml=test-results/sdk/junit.xml \
		--json-report-file=test-results/sdk/report.json
	@echo "✓ All tests passed"

test-type-checks: ## Run adopter-pattern type-check suite (mypy --strict, zero type: ignore allowed)
	$(MYPY) --strict tests/type_checks/
	@echo "✓ Adopter type-checks passed"

test-type-checks-pyright: ## Run the adopter-pattern type-check suite under pyright (see scripts/run_pyright_type_checks.py)
	$(PYTHON) scripts/run_pyright_type_checks.py

check-type-ignore-contract: ## Fail if adopter type-check fixtures use type: ignore suppressions
	$(PYTHON) scripts/check_type_ignore_contract.py
	@echo "✓ Adopter type-check fixtures contain no type: ignore suppressions"

test-generation: ## Run only code generation tests
	$(PYTEST) tests/test_code_generation.py -v
	@echo "✓ Code generation tests passed"

regenerate-registry: ## Regenerate registry types from OpenAPI spec
	@echo "Generating registry types from OpenAPI spec..."
	$(PYTHON) scripts/generate_registry_types.py
	@echo "✓ Registry types regenerated"

validate-generated: ## Validate generated code (syntax, imports, and equality with a regeneration)
	@echo "Validating generated code..."
	@$(PYTHON) -m py_compile src/adcp/types/_generated.py
	@$(PYTHON) scripts/generate_versioned_stubs.py --check
	@$(PYTHON) scripts/generate_types.py --check
	@$(PYTHON) scripts/generate_versioned_bases.py --check
	@echo "✓ Generated code validation passed"

pre-push: format lint typecheck-all test validate-generated ## Run all checks before pushing (format, lint, typecheck, test, validate)
	@echo ""
	@echo "================================"
	@echo "✓ All pre-push checks passed!"
	@echo "================================"
	@echo ""
	@echo "Safe to push to remote."

ci-local: lint typecheck-all test validate-generated ## Run core CI checks locally (without formatting)
	@echo ""
	@echo "================================"
	@echo "✓ All CI checks passed!"
	@echo "================================"

clean: ## Clean generated files and caches
	rm -rf build/
	rm -rf dist/
	rm -rf dist-storage/ $(STORAGE)/build/ $(STORAGE)/src/*.egg-info
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "✓ Cleaned all generated files and caches"

build: ## Build distribution packages (adcp into dist/, adcp-reporting-storage into dist-storage/)
	$(PYTHON) scripts/bundle_schemas.py
	python -m build
	python -m build --outdir dist-storage/ $(STORAGE)
	@echo "✓ Distribution packages built"

# Development workflow commands

quick-check: lint test-fast ## Quick check (lint + fast tests) for rapid iteration
	@echo "✓ Quick check passed"

full-check: pre-push ## Alias for pre-push (full check before committing)

# Schema workflow

check-schema-drift: ## Check if schemas are out of sync with upstream
	@echo "Checking for schema drift..."
	@$(PYTHON) scripts/sync_schemas.py --no-skills
	@$(PYTHON) scripts/fix_schema_refs.py
	@$(PYTHON) scripts/generate_types.py --check
	@if git diff --exit-code schemas/cache/; then \
		echo "✓ Schemas are up-to-date"; \
	else \
		echo "✗ Schemas are out of date!"; \
		echo "Run: make regenerate-schemas"; \
		git diff schemas/cache/; \
		exit 1; \
	fi

# Help users understand what to run
.DEFAULT_GOAL := help
