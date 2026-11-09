"""The public path of the ``core`` domain: §1's one import path for its classes.

The names are the compiler's, re-exported in one line from the aggregator it owns
outright and compares byte for byte, ``adcp.types._surface.core``.  This file is the
COMPOSITION: it declares nothing, lists nothing, and the object reached at a name here
is the class the private per-document module built.  Why the aggregator is a second
file rather than this one is in ``adcp.types``' own docstring and in the ruling
``codegen/emit.py``'s ``SURFACE`` carries.

**AND THIS IS THE ONE DOMAIN WHOSE WORD UPSTREAM ALSO USED FOR HAND-WRITTEN
MACHINERY.**  Upstream's module at this path was 444 lines of the SDK's own types --
``TaskResult``, ``AgentConfig``, ``DebugInfo``, ``Member`` -- and no bundle document
states any of them.  They are restored at ``adcp._client_types``, the SDK's own
namespace, and re-exported below in the ``X as X`` form a type checker reads as a
re-export, so that ``from adcp.types.core import TaskResult`` resolves to upstream's
class and not to something invented for the word.

**They are deliberately NOT in ``__all__``, and the reason is another gate's
reading rather than taste.**  ``__all__`` here is the aggregator's, which is the
COMPILER's export set: ``tests_emit/test_the_domain_surface.py`` reads it as "every
name resolves at exactly one private path and IS the object that path holds", and a
name with no document behind it answers neither half.  A name is importable here
and advertised only where the compiler put it.

**``TaskStatus`` and ``Protocol`` are the same WORD as ours and a different concept,
and nothing is aliased between them.**  Upstream's ``TaskStatus`` has five members
including ``needs_input``; ours, from ``enums/task-status.json``, has nine including
``input-required``, and neither set contains the other.  Ours stays at
``adcp.types.enums`` and upstream's resolves here.  Upstream's ``Protocol`` is
``{a2a, mcp}``, a transport selector, against a protocol-domain enumeration of ours
with no shared value.  See ``docs/migration-from-upstream.md`` §5, which is written
from this exact case.
"""

from .._client_types import Activity as Activity
from .._client_types import ActivityType as ActivityType
from .._client_types import AgentConfig as AgentConfig
from .._client_types import DEFAULT_MAX_RESPONSE_BYTES as DEFAULT_MAX_RESPONSE_BYTES
from .._client_types import DebugInfo as DebugInfo
from .._client_types import Member as Member
from .._client_types import NeedsInputInfo as NeedsInputInfo
from .._client_types import Policy as Policy
from .._client_types import PolicyExemplar as PolicyExemplar
from .._client_types import PolicyExemplars as PolicyExemplars
from .._client_types import PolicyHistory as PolicyHistory
from .._client_types import PolicyRevision as PolicyRevision
from .._client_types import PolicySummary as PolicySummary
from .._client_types import Protocol as Protocol
from .._client_types import ResolvedBrand as ResolvedBrand
from .._client_types import ResolvedProperty as ResolvedProperty
from .._client_types import SubmittedInfo as SubmittedInfo
from .._client_types import TaskResult as TaskResult
from .._client_types import TaskStatus as TaskStatus
from .._client_types import WebhookMetadata as WebhookMetadata
from .._client_types import is_loopback_http_uri as is_loopback_http_uri

from ._surface.core import *  # noqa: F403
from ._surface.core import __all__ as __all__
