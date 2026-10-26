"""The reading layer: a raw mapping in, a typed positioned node out.

``docs/plan/architecture.md`` §1 puts one layer between ``bundle.py`` and the
decision: ``schema/parse.py`` is the ONE parser -- keys and type select the node
kind, and POSITION IS ASSIGNED WHEN THE NODE IS BUILT -- and ``schema/nodes.py``
declares the kinds it builds.  §11 gives this layer "raw mapping -> ``Node``;
admission; applied type; positions; pointers" and denies it the IR, Python types,
text and the run.

**What is here and what is not, as of row ``adcp-client-python-10l.5``.**
``nodes.py`` declares every kind in §4's table, with the four facts §4 says every
node carries and with ``pointer`` and ``position`` excluded from equality.  It has
NO READER yet: ``parse.py`` is the other half of §14 step 5 and is not written, so
``emit._decide`` is still the per-node dispatch and still reads a mapping.

Declared ahead of its reader on the precedent row .2 set for the descent column
(``keywords.descends_at``: "Declared here; its readers are section 14 step 5's and
are not built by this row"), and for the same reason -- the DECLARATION is what the
readers have to agree with, so it is worth having one of.  The row's delivery note
carries why the parser did not land with it.
"""
