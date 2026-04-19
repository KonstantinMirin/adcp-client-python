"""RFC 9421 canonicalization for the AdCP request-signing profile.

Implements the canonical signature base per RFC 9421 §2.5 with the covered
components mandated by the AdCP profile (@method, @target-uri, @authority,
content-type, content-digest). URI canonicalization follows RFC 3986 §6.2
scheme-based normalization plus AdCP-specific rules: query preserved
byte-for-byte, percent-encoding hex uppercased, unreserved chars decoded,
default ports stripped, dot-segments collapsed.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit


@dataclass(frozen=True)
class SignatureInputLabel:
    """A single label in a Signature-Input header (e.g. the `sig1=...` entry)."""

    label: str
    components: tuple[str, ...]
    params: dict[str, str | int]
    raw_value: str


def parse_signature_input_header(header_value: str) -> dict[str, SignatureInputLabel]:
    """Parse a Signature-Input header value into a dict keyed by label.

    A Signature-Input header may contain multiple labels separated by commas:
    `sig1=(...);..., sig2=(...);...`. The AdCP profile mandates that verifiers
    process exactly one label (conventionally `sig1`) and ignore others.
    """
    labels: dict[str, SignatureInputLabel] = {}
    for entry in split_structured_field(header_value, ","):
        entry = entry.strip()
        if not entry:
            continue
        eq_paren = entry.find("=(")
        if eq_paren < 0:
            raise ValueError(f"malformed Signature-Input entry: {entry!r}")
        label = entry[:eq_paren].strip()
        remainder = entry[eq_paren + 1 :]
        close = remainder.find(")")
        if close < 0:
            raise ValueError(f"unterminated component list in label {label!r}")
        components_str = remainder[1:close]
        params_str = remainder[close + 1 :]
        components = tuple(_unquote_component(tok) for tok in components_str.split())
        params = _parse_params(params_str)
        labels[label] = SignatureInputLabel(
            label=label,
            components=components,
            params=params,
            raw_value=remainder,
        )
    return labels


def build_signature_base(
    method: str,
    url: str,
    headers: Mapping[str, str],
    parsed: SignatureInputLabel,
) -> str:
    """Build the RFC 9421 signature base string for the AdCP profile.

    Lines are joined with a single `\\n` (LF, not CRLF). No trailing newline.
    Components appear in the exact order listed in `Signature-Input`, followed
    by `@signature-params` as the last line.
    """
    lines: list[str] = []
    for comp in parsed.components:
        value = _resolve_component(comp, method, url, headers)
        lines.append(f'"{comp}": {value}')
    lines.append(f'"@signature-params": {parsed.raw_value}')
    return "\n".join(lines)


def canonicalize_target_uri(url: str) -> str:
    """Produce the `@target-uri` derived-component value per AdCP profile."""
    parts = urlsplit(url)
    scheme = parts.scheme.lower()
    netloc = _canon_authority(parts.netloc, scheme)
    path = _normalize_path(parts.path)
    if not path and parts.query:
        path = "/"
    # RFC 9421 §2.2.2 + RFC 7230 §5.5: effective request URI excludes the
    # fragment (client-local, never sent on wire).
    return urlunsplit((scheme, netloc, path, parts.query, ""))


def canonicalize_authority(url: str) -> str:
    """Produce the `@authority` derived-component value per AdCP profile."""
    parts = urlsplit(url)
    return _canon_authority(parts.netloc, parts.scheme.lower())


_DEFAULT_PORTS = {"http": 80, "https": 443}

# RFC 3986 §2.3 unreserved = ALPHA / DIGIT / "-" / "." / "_" / "~"
_UNRESERVED = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~")


def _resolve_component(comp: str, method: str, url: str, headers: Mapping[str, str]) -> str:
    if comp == "@method":
        return method.upper()
    if comp == "@target-uri":
        return canonicalize_target_uri(url)
    if comp == "@authority":
        return canonicalize_authority(url)
    if comp.startswith("@"):
        raise ValueError(f"unsupported derived component for AdCP profile: {comp}")
    value = _lookup(headers, comp.lower())
    if value is None:
        raise ValueError(f"missing header for covered component: {comp}")
    return value.strip()


def _lookup(headers: Mapping[str, str], name_lower: str) -> str | None:
    for k, v in headers.items():
        if k.lower() == name_lower:
            return v
    return None


def _canon_authority(netloc: str, scheme: str) -> str:
    if "@" in netloc:
        netloc = netloc.rsplit("@", 1)[1]
    host: str
    port: int | None = None
    if netloc.startswith("["):
        end = netloc.find("]")
        if end < 0:
            raise ValueError(f"unterminated IPv6 literal in authority: {netloc!r}")
        host = netloc[: end + 1]
        tail = netloc[end + 1 :]
        if tail.startswith(":"):
            port = int(tail[1:])
    elif ":" in netloc:
        host, portstr = netloc.rsplit(":", 1)
        port = int(portstr)
    else:
        host = netloc
    host = host.lower()
    if port is not None and port != _DEFAULT_PORTS.get(scheme):
        return f"{host}:{port}"
    return host


def _normalize_path(path: str) -> str:
    return _normalize_pct(_remove_dot_segments(path))


def _remove_dot_segments(path: str) -> str:
    """RFC 3986 §5.2.4 remove_dot_segments."""
    input_buf = path
    output = ""
    while input_buf:
        if input_buf.startswith("../"):
            input_buf = input_buf[3:]
        elif input_buf.startswith("./"):
            input_buf = input_buf[2:]
        elif input_buf.startswith("/./"):
            input_buf = "/" + input_buf[3:]
        elif input_buf == "/.":
            input_buf = "/"
        elif input_buf.startswith("/../"):
            input_buf = "/" + input_buf[4:]
            slash = output.rfind("/")
            output = output[:slash] if slash >= 0 else ""
        elif input_buf == "/..":
            input_buf = "/"
            slash = output.rfind("/")
            output = output[:slash] if slash >= 0 else ""
        elif input_buf in (".", ".."):
            input_buf = ""
        else:
            if input_buf.startswith("/"):
                next_slash = input_buf.find("/", 1)
            else:
                next_slash = input_buf.find("/")
            if next_slash < 0:
                output += input_buf
                input_buf = ""
            else:
                output += input_buf[:next_slash]
                input_buf = input_buf[next_slash:]
    return output


def _normalize_pct(s: str) -> str:
    """Uppercase %XX hex and decode percent-encoded unreserved chars."""
    out: list[str] = []
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c == "%" and i + 2 < n:
            hex2 = s[i + 1 : i + 3]
            try:
                b = int(hex2, 16)
            except ValueError:
                out.append(c)
                i += 1
                continue
            ch = chr(b)
            if ch in _UNRESERVED:
                out.append(ch)
            else:
                out.append("%" + hex2.upper())
            i += 3
        else:
            out.append(c)
            i += 1
    return "".join(out)


def split_structured_field(s: str, sep: str) -> list[str]:
    """Split on `sep` occurrences that are outside RFC 8941 sf-string quotes and parens.

    sf-string escapes per RFC 8941 §3.3.3 are `\\\\` and `\\"` only; the state
    machine tracks an `esc` flag so that `\\\\"` closes the quoted span (the
    backslash escapes itself, the following quote is unescaped).
    """
    out: list[str] = []
    depth = 0
    in_q = False
    esc = False
    start = 0
    for i, c in enumerate(s):
        if in_q:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_q = False
        elif c == '"':
            in_q = True
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
        elif c == sep and depth == 0:
            out.append(s[start:i])
            start = i + 1
    out.append(s[start:])
    return out


def _unquote_component(token: str) -> str:
    t = token.strip()
    if len(t) >= 2 and t[0] == '"' and t[-1] == '"':
        return t[1:-1]
    raise ValueError(f"component name not quoted: {token!r}")


def _parse_params(params_str: str) -> dict[str, str | int]:
    out: dict[str, str | int] = {}
    s = params_str.strip()
    if not s:
        return out
    if s.startswith(";"):
        s = s[1:]
    for part in split_structured_field(s, ";"):
        part = part.strip()
        if not part:
            continue
        k, eq, v = part.partition("=")
        k = k.strip()
        v = v.strip()
        if not k:
            raise ValueError(f"signature param with empty name: {part!r}")
        if not eq or not v:
            raise ValueError(f"signature param {k!r} has empty value")
        if v.startswith('"'):
            if not (v.endswith('"') and len(v) >= 2):
                raise ValueError(f"signature param {k!r} has unterminated quoted value")
            out[k] = _unescape_sf_string(v[1:-1])
        else:
            try:
                out[k] = int(v)
            except ValueError as exc:
                raise ValueError(
                    f"signature param {k!r} must be a quoted string or integer, got {v!r}"
                ) from exc
    return out


def _unescape_sf_string(s: str) -> str:
    """Unescape RFC 8941 §3.3.3 sf-string contents (only `\\\\` and `\\"`)."""
    out: list[str] = []
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c == "\\" and i + 1 < n and s[i + 1] in ("\\", '"'):
            out.append(s[i + 1])
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)
