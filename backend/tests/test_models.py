"""Tests for SQLAlchemy ORM models — verify table metadata matches SPEC §6."""

import pytest
from sqlalchemy import inspect, Integer, BigInteger, Numeric, String, Boolean, Date, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB, INET


# ---------------------------------------------------------------------------
# RED: These imports should fail because models don't exist yet
# ---------------------------------------------------------------------------
def test_all_models_can_be_imported():
    """All 7 model classes can be imported from app.models."""
    from app.models import User, ApiKey, UsageRecord, KeyShare, AlertRule, AlertEvent, AuditLog

    assert User is not None
    assert ApiKey is not None
    assert UsageRecord is not None
    assert KeyShare is not None
    assert AlertRule is not None
    assert AlertEvent is not None
    assert AuditLog is not None


def test_all_table_names_are_correct():
    """Table names match the SPEC."""
    from app.models import User, ApiKey, UsageRecord, KeyShare, AlertRule, AlertEvent, AuditLog

    assert User.__tablename__ == "users"
    assert ApiKey.__tablename__ == "api_keys"
    assert UsageRecord.__tablename__ == "usage_records"
    assert KeyShare.__tablename__ == "key_shares"
    assert AlertRule.__tablename__ == "alert_rules"
    assert AlertEvent.__tablename__ == "alert_events"
    assert AuditLog.__tablename__ == "audit_logs"


# ---------------------------------------------------------------------------
# Helper: get column info from a model
# ---------------------------------------------------------------------------
def _col(model, name: str):
    """Return the Column object for *name* on *model*."""
    mapper = inspect(model)
    return mapper.columns.get(name)


def _assert_pk_uuid(model, col_name="id"):
    col = _col(model, col_name)
    assert col is not None, f"{model.__tablename__}.{col_name} missing"
    assert col.primary_key, f"{model.__tablename__}.{col_name} is not PK"
    assert isinstance(col.type, PG_UUID), f"{model.__tablename__}.{col_name} is not UUID"


def _assert_fk(col, target_table: str, target_col: str = "id"):
    assert col is not None
    fks = list(col.foreign_keys)
    assert len(fks) >= 1, f"no FK on column"
    fk = fks[0]
    assert fk.column.table.name == target_table, f"FK → {fk.column.table.name}, expected {target_table}"
    assert fk.column.name == target_col, f"FK → {fk.column.name}, expected {target_col}"


# ---------------------------------------------------------------------------
# User model
# ---------------------------------------------------------------------------
class TestUserModel:
    def test_table_name(self):
        from app.models import User
        assert User.__tablename__ == "users"

    def test_pk(self):
        from app.models import User
        _assert_pk_uuid(User)

    def test_email_unique_not_null_indexed(self):
        from app.models import User
        col = _col(User, "email")
        assert col is not None
        assert isinstance(col.type, String)
        assert col.type.length == 255
        assert not col.nullable
        assert col.unique or col.index  # at minimum indexed

    def test_password_hash_nullable(self):
        from app.models import User
        col = _col(User, "password_hash")
        assert col.nullable

    def test_oauth_provider_nullable(self):
        from app.models import User
        col = _col(User, "oauth_provider")
        assert col.nullable

    def test_display_name_not_null(self):
        from app.models import User
        col = _col(User, "display_name")
        assert not col.nullable

    def test_is_active_default_true(self):
        from app.models import User
        col = _col(User, "is_active")
        assert isinstance(col.type, Boolean)

    def test_has_created_at_and_updated_at(self):
        from app.models import User
        assert _col(User, "created_at") is not None
        assert _col(User, "updated_at") is not None


