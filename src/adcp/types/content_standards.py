"""The public path of the ``content_standards`` domain: §1's one import path for its classes.

The names are the compiler's, re-exported in one line from the aggregator it owns
outright and compares byte for byte, ``adcp.types._surface.content_standards``.  This file is the
COMPOSITION: it declares nothing, lists nothing, and the object reached at a name here
is the class the private per-document module built.  Why the aggregator is a second
file rather than this one is in ``adcp.types``' own docstring and in the ruling
``codegen/emit.py``'s ``SURFACE`` carries.
"""

from ._surface.content_standards import *  # noqa: F403
from ._surface.content_standards import __all__ as __all__
