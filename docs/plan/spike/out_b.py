from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Money(BaseModel):
    model_config = ConfigDict(extra='forbid')
    amount: Annotated[float, Field(ge=0)]
    currency: Annotated[str, Field(min_length=3, max_length=3, pattern='^[A-Z]{3}$')]
    note: Annotated[str, Field(max_length=80)] | None = None


class MediaBuyStatus(str, Enum):
    active = 'active'
    paused = 'paused'
    completed = 'completed'


class AccountRef(BaseModel):
    model_config = ConfigDict(extra='forbid')
    note: str | None = None
    by_id: Annotated[str, Field(min_length=1)] | None = None
    by_name: Annotated[str, Field(min_length=1)] | None = None
    @model_validator(mode="after")
    def _one_of_required_groups(self):
        groups = (('by_id',), ('by_name',))
        present = {k for k in self.model_fields_set}
        if sum(all(n in present for n in g) for g in groups) != 1:
            raise ValueError("exactly one of the required groups must be present: " + repr(groups))
        return self


class AccountRefById(AccountRef):
    by_id: Annotated[str, Field(min_length=1)]


class AccountRefByName(AccountRef):
    by_name: Annotated[str, Field(min_length=1)]


AccountRefBranches = AccountRefById | AccountRefByName
