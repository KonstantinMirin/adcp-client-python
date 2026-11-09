"""The exports of the ``extensions`` domain, as the compiler aggregates them.

Every name here is the class, root model, enumeration or alias the schema document
of that name compiles to, re-exported from the private module at the document's own
path.  The object is the same one the runtime validates into -- ``isinstance``
against a union branch imported from here is true.

Generated from the compiler's own record of what it exported: every document ROOT,
every union BRANCH and every type ALIAS the documents of this domain declare.  A
document added upstream appears here with nothing edited.

**NOT the path a consumer writes.**  This file is the compiler's outright and is
compared byte for byte, so that the domain's PUBLIC module can compose it in one
line and serve a hand-written name set beside it where the domain's word is also a
word upstream kept machinery under.  The public module is the one import path for
every name here.
"""

from __future__ import annotations

from .._schemas.extensions.extension_meta import AdCPExtensionFileSchema as AdCPExtensionFileSchema
from .._schemas.extensions.index import AdCPExtensionRegistry as AdCPExtensionRegistry

__all__ = [
    'AdCPExtensionFileSchema',
    'AdCPExtensionRegistry',
]
