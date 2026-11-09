"""The reading layer: a raw mapping in, a typed positioned node out.

``docs/plan/architecture.md`` §1 puts one layer between ``bundle.py`` and the
decision: ``schema/parse.py`` is the ONE parser -- keys and type select the node
kind, and POSITION IS ASSIGNED WHEN THE NODE IS BUILT -- and ``schema/nodes.py``
declares the kinds it builds.  §11 gives this layer "raw mapping -> ``Node``;
admission; applied type; positions; pointers" and denies it the IR, Python types,
text and the run.

**What is here, and the READING for each half rather than a size.**  ``nodes.py``
declares every kind in §4's table, with the four facts §4 says every node carries and
with ``pointer`` and ``position`` excluded from equality.  ``parse.py`` is its reader
and it is the ONLY entry in this package that reads a raw mapping, which is §4's rule
and is asserted rather than reviewed:
``tests/test_import_rule.py::test_the_parser_is_the_only_entry_that_reads_a_raw_mapping``
holds it, ``::test_only_the_named_modules_read_a_declaration`` holds the three
sanctioned declaration readers §4 names, and
``::test_no_node_carries_the_mapping_it_was_parsed_from`` holds §14 step 5's own exit
condition -- no kind of §4's table declares a ``raw`` field, so no handler can reach the
document behind the parser.

**The dispatch is NOT here and is not ``emit``'s either.**  ``codegen/lower/decide.py``
is the exhaustive ``match`` over these kinds (§5's one dispatch, with ``assert_never``);
``emit.decide_type`` wraps it with the two things a node reached twice needs, which §5
keeps outside the route.  This docstring said for a while that ``parse.py`` was
unwritten and that ``emit._decide`` was the dispatch; both stopped being true when step
5 landed and neither ``emit._decide`` nor an unread ``nodes.py`` exists.  The symbol
``emit._decide`` survives in ``docs/plan/architecture.md`` §11's layer table, which is
the owner's document and not a lane's to edit.

``nodes.py`` was declared ahead of its reader, on the precedent row .2 set for the
descent column (``keywords.descends_at``: "Declared here; its readers are section 14
step 5's and are not built by this row"), and for the same reason -- the DECLARATION is
what the readers have to agree with, so it is worth having one of.
"""
