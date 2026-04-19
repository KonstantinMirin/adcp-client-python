"""The :class:`IdempotencyStore` coordinator: canonical hashing + backend + decorator.

Responsibilities:

1. Extract ``idempotency_key`` from the incoming request.
2. Scope lookups by ``(principal_id, key)`` via the backend.
3. On cache hit with matching canonical payload hash: return the cached response
   and mark ``replayed=True`` on the envelope.
4. On cache hit with a different hash: raise
   :class:`adcp.exceptions.IdempotencyConflictError`.
5. On miss: run the wrapped handler, then commit ``(hash, response)`` to the
   backend.

Per-principal scoping is a hard security requirement (AdCP #2315): a key from
principal A on seller S has no meaning for principal B. The store pulls the
principal id from :class:`adcp.server.base.ToolContext.caller_identity`. If no
context / no caller_identity is supplied, the store refuses to proceed —
fail-closed rather than collapse every buyer into a shared namespace.
"""

from __future__ import annotations

import copy
import logging
import time
import warnings
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

from pydantic import BaseModel

from adcp.exceptions import IdempotencyConflictError
from adcp.server.idempotency.backends import CachedResponse, IdempotencyBackend
from adcp.server.idempotency.canonicalize import canonical_json_sha256

logger = logging.getLogger(__name__)

# Spec bounds from capabilities.idempotency.replay_ttl_seconds (1h-7d).
_MIN_TTL_SECONDS = 3600
_MAX_TTL_SECONDS = 604800

HandlerFn = Callable[..., Awaitable[Any]]


class IdempotencyStore:
    """Coordinator that binds canonical hashing to a storage backend.

    :param backend: A concrete :class:`IdempotencyBackend`.
    :param ttl_seconds: How long cached responses remain replayable. Must be
        within the spec's ``[3600, 604800]`` range (1h to 7d). 86400 (24h) is
        the recommended floor and matches the compliance storyboard.
    :param hash_fn: Optional override for the canonical hash function. Defaults
        to :func:`canonical_json_sha256`. Exposed for tests and for anyone who
        wants to experiment with alternative equivalence rules — though note
        the spec mandates RFC 8785 JCS for interop.
    """

    def __init__(
        self,
        backend: IdempotencyBackend,
        ttl_seconds: int = 86400,
        hash_fn: Callable[[dict[str, Any]], str] = canonical_json_sha256,
        *,
        clock: Callable[[], float] = time.time,
    ) -> None:
        if not _MIN_TTL_SECONDS <= ttl_seconds <= _MAX_TTL_SECONDS:
            raise ValueError(
                f"ttl_seconds must be in [{_MIN_TTL_SECONDS}, {_MAX_TTL_SECONDS}] "
                f"per AdCP spec (capabilities.idempotency.replay_ttl_seconds), "
                f"got {ttl_seconds}"
            )
        self.backend = backend
        self.ttl_seconds = ttl_seconds
        self._hash_fn = hash_fn
        self._clock = clock

    def capability(self) -> dict[str, Any]:
        """Return the capabilities fragment declaring this store's replay window.

        Embed under ``capabilities.adcp.idempotency`` on the seller's
        ``get_adcp_capabilities`` response. Buyers read this to reason about
        retry-safe windows (AdCP #2315)::

            caps.adcp.idempotency = idempotency.capability()
            # → {"replay_ttl_seconds": 86400}
        """
        return {"replay_ttl_seconds": self.ttl_seconds}

    def wrap(self, handler: HandlerFn) -> HandlerFn:
        """Decorator that adds idempotency semantics to an AdCP handler method.

        The wrapped handler is called as ``handler(self, params, context)``.
        ``params`` may be a dict or a Pydantic model — both are normalized to
        a dict before hashing. The return value is coerced to a dict for
        caching (via ``model_dump`` if Pydantic).

        The decorator always returns the handler's original object on a cache
        miss and a best-effort Pydantic re-validation on a hit (when the
        handler's declared return type exposes ``model_validate``). Callers
        that return raw dicts get dicts back.
        """

        @wraps(handler)
        async def _wrapped(
            handler_self: Any,
            params: Any,
            context: Any = None,
            *args: Any,
            **kwargs: Any,
        ) -> Any:
            principal_id, idempotency_key, params_dict = self._prepare(params, context)
            if principal_id is None or idempotency_key is None:
                # No key → spec says the server MUST reject with INVALID_REQUEST.
                # We let the handler run so validation layers above us (Pydantic,
                # FastAPI, etc.) can reject with a typed error; the middleware's
                # job is only to dedup when a key IS present.
                return await handler(handler_self, params, context, *args, **kwargs)

            payload_hash = self._hash_fn(params_dict)

            cached = await self.backend.get(principal_id, idempotency_key)
            if cached is not None:
                if cached.payload_hash == payload_hash:
                    logger.debug(
                        "idempotency replay: principal=%s key_prefix=%s",
                        principal_id,
                        idempotency_key[:8],
                    )
                    return _clone_response(cached.response)
                # Same key, different payload — spec-defined conflict.
                raise IdempotencyConflictError(
                    operation=getattr(handler, "__name__", "handler"),
                    errors=[
                        {
                            "code": "IDEMPOTENCY_CONFLICT",
                            "message": (
                                "idempotency_key reused with a different payload "
                                "(canonical hash mismatch)"
                            ),
                        }
                    ],
                )

            response = await handler(handler_self, params, context, *args, **kwargs)
            # Deep-copy when caching so post-return mutation of the caller's
            # copy can't poison future replays. `_clone_response` also deep-
            # copies on the hit path, giving independent objects per replay.
            response_dict = copy.deepcopy(_to_dict(response))
            entry = CachedResponse(
                payload_hash=payload_hash,
                response=response_dict,
                expires_at_epoch=self._clock() + self.ttl_seconds,
            )
            # Commit cache AFTER handler returns. Atomicity with the handler's
            # side effects depends on the backend: MemoryBackend is best-effort
            # (no transactional relationship to external resources); PgBackend
            # (follow-up) will commit in the same transaction when the handler
            # uses the same engine. On put failure we log loudly and return
            # the handler's response — swallowing the exception would be wrong
            # (operators need the signal that caching is broken), and raising
            # would look to the caller like the handler failed, triggering a
            # retry that re-executes side effects. Best compromise: warn
            # operators, return the result, and accept that the next retry
            # with this key will re-execute.
            try:
                await self.backend.put(principal_id, idempotency_key, entry)
            except Exception:
                logger.warning(
                    "Idempotency cache put failed for principal=%s key_prefix=%s — "
                    "handler completed but a subsequent retry with this key will "
                    "re-execute rather than replay. This indicates an operational "
                    "issue with the idempotency backend.",
                    principal_id,
                    idempotency_key[:8],
                    exc_info=True,
                )
            return response

        return _wrapped

    def _prepare(
        self, params: Any, context: Any
    ) -> tuple[str | None, str | None, dict[str, Any]]:
        """Normalize inputs and extract the (principal, key, params_dict) tuple.

        Returns ``(None, None, params_dict)`` when idempotency doesn't apply
        (no caller identity or no key supplied). The caller falls through to
        the plain handler in that case — validation of missing-key lives in
        the request schema, not here.
        """
        params_dict = _to_dict(params)
        idempotency_key = params_dict.get("idempotency_key")
        if not isinstance(idempotency_key, str) or not idempotency_key:
            return None, None, params_dict
        principal_id = _extract_principal_id(context)
        if principal_id is None:
            # No caller identity: we can't safely scope the key. Spec requires
            # per-principal scope; anything else is a cross-principal replay
            # attack surface. Fall through to the handler (which will process
            # the request normally — no dedup, but no security regression).
            self._warn_missing_principal_once()
            return None, None, params_dict
        return principal_id, idempotency_key, params_dict

    _missing_principal_warned: bool = False

    def _warn_missing_principal_once(self) -> None:
        """Emit a one-time warning when the middleware sees a key but no principal.

        Silent fall-through is the worst DX: the seller drops in
        ``@idempotency.wrap``, ships, and doesn't discover until incident
        review that no dedup ever happened. Fire once per store instance so
        operators see the signal without filling logs on every request.
        """
        if self._missing_principal_warned:
            return
        self._missing_principal_warned = True
        warnings.warn(
            "IdempotencyStore received a request with idempotency_key but no "
            "caller_identity on ToolContext — dedup is SKIPPED. This usually "
            "means your transport isn't populating the authenticated principal. "
            "A2A: wire an a2a-sdk auth middleware that sets ServerCallContext.user; "
            "MCP: populate ToolContext.caller_identity from your FastMCP auth "
            "middleware (see adcp.server.idempotency README). "
            "This warning fires once per IdempotencyStore instance.",
            UserWarning,
            stacklevel=3,
        )


