# The measurement probe — NOT part of the wheel, and never imported by the tree

`sitecustomize.py` here is on no import path unless this directory is put on `PYTHONPATH`
and `FWVM_PROBE=1` is set, which only `run-the-behavioural-suite.sh` does. Nothing in `src/`
reaches it, no gate of ours grades through it, and `./check` does not see it.

**WHAT IT IS FOR.** Upstream's 577 behavioural files are the one measurement of reading 10
that is not a claim about our own table — "a table complete against itself proves nothing
here, because the thing being claimed is about an import someone else already wrote." The
probe resolves the names the alias layer does not yet carry so the suite can be asked what
lies BEHIND them, and every approximation it makes is numbered in its own source with the
reading that forbids making it permanent.

**THE FOUR PATCHES, each recorded at its site:**

1. the node-keyed map (`probe_map.json`, 2,626 rows) — built by `build_map.py` from the two
   `dump_side.py` dumps, by `survey/dropin_blocking.py`'s own four rules: upstream's defining
   module names the DOCUMENT, our declarations from that document are the candidates, identity
   is a GATE on that candidate set and never the proposal, and a row no rule resolves is left
   UNRESOLVED. This is the part that belongs in the tree, as alias statements — see
   `adcp-client-python-5z7a` and the migration guide's §10.
2. `_generated` as the lazy alias module it is (`gen_bind.json`) — 2,971 re-exports resolved
   on demand, because eager one absent name takes `aliases.py` with it.
3. a pass-through for the TWO private validators upstream's generator wrote onto a generated
   class — machinery this project does not emit and cannot derive from a schema (reading 10).
   **AN APPROXIMATION, and it is not a decision.**
4. two patches to upstream's own kept `aliases.py`: the `const`-as-`default` scan
   (`adcp-client-python-0hp7`, RULED theirs) and the nodeless `TmpxMacro` import
   (`adcp-client-python-m88n`). Neither mints a class and neither widens a type.

**RE-DERIVE EVERY FIGURE:**

    $UP/bin/python   survey/probes/dump_side.py adcp.types.domains   up.dom.json
    PYTHONPATH=.:src python survey/probes/dump_side.py adcp.types._schemas our.sch.json
    python survey/probes/build_map.py
    survey/probes/run-the-behavioural-suite.sh <label>
