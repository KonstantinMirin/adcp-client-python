"""Request-body size cap middleware — closes #239.

ASGI middleware that rejects HTTP requests whose body exceeds a
configurable byte cap. Without this guard, every MCP/A2A tool call
reaches ``Pydantic.model_validate`` with no input size bound, letting
a single attacker send arbitrarily large JSON and exhaust CPU/memory
at the validation step. (PR #238 security review flagged this when
typed-dispatch made per-request validation unconditional.)

Installed once at server bind time — before FastMCP or the a2a-sdk
``Starlette`` app handle the request — so oversized bodies are cut
off at the ASGI boundary, well before any parser allocates for them.
"""

from __future__ import annotations

from typing import Any

# 10 MB — generous enough for realistic AdCP payloads (multi-package
# create_media_buy with embedded creatives/assets can run ~1–2 MB) but
# small enough that adversarial traffic can't trivially exhaust a
# single-worker server. Sellers who legitimately need more override via
# ``serve(..., max_request_size=N)``.
DEFAULT_MAX_REQUEST_BYTES: int = 10 * 1024 * 1024


class RequestSizeLimitMiddleware:
    """Reject HTTP requests whose body exceeds ``max_bytes``.

    Two layers:

    1. **Content-Length fast-fail.** If the client advertises a body
       bigger than the cap, we reject before reading a single byte.
    2. **Streaming accounting.** For chunked transfers (``Transfer-
       Encoding: chunked`` with no Content-Length) the middleware
       buffers and counts bytes as they arrive; when the total crosses
       the cap it stops reading and returns ``413 Payload Too Large``.

    GET / HEAD / OPTIONS bypass both — they don't carry request bodies
    in any spec we talk to.

    The response payload is deliberately minimal. AdCP has no transport
    error shape for oversized requests (errors/recovery are for
    application-layer failures), so we return a plain HTTP 413 —
    the standard shape every HTTP client understands.
    """

    def __init__(self, app: Any, max_bytes: int = DEFAULT_MAX_REQUEST_BYTES) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "GET").upper()
        if method in ("GET", "HEAD", "OPTIONS"):
            await self.app(scope, receive, send)
            return

        # Pattern 1 — Content-Length fast-fail.
        for key, value in scope.get("headers", []):
            if key == b"content-length":
                try:
                    declared = int(value)
                except ValueError:
                    # Malformed header; fall through to streaming check.
                    break
                if declared > self.max_bytes:
                    await self._send_413(send)
                    return
                break

        # Pattern 2 — buffer + count. We read the whole body (up to the
        # cap) before handing it to the inner app. Buffering is fine
        # because (a) we're bounding the buffer size by the cap, and
        # (b) ASGI apps downstream (FastMCP, a2a-sdk) already read the
        # full body into memory before parsing — we're not adding a new
        # RAM cost, we're enforcing one that already exists.
        chunks: list[bytes] = []
        total = 0
        more_body = True
        while more_body:
            msg = await receive()
            msg_type = msg.get("type")
            if msg_type == "http.disconnect":
                # Client gave up before sending the full body. Pass
                # through — nothing to do.
                return
            if msg_type != "http.request":
                # Unexpected message type; forward verbatim via a fresh
                # receive loop by replaying what we have and letting the
                # app handle the rest.
                chunks.append(b"")
                break
            body = msg.get("body", b"")
            total += len(body)
            if total > self.max_bytes:
                await self._send_413(send)
                return
            chunks.append(body)
            more_body = bool(msg.get("more_body", False))

        # Body fit within the cap — replay to the app.
        index = 0
        chunks_count = len(chunks)

        async def replay_receive() -> dict[str, Any]:
            nonlocal index
            if index < chunks_count:
                body = chunks[index]
                index += 1
                return {
                    "type": "http.request",
                    "body": body,
                    "more_body": index < chunks_count,
                }
            # App asked for more after we replayed everything — the
            # spec says http.disconnect once the body is drained.
            return {"type": "http.disconnect"}

        await self.app(scope, replay_receive, send)

    @staticmethod
    async def _send_413(send: Any) -> None:
        """Emit a minimal HTTP 413 Payload Too Large response."""
        body = b"Payload too large.\n"
        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [
                    (b"content-type", b"text/plain; charset=utf-8"),
                    (b"content-length", str(len(body)).encode("ascii")),
                ],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": body,
                "more_body": False,
            }
        )
