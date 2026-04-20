"""v3 → v4 migration for the AdCP SDK.

The spec redesign in 4.0 renamed the 9 ``<Type>Asset`` payload
classes to ``<Type>Content`` and removed several legacy types
(``BrandManifest``, ``DeliverTo``, ``Pricing``, ``PromotedProducts``,
``PromotedOfferings``, ``FormatCategory``, ``PackageStatus``). This
module does the mechanical rewrites and prints a structured report of
everything that still needs human attention.

Two kinds of findings:

* **Applied**: direct name rewrites (``AudioAsset`` → ``AudioContent``
  etc). The 9 rename targets are distinctive enough that word-boundary
  regex is safe; sellers should still review the diff.
* **Flagged**: removed types, numbered ``Assets<N>`` imports,
  ``adcp.types.generated_poc`` imports. These don't rewrite — the
  seller has to choose the replacement (e.g. ``BrandManifest`` →
  ``BrandReference(domain=...)`` depends on call-site context).

Invocation::

    python -m adcp.migrate v3-to-v4 ./src            # dry run, report only
    python -m adcp.migrate v3-to-v4 ./src --apply    # rewrite files in place
    python -m adcp.migrate v3-to-v4 ./src --json     # structured report

The dry run is the default — you always see what would change before
anything moves. ``--apply`` writes files in place; commit your tree
before running it so ``git diff`` is the review view.

.. important::
   The codemod matches identifiers textually (word-boundary regex, not
   AST). That's deliberate — attribute accesses, imports, type
   annotations, and f-string-interpolated type names all need the
   rename, and a text-match catches every context a caller cares
   about. The tradeoff: a string literal like
   ``ERROR_MSG = "AudioAsset deprecated"`` or a comment mentioning
   ``AudioAsset`` will rewrite. Review the ``git diff`` for these
   cases (usually trivially reverted) — they are the one class of
   false positive the regex approach produces.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

# The 9 spec rename mappings — payload ``<Type>Asset`` → ``<Type>Content``.
# Order matters only for predictable report output; the regex replaces
# each name independently.
ASSET_CONTENT_RENAMES: dict[str, str] = {
    "AudioAsset": "AudioContent",
    "CssAsset": "CssContent",
    "HtmlAsset": "HtmlContent",
    "ImageAsset": "ImageContent",
    "JavascriptAsset": "JavascriptContent",
    "TextAsset": "TextContent",
    "UrlAsset": "UrlContent",
    "VideoAsset": "VideoContent",
    "WebhookAsset": "WebhookContent",
}


# Removed types — no auto-replacement possible, flag with migration hint.
# Paired with an anchor slug in MIGRATION_v3_to_v4.md so operators can
# jump straight to the replacement pattern.
REMOVED_TYPES: dict[str, tuple[str, str]] = {
    "BrandManifest": (
        "use BrandReference(domain=...) on requests; " "read ResolvedBrand.brand from the registry",
        "brandmanifest--brandreference",
    ),
    "FormatCategory": (
        "removed — format category info lives on Format metadata",
        "formatcategory--removed",
    ),
    "DeliverTo": (
        "use publisher_properties on the request",
        "deliverto--publisher_properties",
    ),
    "PromotedProducts": (
        "use the spec-current offerings shape",
        "promotedproducts--promotedofferings--offerings",
    ),
    "PromotedOfferings": (
        "use the spec-current offerings shape",
        "promotedproducts--promotedofferings--offerings",
    ),
    "Pricing": (
        "use the discriminated *PricingOption classes " "(e.g. CpmFixedRatePricingOption)",
        "pricing--discriminated-pricingoption",
    ),
    "PackageStatus": (
        "package status is now carried by MediaBuyStatus",
        "packagestatus--mediabuystatus",
    ),
}


# Attribute accesses that moved / were removed. Flagged not rewritten
# because context determines the right replacement.
REMOVED_ATTRIBUTE_ACCESSES: dict[str, str] = {
    ".brand_manifest": ("ResolvedBrand.brand_manifest removed — use .brand instead"),
}


# Private-module imports that shouldn't appear in downstream code.
PRIVATE_IMPORT_PATHS: dict[str, str] = {
    "adcp.types.generated_poc": (
        "private module — import from adcp.types (stable public API) instead"
    ),
}


# Regex for numbered Assets direct imports (``Assets5``, ``Assets14``, etc).
# Bare ``Assets`` (no digits) is a legitimate base class alias; the
# regex requires at least one digit to avoid false positives.
NUMBERED_ASSETS_PATTERN = re.compile(r"\bAssets\d+\b")


@dataclass
class Finding:
    """One migration finding — either an applied rename or a manual TODO."""

    kind: str  # "rename" | "flag_removed" | "flag_private" | "flag_numbered" | "flag_attribute"
    path: str
    line: int
    column: int
    before: str
    after: str | None = None  # None for flag-only items
    hint: str | None = None
    migration_anchor: str | None = None


@dataclass
class Report:
    """Structured migration report."""

    applied: list[Finding] = field(default_factory=list)
    flagged: list[Finding] = field(default_factory=list)
    scanned_files: int = 0
    rewritten_files: int = 0

    def add(self, finding: Finding) -> None:
        if finding.kind == "rename":
            self.applied.append(finding)
        else:
            self.flagged.append(finding)


_SKIP_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        ".tox",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "__pycache__",
        "node_modules",
        "dist",
        "build",
        ".eggs",
    }
)


def _iter_python_files(root: Path) -> list[Path]:
    """Walk ``root`` for ``*.py`` files, skipping common build/dep dirs.

    Skip-dir matching is applied to path components *relative to
    ``root``*, not absolute parts. A seller's repo checked out at
    ``/home/ci/build/myrepo/src`` (where ``build`` is a CI-scratch
    ancestor directory) previously had every file silently skipped —
    the absolute-path check hit ``build`` and dropped the whole tree.
    Relative matching makes the skip honour user intent: skip
    ``myrepo/src/build/output.py`` while still scanning
    ``/home/ci/build/myrepo/src/app.py``.
    """
    if root.is_file():
        return [root] if root.suffix == ".py" else []
    resolved_root = root.resolve()
    files: list[Path] = []
    for p in root.rglob("*.py"):
        try:
            rel_parts = p.resolve().relative_to(resolved_root).parts
        except ValueError:
            # rglob can return paths outside root when root contains a
            # symlink; fall back to the raw parts for those.
            rel_parts = p.parts
        if any(part in _SKIP_DIRS for part in rel_parts):
            continue
        files.append(p)
    return sorted(files)


# Compile rename regexes once at module import. Word boundaries prevent
# partial matches (``MyAudioAsset`` stays untouched).
_RENAME_PATTERNS = {name: re.compile(rf"\b{re.escape(name)}\b") for name in ASSET_CONTENT_RENAMES}
_REMOVED_PATTERNS = {name: re.compile(rf"\b{re.escape(name)}\b") for name in REMOVED_TYPES}

# Attribute access patterns — word-boundary regex prevents
# ``my.brand_manifest_v2`` / ``brand_manifest_foo`` false positives
# that a plain ``in`` substring check would fire on.
_REMOVED_ATTRIBUTE_PATTERNS = {
    attr: re.compile(rf"{re.escape(attr)}\b") for attr in REMOVED_ATTRIBUTE_ACCESSES
}


def scan_file(path: Path, *, apply_changes: bool) -> tuple[list[Finding], str | None]:
    """Scan one file. Returns (findings, new_contents_or_None).

    new_contents_or_None is None when apply_changes=False or when no
    renames fired; the caller uses it as the signal to rewrite.

    Reads with ``utf-8-sig`` so UTF-8-BOM-prefixed source files (legal
    Python, common on Windows) migrate correctly. Uses ``newline=""``
    on read and write so CRLF line endings are preserved verbatim —
    Windows sellers otherwise get a giant noise diff where every line
    flips to LF.
    """
    findings: list[Finding] = []
    try:
        # Use ``open(..., newline="")`` over ``Path.read_text(newline=)``
        # — the latter was added in 3.13 but the SDK supports 3.10+.
        with open(path, encoding="utf-8-sig", newline="") as fh:
            original = fh.read()
    except (UnicodeDecodeError, OSError):
        # Skip unreadable or non-UTF8 files; migration targets Python source.
        return findings, None

    # Detect renames per-line so the report carries column info and the
    # same pattern that matched detection also drives the rewrite.
    updated = original
    rename_hits = False
    for lineno, line in enumerate(original.splitlines(), start=1):
        for old, new in ASSET_CONTENT_RENAMES.items():
            for match in _RENAME_PATTERNS[old].finditer(line):
                findings.append(
                    Finding(
                        kind="rename",
                        path=str(path),
                        line=lineno,
                        column=match.start() + 1,
                        before=old,
                        after=new,
                    )
                )
                rename_hits = True

        # Removed types — flagged, not rewritten.
        for name, (hint, anchor) in REMOVED_TYPES.items():
            for match in _REMOVED_PATTERNS[name].finditer(line):
                findings.append(
                    Finding(
                        kind="flag_removed",
                        path=str(path),
                        line=lineno,
                        column=match.start() + 1,
                        before=name,
                        hint=hint,
                        migration_anchor=anchor,
                    )
                )

        # Numbered Assets imports / references.
        for match in NUMBERED_ASSETS_PATTERN.finditer(line):
            findings.append(
                Finding(
                    kind="flag_numbered",
                    path=str(path),
                    line=lineno,
                    column=match.start() + 1,
                    before=match.group(0),
                    hint=(
                        "numbered Assets classes are unstable across spec revisions; "
                        "import the semantic alias from adcp.types instead"
                    ),
                    migration_anchor="numbered-discriminated-union-classes-shifted",
                )
            )

        # adcp.types.generated_poc imports.
        for private_path, hint in PRIVATE_IMPORT_PATHS.items():
            if private_path in line:
                col = line.index(private_path) + 1
                findings.append(
                    Finding(
                        kind="flag_private",
                        path=str(path),
                        line=lineno,
                        column=col,
                        before=private_path,
                        hint=hint,
                    )
                )

        # Removed attribute accesses (.brand_manifest etc.). Regex with
        # trailing word boundary prevents false-positives on
        # ``.brand_manifest_v2``, ``.brand_manifest_override``, etc.
        for attr, hint in REMOVED_ATTRIBUTE_ACCESSES.items():
            for match in _REMOVED_ATTRIBUTE_PATTERNS[attr].finditer(line):
                findings.append(
                    Finding(
                        kind="flag_attribute",
                        path=str(path),
                        line=lineno,
                        column=match.start() + 1,
                        before=attr,
                        hint=hint,
                    )
                )

    if apply_changes and rename_hits:
        for old, new in ASSET_CONTENT_RENAMES.items():
            updated = _RENAME_PATTERNS[old].sub(new, updated)
        return findings, updated

    return findings, None


def run(root: Path, *, apply_changes: bool = False) -> Report:
    """Execute the migration across ``root``. Returns a :class:`Report`."""
    report = Report()
    for path in _iter_python_files(root):
        report.scanned_files += 1
        findings, new_contents = scan_file(path, apply_changes=apply_changes)
        for f in findings:
            report.add(f)
        if new_contents is not None:
            # newline="" preserves whatever line endings were read
            # (including mixed — unusual but possible). Pair with the
            # ``open(..., newline="")`` read in ``scan_file``.
            with open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write(new_contents)
            report.rewritten_files += 1
    return report


def _format_text_report(report: Report, *, apply_changes: bool) -> str:
    """Human-readable migration report for the default CLI output."""
    lines: list[str] = []
    mode = "applied" if apply_changes else "would apply"

    lines.append(f"adcp migrate v3-to-v4 — scanned {report.scanned_files} files")
    lines.append("")

    if report.applied:
        lines.append(f"Renames {mode}: {len(report.applied)}")
        # Group by (before, after) for a compact summary.
        by_rename: dict[str, dict[str, list[Finding]]] = {}
        for f in report.applied:
            by_rename.setdefault(f.before, {}).setdefault(f.after or "?", []).append(f)
        for before, after_map in sorted(by_rename.items()):
            for after, hits in sorted(after_map.items()):
                lines.append(
                    f"  {before} → {after}  ({len(hits)} hit{'s' if len(hits) != 1 else ''})"
                )
                for f in hits[:5]:
                    lines.append(f"    {f.path}:{f.line}:{f.column}")
                if len(hits) > 5:
                    lines.append(f"    … and {len(hits) - 5} more")
    else:
        lines.append("No renames needed.")

    if report.flagged:
        lines.append("")
        lines.append(f"Manual review required: {len(report.flagged)} findings")
        by_name: dict[str, list[Finding]] = {}
        for f in report.flagged:
            by_name.setdefault(f.before, []).append(f)
        for name, hits in sorted(by_name.items()):
            lines.append(f"  {name}  ({len(hits)} hit{'s' if len(hits) != 1 else ''})")
            hint = hits[0].hint
            if hint:
                lines.append(f"    → {hint}")
            anchor = hits[0].migration_anchor
            if anchor:
                lines.append(f"    MIGRATION_v3_to_v4.md#{anchor}")
            for f in hits[:5]:
                lines.append(f"    {f.path}:{f.line}:{f.column}")
            if len(hits) > 5:
                lines.append(f"    … and {len(hits) - 5} more")
    else:
        lines.append("")
        lines.append("No manual-review findings.")

    if apply_changes and report.rewritten_files:
        lines.append("")
        lines.append(f"Rewrote {report.rewritten_files} files in place.")
        lines.append("Review with `git diff` before committing.")

    return "\n".join(lines)


def _format_json_report(report: Report) -> str:
    """JSON report for programmatic consumption (CI, editors)."""
    payload = {
        "scanned_files": report.scanned_files,
        "rewritten_files": report.rewritten_files,
        "applied": [asdict(f) for f in report.applied],
        "flagged": [asdict(f) for f in report.flagged],
    }
    return json.dumps(payload, indent=2)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for ``python -m adcp.migrate v3-to-v4``."""
    parser = argparse.ArgumentParser(
        prog="adcp.migrate v3-to-v4",
        description=(
            "Rewrite adcp 3.x → 4.0 ``<Type>Asset`` → ``<Type>Content`` renames "
            "and flag usages of removed types."
        ),
    )
    parser.add_argument(
        "path",
        type=Path,
        help="File or directory to scan (source tree root in typical use).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Rewrite files in place. Default is dry-run (report only). "
            "Commit your tree first so `git diff` is your review view."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON report instead of the human-readable text.",
    )
    args = parser.parse_args(argv)

    if not args.path.exists():
        print(f"error: path does not exist: {args.path}", file=sys.stderr)
        return 2

    report = run(args.path, apply_changes=args.apply)

    if args.json:
        print(_format_json_report(report))
    else:
        print(_format_text_report(report, apply_changes=args.apply))

    # Return non-zero when there are manual-review findings so CI can
    # gate on a clean report. Renames alone don't trip the gate —
    # they're mechanical and apply cleanly.
    return 1 if report.flagged else 0


if __name__ == "__main__":
    sys.exit(main())