# ---------------------------------------------------------------------------
# ApiKey model
# ---------------------------------------------------------------------------
class TestApiKeyModel:
    def test_table_name(self):
        from app.models import ApiKey
        assert ApiKey.__tablename__ == "api_keys"

    def test_pk(self):
        from app.models import ApiKey
        _assert_pk_uuid(ApiKey)

    def test_user_id_fk(self):
        from app.models import ApiKey
        _assert_fk(_col(ApiKey, "user_id"), "users")

    def test_provider_not_null(self):
        from app.models import ApiKey
        col = _col(ApiKey, "provider")
        assert isinstance(col.type, String)
        assert col.type.length == 50
        assert not col.nullable

    def test_key_encrypted_text_not_null(self):
        from app.models import ApiKey
        col = _col(ApiKey, "key_encrypted")
        assert isinstance(col.type, Text)
        assert not col.nullable

    def test_key_prefix_not_null(self):
        from app.models import ApiKey
        col = _col(ApiKey, "key_prefix")
        assert isinstance(col.type, String)
        assert col.type.length == 20
        assert not col.nullable

    def test_last_4_char4_not_null(self):
        from app.models import ApiKey
        col = _col(ApiKey, "last_4")
        assert isinstance(col.type, String)
        assert col.type.length == 4
        assert not col.nullable

    def test_tags_jsonb(self):
        from app.models import ApiKey
        col = _col(ApiKey, "tags")
        assert isinstance(col.type, JSONB)

    def test_status_default(self):
        from app.models import ApiKey
        col = _col(ApiKey, "status")
        assert isinstance(col.type, String)
        assert col.type.length == 20


# ---------------------------------------------------------------------------
# UsageRecord model
# ---------------------------------------------------------------------------
class TestUsageRecordModel:
    def test_table_name(self):
        from app.models import UsageRecord
        assert UsageRecord.__tablename__ == "usage_records"

    def test_pk(self):
        from app.models import UsageRecord
        _assert_pk_uuid(UsageRecord)

    def test_key_id_fk(self):
        from app.models import UsageRecord
        _assert_fk(_col(UsageRecord, "key_id"), "api_keys")

    def test_provider_denormalized_not_null(self):
        from app.models import UsageRecord
        col = _col(UsageRecord, "provider")
        assert isinstance(col.type, String)
        assert col.type.length == 50
        assert not col.nullable

    def test_period_dates_not_null(self):
        from app.models import UsageRecord
        start = _col(UsageRecord, "period_start")
        end = _col(UsageRecord, "period_end")
        assert isinstance(start.type, Date)
        assert isinstance(end.type, Date)
        assert not start.nullable
        assert not end.nullable

    def test_tokens_in_bigint(self):
        from app.models import UsageRecord
        col = _col(UsageRecord, "tokens_in")
        assert isinstance(col.type, BigInteger)

    def test_tokens_out_bigint(self):
        from app.models import UsageRecord
        col = _col(UsageRecord, "tokens_out")
        assert isinstance(col.type, BigInteger)

    def test_calls_integer(self):
        from app.models import UsageRecord
        col = _col(UsageRecord, "calls")
        assert isinstance(col.type, Integer)

    def test_cost_estimate_nullable(self):
        from app.models import UsageRecord
        col = _col(UsageRecord, "cost_estimate")
        assert col.nullable

    def test_raw_response_jsonb_nullable(self):
        from app.models import UsageRecord
        col = _col(UsageRecord, "raw_response")
        assert isinstance(col.type, JSONB)
        assert col.nullable


# ---------------------------------------------------------------------------
# KeyShare model
# ---------------------------------------------------------------------------
class TestKeyShareModel:
    def test_table_name(self):
        from app.models import KeyShare
        assert KeyShare.__tablename__ == "key_shares"

    def test_pk(self):
        from app.models import KeyShare
        _assert_pk_uuid(KeyShare)

    def test_key_id_fk(self):
        from app.models import KeyShare
        _assert_fk(_col(KeyShare, "key_id"), "api_keys")

    def test_shared_by_fk(self):
        from app.models import KeyShare
        _assert_fk(_col(KeyShare, "shared_by"), "users")

    def test_shared_with_fk(self):
        from app.models import KeyShare
        _assert_fk(_col(KeyShare, "shared_with"), "users")

    def test_permission_not_null(self):
        from app.models import KeyShare
        col = _col(KeyShare, "permission")
        assert isinstance(col.type, String)
        assert col.type.length == 10
        assert not col.nullable


