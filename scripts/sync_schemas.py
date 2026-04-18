#!/usr/bin/env python3
"""
Sync AdCP JSON schemas from the authoritative protocol bundle.

Downloads a single gzipped tarball at
https://adcontextprotocol.org/protocol/{version}.tgz, verifies the bundle
against its SHA-256 sidecar, and extracts the `schemas/` tree into
`schemas/cache/`. Replaces the prior per-file sync.

Pinned releases additionally ship Sigstore keyless sidecars (`.tgz.sig` +
`.tgz.crt`). When present, this script shells out to `cosign verify-blob`
to prove the bundle was built by the adcontextprotocol/adcp release
workflow. Missing sidecars (e.g., `latest.tgz`, or releases that predate
signing) fall back to checksum-only trust per the upstream client contract.

The target version comes from `src/adcp/ADCP_VERSION`. If that version's
bundle is not published, sync falls back to `latest.tgz` (the dev snapshot).

Usage:
    python scripts/sync_schemas.py
"""

from __future__ import annotations

import hashlib
import io
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).parent.parent
CACHE_DIR = REPO_ROOT / "schemas" / "cache"
VERSION_FILE = REPO_ROOT / "src" / "adcp" / "ADCP_VERSION"
BUNDLE_BASE_URL = "https://adcontextprotocol.org/protocol"
USER_AGENT = "adcp-python-sdk/3.0"

# Sigstore keyless verification identity. Must match the upstream release
# workflow — see adcontextprotocol/adcp#2273.
COSIGN_IDENTITY_REGEX = (
    r"^https://github\.com/adcontextprotocol/adcp/"
    r"\.github/workflows/release\.yml@refs/heads/.*$"
)
COSIGN_OIDC_ISSUER = "https://token.actions.githubusercontent.com"


def get_target_adcp_version() -> str:
    """Read target AdCP version from ADCP_VERSION file (e.g. "3.0.0-rc.3")."""
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text().strip()
    return "latest"


def _http_get(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req) as response:
        return response.read()


def _http_get_optional(url: str) -> bytes | None:
    """GET returning None on 404 instead of raising."""
    try:
        return _http_get(url)
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise


def fetch_bundle(version: str) -> tuple[bytes, str]:
    """Fetch the bundle and expected checksum for a version.

    Returns:
        (tgz_bytes, expected_sha256_hex)
    """
    tgz_bytes = _http_get(f"{BUNDLE_BASE_URL}/{version}.tgz")
    sha_text = _http_get(f"{BUNDLE_BASE_URL}/{version}.tgz.sha256").decode()
    expected = sha_text.split()[0].strip().lower()
    return tgz_bytes, expected


def fetch_bundle_with_fallback(version: str) -> tuple[bytes, str, str]:
    """Fetch a pinned bundle; fall back to `latest` if not published yet.

    Returns:
        (tgz_bytes, expected_sha256_hex, effective_version)
    """
    try:
        data, sha = fetch_bundle(version)
        return data, sha, version
    except HTTPError as exc:
        if exc.code != 404 or version == "latest":
            raise
        print(f"  ! {version}.tgz not published yet; falling back to latest.tgz")
        data, sha = fetch_bundle("latest")
        return data, sha, "latest"


def fetch_signature_sidecars(version: str) -> tuple[bytes | None, bytes | None]:
    """Fetch Sigstore `.sig` and `.crt` sidecars for a version.

    Returns:
        (sig_bytes, crt_bytes), or (None, None) if either sidecar is missing.
    """
    sig = _http_get_optional(f"{BUNDLE_BASE_URL}/{version}.tgz.sig")
    crt = _http_get_optional(f"{BUNDLE_BASE_URL}/{version}.tgz.crt")
    if sig is None or crt is None:
        return None, None
    return sig, crt


