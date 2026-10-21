"""The three spike cases, as the JSON Schema each route lowers. Shared so both
routes are measured on identical input."""

MONEY = {
    "title": "Money",
    "type": "object",
    "additionalProperties": False,
    "required": ["amount", "currency"],
    "properties": {
        "amount": {"type": "number", "minimum": 0},
        "currency": {"type": "string", "minLength": 3, "maxLength": 3, "pattern": "^[A-Z]{3}$"},
        "note": {"type": "string", "maxLength": 80},
    },
}

STATUS = {
    "title": "Media Buy Status",
    "type": "string",
    "enum": ["active", "paused", "completed"],
}

ACCOUNT_REF = {
    "title": "Account Ref",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "note": {"type": "string"},
        "by_id": {"type": "string", "minLength": 1},
        "by_name": {"type": "string", "minLength": 1},
    },
    "oneOf": [
        {"title": "Account Ref By Id", "required": ["by_id"]},
        {"title": "Account Ref By Name", "required": ["by_name"]},
    ],
}

CASES = {"Money": MONEY, "MediaBuyStatus": STATUS, "AccountRefBranches": ACCOUNT_REF}
