"""``adcp.types.domains.<domain>.<document>`` -- v9.6's module layout, as a COMPATIBILITY
mirror of the private tree and never as a second public path.

**WHAT FORCES IT.**  ``docs/plan/rebuild-plan.md`` §1 writes a document's module to
``adcp.types._schemas.<domain>.<document>`` and gives each class ONE public path, the
domain surface ``adcp.types.<domain>``.  v9.6 published the generated tree itself, at
``adcp.types.domains.<domain>.<document>``, and the machinery this release keeps is written
against that layout: measured over ``src/adcp/`` less ``src/adcp/types/``, **1,423
module-scope ``(module, name)`` imports from ``adcp.types*``, of which 792 resolve and 92
distinct pairs are blocked because 91 modules under ``adcp.types.domains.*`` do not
exist**.  Because the imports are at MODULE SCOPE one absent module takes the whole
importing file and every name it carried, so the layout has to resolve for the kept
machinery to import at all.  All 91 have an exact counterpart under ``_schemas`` -- 91 of
91 -- so what is owed is a second NAME for a module, not a second module.

**AND IT IS NOT A SECOND PUBLIC PATH, which is the clause that keeps ``final-state.md``
reading 6 true.**  Reading 6 is "``from adcp.types.<domain> import <Name>`` reaches every
class the tree declares -- roots, union branches and aliases alike -- at exactly one such
path", and it is stated over the DOMAIN surface.  The gate that holds it
(``tests_emit/test_the_domain_surface.py``) derives its population from the compiler's own
export record (``emit.surface``, keyed on the modules the run wrote under ``_schemas``), so
the paths it counts are ``adcp.types.<domain>.<Name>`` and nothing else.  This module adds
none of those.  It is a compatibility surface in the sense ``adcp.types.compat`` is one --
the spelling an application has already written, resolving to the one object -- and the
gate is not widened to tolerate it, because the gate never ranges over it.

**NOTHING HERE IS A DECLARATION, and the identity is structural rather than per name.**  A
mirror module IS the private module: the import system is handed the object
``adcp.types._schemas.<rest>`` already built, bound in ``sys.modules`` under the second
name, so

    adcp.types.domains.core.account.Account is adcp.types._schemas.core.account.Account

holds by construction and cannot be half true.  The count of class declarations does not
move, there is one ``__adcp_schema__`` per class, and ``isinstance`` holds across both
spellings.  An alias is a name, never a second type -- and a re-export written per name
could still have been a second type per name, which this arrangement cannot be.

**THERE IS NO MODULE LIST, which is why the mirror cannot go stale.**  The mapping is one
prefix substitution, ``<this package>.<rest>`` -> ``<its parent>._schemas.<rest>``, read
off ``__name__`` at import time and resolved against whatever ``adcp.types._schemas`` the
process has bound.  A document added upstream is mirrored with nothing regenerated; a
document that stops emitting stops being mirrored in the same breath, so there is no stale
module left behind importing a name no module declares.  It also means the mirror follows
``tests_emit/fresh.py``'s fresh tree rather than the committed one, so no reader can be
handed a mirror of one compiler over a tree from another.

**THE FINDER GOES IN FRONT OF ``PathFinder`` AND THAT IS LOAD-BEARING, not an ordering
preference.**  The parent of ``adcp.types.domains.core.account`` is the module object
``adcp.types._schemas.core``, whose ``__path__`` is the REAL directory -- so a ``PathFinder``
consulted first finds ``account.py`` sitting there and executes it a SECOND time under the
mirror name, minting a second class for every node of the document, with a second
``__adcp_schema__`` and an ``isinstance`` that is false against the class the runtime
validates into.  That is the exact defect §1's one-path rule exists to make
unrepresentable, so the finder is INSERTED at the head of ``sys.meta_path`` and the red
direction is asserted rather than argued
(``tests_emit/test_the_compat_mirror.py::test_the_finder_in_front_of_the_path_finder_is_what_stops_a_second_class``).

**HOW THE ALIAS IS MADE, and why it is the loader's ``sys.modules`` write rather than a
module returned from ``create_module``.**  ``importlib._bootstrap._init_module_attrs``
sets ``__spec__`` UNCONDITIONALLY, so a loader handing back the private module would stamp
the mirror's spec onto it -- ``adcp.types._schemas.core.account.__spec__.name`` would then
say ``adcp.types.domains.core.account``, and every reader that resolves a module through
its spec would be told the private tree lives at the compatibility path.  CPython's own
answer is the case its comment in ``_load_unlocked`` names: *"We don't ensure that the
import-related module attributes get set in the sys.modules replacement case."*  A fresh
throwaway module is created from the spec, :meth:`_Mirror.exec_module` replaces it in
``sys.modules`` with the private one, and ``_load_unlocked`` returns what it finds there.
The private module is never mutated, and the parent attribute the import system sets
afterwards is set to the same object it already held.

**THIS FILE IS AN EMITTED ARTIFACT.**  It is written by ``codegen/mirror/__init__.py`` from
``emit.write``'s own writing stage, into ``adcp/types/domains/__init__.py`` beside the
tree, so it is regenerated whenever the tree is and nobody maintains it by hand.  In its
home under ``codegen/`` the guard at the foot of this module is FALSE -- there is no
``codegen.mirror._schemas`` to mirror -- so importing it there installs nothing, which is
the one sentence that makes a verbatim artifact safe to keep as real, parseable Python
instead of as a string.
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from importlib.machinery import ModuleSpec
from types import ModuleType

#: This package's own dotted name.  Read off ``__name__`` and never written down, so the
#: mirror does not carry a second spelling of where it was installed.
MIRROR = __name__

#: The private tree this package mirrors: ``_schemas`` beside it, under the same parent.
#: ``adcp.types.domains`` -> ``adcp.types._schemas``.
GENERATED = f"{MIRROR.rpartition('.')[0]}._schemas"


def generated(fullname: str) -> str:
    """The private name ``fullname`` mirrors.

    The whole of the mapping, and the reason there is no list: a mirror name is its
    private counterpart with one prefix swapped, at any depth, so
    ``adcp.types.domains.core.requirements.asset_requirements`` resolves exactly as
    ``adcp.types.domains.core.account`` does.
    """
    return GENERATED + fullname[len(MIRROR) :]


class _Mirror:
    """A finder and loader that binds ``<MIRROR>.<rest>`` to the module ``<GENERATED>.<rest>``
    already IS.

    Both halves in one object because they are one decision: the spec says which private
    module a mirror name resolves to, and the load is the ``sys.modules`` write that makes
    the two names one object.  A loader that defines ``exec_module`` must define
    ``create_module`` (``importlib.util.module_from_spec``), and this one returns ``None``
    on purpose -- the throwaway module the import system then builds is what keeps the
    private module's own attributes out of reach.
    """

    #: What this instance mirrors, for the re-import guard at the foot of the module.  A
    #: marker on the instance rather than an ``isinstance`` check, because a reloaded
    #: module defines a NEW class and the old instance would not be an instance of it.
    mirrors = MIRROR

    def find_spec(
        self,
        fullname: str,
        path: object = None,
        target: ModuleType | None = None,
    ) -> ModuleSpec | None:
        """A spec for a mirror name whose private counterpart exists, else ``None``.

        ``None`` for everything outside the mirror, which is what makes a finder at the
        head of ``sys.meta_path`` cheap and inert for every other import in the process.

        The counterpart is resolved with ``find_spec`` and not by importing it, so a
        private module that raises for its OWN reasons raises from
        :meth:`exec_module` with its own traceback rather than being swallowed into a
        ``ModuleNotFoundError`` about the compatibility path.
        """
        if not fullname.startswith(f"{MIRROR}."):
            return None
        try:
            private = importlib.util.find_spec(generated(fullname))
        except (ImportError, AttributeError, ValueError):
            return None
        if private is None:
            return None
        spec = ModuleSpec(fullname, self, origin=private.origin)
        if private.submodule_search_locations is not None:
            # A PACKAGE, so the mirror name must carry search locations too -- the import
            # system reads them off the PARENT when it resolves a child, and this finder
            # is what answers for the child whatever they say.
            spec.submodule_search_locations = list(private.submodule_search_locations)
        return spec

    def create_module(self, spec: ModuleSpec) -> ModuleType | None:
        """``None``: let the import system build a throwaway module from the spec.

        Returning the private module here would be the obvious shape and is the wrong one
        -- ``_init_module_attrs`` sets ``__spec__`` unconditionally, so it would rewrite
        the private module's own spec.  See this module's docstring.
        """
        return None

    def exec_module(self, module: ModuleType) -> None:
        """Replace the throwaway module with the private one, under the mirror's name.

        ``_load_unlocked`` re-reads ``sys.modules[spec.name]`` after this returns and hands
        back what it finds, which is CPython's own supported arrangement for an alias.
        """
        name = module.__name__
        sys.modules[name] = importlib.import_module(generated(name))

    def invalidate_caches(self) -> None:
        """Nothing is cached here: every answer is re-derived from the private tree."""


def installed() -> bool:
    """Is a mirror for :data:`MIRROR` already on ``sys.meta_path``.

    Read off a MARKER on the instance and not by ``isinstance``, because a reloaded module
    defines a new class and the live instance would not be an instance of it -- and two
    finders answering the same names is the one failure a re-import can introduce here.
    """
    return any(getattr(finder, "mirrors", None) == MIRROR for finder in sys.meta_path)


def there_is_a_tree_to_mirror() -> bool:
    """Does a private tree sit beside this package for the mirror to resolve into.

    **This is the whole of what makes the file inert where it is authored.**  It is true at
    ``adcp.types.domains``, where ``adcp.types._schemas`` is the emitted tree, and false at
    ``codegen.mirror.domains``, where nothing of the sort exists -- so importing the
    artifact in its own home installs no finder, and the artifact can stay real, parseable
    Python instead of a string held by a module of the compiler.

    Cheap, and it imports no document: ``find_spec`` locates ``_schemas`` without executing
    it, and ``_schemas/__init__.py`` is empty in any case.
    """
    try:
        return importlib.util.find_spec(GENERATED) is not None
    except (ImportError, AttributeError, ValueError):
        return False


if not installed() and there_is_a_tree_to_mirror():
    sys.meta_path.insert(0, _Mirror())
