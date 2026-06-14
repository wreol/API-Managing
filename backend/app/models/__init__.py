"""SQLAlchemy ORM models for API Vault.

All model classes are re-exported so they can be imported as:
    from app.models import User, ApiKey, ...

The Base class is declared in user.py and re-exported here.
"""

# ---------------------------------------------------------------------------
# Python 3.14 compatibility: SQLAlchemy 2.0.x's make_union_type() uses
#   cast(Any, Union).__getitem__(types)
# which fails on Python 3.14 because Union.__getitem__ requires a real
# typing.Union object, not a bare class received via cast().
# ---------------------------------------------------------------------------
import sys
from typing import Union as _Union

if sys.version_info >= (3, 14):
    import sqlalchemy.util.typing as _sa_typing

    _sa_typing.make_union_type = lambda *types: (
        _Union[types] if len(types) > 1 else types[0]
    )

from app.models.user import Base, User
from app.models.api_key import ApiKey
from app.models.usage_record import UsageRecord
from app.models.key_share import KeyShare
from app.models.alert_rule import AlertRule
from app.models.alert_event import AlertEvent
from app.models.audit_log import AuditLog

__all__ = [
    "Base",
    "User",
    "ApiKey",
    "UsageRecord",
    "KeyShare",
    "AlertRule",
    "AlertEvent",
    "AuditLog",
]

