"""The public types of the ``extensions`` domain.

Every name here is the class, root model, enumeration or alias the schema document
of that name compiles to, re-exported from the private module at the document's own
path.  This is the one import path for each of them, and the object is the same one
the runtime validates into -- ``isinstance`` against a union branch imported from
here is true.

Generated from the compiler's own record of what it exported: every document ROOT,
every union BRANCH and every type ALIAS the documents of this domain declare.  A
document added upstream appears here with nothing edited.
"""

from __future__ import annotations

from ._schemas.extensions.extension_meta import AdCPExtensionFileSchema as AdCPExtensionFileSchema
from ._schemas.extensions.index import AdCPExtensionRegistry as AdCPExtensionRegistry

__all__ = [
    'AdCPExtensionFileSchema',
    'AdCPExtensionRegistry',
]