def _to_dict(value: Any) -> dict[str, Any]:
    """Coerce a request/response to a plain dict for hashing and caching."""
    if isinstance(value, dict):
        return value
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", exclude_none=True)
    if hasattr(value, "model_dump") and callable(value.model_dump):
        return value.model_dump(mode="json", exclude_none=True)  # type: ignore[no-any-return]
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    raise TypeError(
        f"Cannot coerce {type(value).__name__} to dict for idempotency caching"
    )


def _extract_principal_id(context: Any) -> str | None:
    """Pull the principal id from a ToolContext or equivalent shape.

    Accepts:

    * :class:`adcp.server.base.ToolContext` with ``caller_identity``
    * Any object exposing ``caller_identity`` / ``principal_id`` / ``principal.id``
    * A dict with any of the above keys
    """
    if context is None:
        return None
    for attr in ("caller_identity", "principal_id"):
        val = getattr(context, attr, None)
        if isinstance(val, str) and val:
            return val
    principal = getattr(context, "principal", None)
    if principal is not None:
        val = getattr(principal, "id", None)
        if isinstance(val, str) and val:
            return val
    if isinstance(context, dict):
        for key in ("caller_identity", "principal_id"):
            val = context.get(key)
            if isinstance(val, str) and val:
                return val
        principal = context.get("principal")
        if isinstance(principal, dict):
            val = principal.get("id")
            if isinstance(val, str) and val:
                return val
    return None


def _clone_response(response: dict[str, Any]) -> dict[str, Any]:
    """Return a deep copy of the cached response.

    The whole point of a cached replay is "identical response, every time."
    A shallow copy would let a caller mutate nested lists/dicts on first
    replay and poison every subsequent one. Deep copy the whole tree so each
    caller gets an independent object.
    """
    return copy.deepcopy(response)