def verify_cosign_signature(
    tgz_bytes: bytes, sig_bytes: bytes, crt_bytes: bytes
) -> None:
    """Verify the bundle with `cosign verify-blob`.

    Raises RuntimeError if cosign is not installed or verification fails.
    """
    if shutil.which("cosign") is None:
        raise RuntimeError(
            "Bundle has Sigstore signature sidecars but `cosign` is not installed.\n"
            "  Install: https://docs.sigstore.dev/cosign/installation/\n"
            "  Or set ADCP_SKIP_SIGNATURE=1 to trust the SHA-256 checksum only."
        )

    with tempfile.TemporaryDirectory() as tmp:
        tgz_path = Path(tmp) / "bundle.tgz"
        sig_path = Path(tmp) / "bundle.tgz.sig"
        crt_path = Path(tmp) / "bundle.tgz.crt"
        tgz_path.write_bytes(tgz_bytes)
        sig_path.write_bytes(sig_bytes)
        crt_path.write_bytes(crt_bytes)

        result = subprocess.run(
            [
                "cosign",
                "verify-blob",
                "--signature",
                str(sig_path),
                "--certificate",
                str(crt_path),
                "--certificate-identity-regexp",
                COSIGN_IDENTITY_REGEX,
                "--certificate-oidc-issuer",
                COSIGN_OIDC_ISSUER,
                str(tgz_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    if result.returncode != 0:
        raise RuntimeError(
            "Cosign signature verification failed.\n"
            f"  stdout: {result.stdout.strip()}\n"
            f"  stderr: {result.stderr.strip()}"
        )


def replace_cache_from_bundle(tgz_bytes: bytes, effective_version: str) -> int:
    """Extract the bundle's `schemas/` tree into CACHE_DIR, replacing its contents.

    Returns the number of files written.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        with tarfile.open(fileobj=io.BytesIO(tgz_bytes), mode="r:gz") as tf:
            tf.extractall(tmpdir, filter="data")

        bundle_root = Path(tmpdir) / f"adcp-{effective_version}"
        schemas_src = bundle_root / "schemas"
        if not schemas_src.is_dir():
            raise RuntimeError(
                f"Bundle missing expected directory: adcp-{effective_version}/schemas/"
            )

        if CACHE_DIR.exists():
            shutil.rmtree(CACHE_DIR)
        CACHE_DIR.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(schemas_src, CACHE_DIR)

        return sum(1 for _ in CACHE_DIR.rglob("*") if _.is_file())


def main() -> None:
    target_version = get_target_adcp_version()
    print(f"Syncing AdCP schema bundle from {BUNDLE_BASE_URL}...")
    print(f"Target version: {target_version}")
    print(f"Cache directory: {CACHE_DIR}\n")

    try:
        print(f"Fetching {target_version}.tgz + checksum...")
        tgz_bytes, expected_sha, effective_version = fetch_bundle_with_fallback(
            target_version
        )
    except (HTTPError, URLError) as exc:
        print(f"\n✗ Failed to download bundle: {exc}", file=sys.stderr)
        sys.exit(1)

    actual_sha = hashlib.sha256(tgz_bytes).hexdigest()
    if actual_sha != expected_sha:
        print(
            f"\n✗ Checksum mismatch for adcp-{effective_version}.tgz:\n"
            f"  expected: {expected_sha}\n"
            f"  actual:   {actual_sha}",
            file=sys.stderr,
        )
        sys.exit(1)
    print(f"  ✓ Checksum verified ({actual_sha[:12]}…, {len(tgz_bytes):,} bytes)")

    if os.environ.get("ADCP_SKIP_SIGNATURE") == "1":
        print("  ! Skipping Sigstore verification (ADCP_SKIP_SIGNATURE=1)")
    else:
        try:
            sig_bytes, crt_bytes = fetch_signature_sidecars(effective_version)
        except (HTTPError, URLError) as exc:
            print(f"\n✗ Failed to fetch signature sidecars: {exc}", file=sys.stderr)
            sys.exit(1)

        if sig_bytes is None or crt_bytes is None:
            print(
                f"  ! No Sigstore sidecars for adcp-{effective_version} "
                "(checksum-only trust)"
            )
        else:
            try:
                verify_cosign_signature(tgz_bytes, sig_bytes, crt_bytes)
            except RuntimeError as exc:
                print(f"\n✗ {exc}", file=sys.stderr)
                sys.exit(1)
            print(
                "  ✓ Sigstore signature verified "
                "(issued to adcontextprotocol/adcp release workflow)"
            )

    try:
        file_count = replace_cache_from_bundle(tgz_bytes, effective_version)
    except (tarfile.TarError, RuntimeError) as exc:
        print(f"\n✗ Failed to extract bundle: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"\n✓ Successfully synced {file_count} schema files")
    print(f"  Effective version: adcp-{effective_version}")
    print(f"  Location: {CACHE_DIR}")


if __name__ == "__main__":
    main()
