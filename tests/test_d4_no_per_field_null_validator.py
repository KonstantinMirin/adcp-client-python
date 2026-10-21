"""D4: optionals render plain `T | None = None`. No per-field null validator.

Acceptance belongs to `AdCPBaseModel.strict_validate` — schema, then construct.
`docs/plan/rebuild-plan.md` D4 has the reasoning.
"""

from __future__ import annotations

import ast
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
BANNED = ("Absent", "refuse_null")
SEARCHED = ("codegen", "src", "tests")  # not docs/: the plan names these to ban them


def _python_files() -> list[pathlib.Path]:
    return [
        p
        for top in SEARCHED
        for p in (ROOT / top).rglob("*.py")
        if "__pycache__" not in p.parts and p.name != pathlib.Path(__file__).name
    ]


def test_population_is_not_empty() -> None:
    files = _python_files()
    assert len(files) > 30, len(files)
    assert any(p.parts[-3:-1] == ("_schemas", "core") for p in files), "emitted tree not searched"


def test_no_module_names_the_retired_validator() -> None:
    """Banned by NAME, tokenised — so prose explaining the ban is not a violation."""
    offenders = []
    for path in _python_files():
        names = set()
        for node in ast.walk(ast.parse(path.read_text(), filename=str(path))):
            if isinstance(node, ast.Name):
                names.add(node.id)
            elif isinstance(node, ast.Attribute):
                names.add(node.attr)
            elif isinstance(node, ast.alias):
                names.add(node.asname or node.name.rsplit(".", 1)[-1])
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.add(node.name)
        if hit := names & set(BANNED):
            offenders.append(f"{path.relative_to(ROOT)}: {sorted(hit)}")
    assert not offenders, "\n  ".join(["retired rendering still present:", *offenders])


def test_optionals_render_plain() -> None:
    """States what the rendering IS, so a third spelling cannot satisfy both tests."""
    schemas = ROOT / "src" / "adcp" / "types" / "_schemas"
    modules = [p for p in schemas.rglob("*.py") if "__pycache__" not in p.parts]
    assert modules, "no emitted modules"
    seen, offenders = 0, []
    for path in modules:
        for ann in re.findall(r"^\s{4}\w+:\s*(.+?)\s*=\s*None\s*$", path.read_text(), re.M):
            seen += 1
            if any(b in ann for b in BANNED):
                offenders.append(f"{path.relative_to(ROOT)}: {ann}")
    assert seen, "no optional property found"
    assert not offenders, "\n  ".join(["optionals still aliased:", *offenders])


def test_base_documents_what_model_validate_skips() -> None:
    """pydantic exposes model_validate and we cannot remove it, so say what it skips."""
    base = (ROOT / "src" / "adcp" / "types" / "_base.py").read_text()
    assert "strict_validate" in base
    assert "model_validate" in base and "without" in base.lower()
