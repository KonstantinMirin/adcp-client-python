"""The verifier: three assertions per node, and nothing else.

``docs/plan/architecture.md`` §9 is this package's whole specification.  It asserts
three things at every node of every portable document --

===============================================  ====================  ===================
the witness                                      the subject           what must hold
===============================================  ====================  ===================
the constructed valid instance                   the emitted class     the class accepts it
each invalidating mutation of it                 the emitted class     it refuses it, THERE
the accepted instance, instantiated and dumped   the document          the document admits
===============================================  ====================  ===================

-- and :mod:`codegen.verify.witness` is the first two columns' first row: the value a
node's own keywords state it admits, and one mutation per keyword it states.

**NOTHING HERE IMPORTS THE WALK.**  ``codegen.keywords``, ``codegen.attribution``,
``codegen.bundle``, ``codegen.refusal`` and ``codegen.dump_exemptions`` are the permitted
set, asserted by ``tests/test_import_rule.py``, and §9 gives the reason: one body of code
deciding what the model states and what the document states agrees with itself by
construction, so a defect in it is green on both sides.
"""

from __future__ import annotations