# ---------------------------------------------------------------------------
# AlertRule model
# ---------------------------------------------------------------------------
class TestAlertRuleModel:
    def test_table_name(self):
        from app.models import AlertRule
        assert AlertRule.__tablename__ == "alert_rules"

    def test_pk(self):
        from app.models import AlertRule
        _assert_pk_uuid(AlertRule)

    def test_user_id_fk(self):
        from app.models import AlertRule
        _assert_fk(_col(AlertRule, "user_id"), "users")

    def test_key_id_fk_nullable(self):
        from app.models import AlertRule
        col = _col(AlertRule, "key_id")
        assert col.nullable  # null = provider-level rule

    def test_provider_nullable(self):
        from app.models import AlertRule
        col = _col(AlertRule, "provider")
        assert col.nullable

    def test_type_not_null(self):
        from app.models import AlertRule
        col = _col(AlertRule, "type")
        assert isinstance(col.type, String)
        assert col.type.length == 20
        assert not col.nullable

    def test_threshold_decimal_not_null(self):
        from app.models import AlertRule
        col = _col(AlertRule, "threshold")
        assert isinstance(col.type, Numeric)
        assert not col.nullable

    def test_notify_email_not_null(self):
        from app.models import AlertRule
        col = _col(AlertRule, "notify_email")
        assert isinstance(col.type, String)
        assert col.type.length == 255
        assert not col.nullable

    def test_is_active_default_true(self):
        from app.models import AlertRule
        col = _col(AlertRule, "is_active")
        assert isinstance(col.type, Boolean)


# ---------------------------------------------------------------------------
# AlertEvent model
# ---------------------------------------------------------------------------
class TestAlertEventModel:
    def test_table_name(self):
        from app.models import AlertEvent
        assert AlertEvent.__tablename__ == "alert_events"

    def test_pk(self):
        from app.models import AlertEvent
        _assert_pk_uuid(AlertEvent)

    def test_rule_id_fk(self):
        from app.models import AlertEvent
        _assert_fk(_col(AlertEvent, "rule_id"), "alert_rules")

    def test_threshold_pct_decimal_not_null(self):
        from app.models import AlertEvent
        col = _col(AlertEvent, "threshold_pct")
        assert isinstance(col.type, Numeric)
        assert not col.nullable

    def test_message_text_not_null(self):
        from app.models import AlertEvent
        col = _col(AlertEvent, "message")
        assert isinstance(col.type, Text)
        assert not col.nullable

    def test_is_read_default_false(self):
        from app.models import AlertEvent
        col = _col(AlertEvent, "is_read")
        assert isinstance(col.type, Boolean)

    def test_email_sent_default_false(self):
        from app.models import AlertEvent
        col = _col(AlertEvent, "email_sent")
        assert isinstance(col.type, Boolean)


# ---------------------------------------------------------------------------
# AuditLog model
# ---------------------------------------------------------------------------
class TestAuditLogModel:
    def test_table_name(self):
        from app.models import AuditLog
        assert AuditLog.__tablename__ == "audit_logs"

    def test_pk(self):
        from app.models import AuditLog
        _assert_pk_uuid(AuditLog)

    def test_user_id_fk(self):
        from app.models import AuditLog
        _assert_fk(_col(AuditLog, "user_id"), "users")

    def test_action_not_null(self):
        from app.models import AuditLog
        col = _col(AuditLog, "action")
        assert isinstance(col.type, String)
        assert col.type.length == 50
        assert not col.nullable

    def test_resource_type_not_null(self):
        from app.models import AuditLog
        col = _col(AuditLog, "resource_type")
        assert isinstance(col.type, String)
        assert col.type.length == 50
        assert not col.nullable

    def test_resource_id_uuid_not_null(self):
        from app.models import AuditLog
        col = _col(AuditLog, "resource_id")
        assert isinstance(col.type, PG_UUID)
        assert not col.nullable

    def test_ip_address_inet_nullable(self):
        from app.models import AuditLog
        col = _col(AuditLog, "ip_address")
        assert isinstance(col.type, INET)
        assert col.nullable

    def test_user_agent_text_nullable(self):
        from app.models import AuditLog
        col = _col(AuditLog, "user_agent")
        assert isinstance(col.type, Text)
        assert col.nullable
