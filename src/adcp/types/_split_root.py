"""The one derivation for "which classes stand behind this name".

A schema root whose arms partition by requiredness is generated as a shared
base plus one class per arm, with the root's public name bound to a union over
the arms. Three places then need the same fact, and each got it wrong in its
own way before this existed:

* the ergonomic-coercion generator analyses a model's fields -- a union has
  none;
* the consolidated-export module rebuilds forward references -- a union has no
  ``model_rebuild``, and the generated comment beside those calls already said
  "only call model_rebuild() on actual classes, not Union type aliases" without
  any way to tell;
* ``_forward_compat`` patches a field and then rebuilds, and a patch to the
  base is invisible to an arm until that arm is rebuilt too, because a subclass
  caches its parent's annotations when it is built.

So the derivation lives here once. The base is read off an arm's MRO rather
than looked up by name or spelled out: the arms all name it, which is the
property the emitter's own tests grade, and reading it this way means this
module does not have to know how the base is spelled.
"""

from __future__ import annotations

from typing import Any, get_args

__all__ = ["classes_behind", "shared_base"]


def classes_behind(declared: Any) -> tuple[Any, ...]:
    """Every class the name stands for, base first, or just the model itself.

    For a split root: the shared base followed by each arm, which is the order
    a patch-then-rebuild needs -- the base carries the change and every arm has
    to be rebuilt to see it.
    """
    members = get_args(declared)
    if not members:
        return (declared,)
    return (members[0].__mro__[1], *members)


def shared_base(declared: Any) -> Any:
    """What carries the fields: the shared base for a split root, else the model.

    This is the target of anything that reads or patches a FIELD. The arms only
    change which fields are required, forbidden or pinned, so the field set is
    the base's and patching it once covers every arm.
    """
    return classes_behind(declared)[0]
