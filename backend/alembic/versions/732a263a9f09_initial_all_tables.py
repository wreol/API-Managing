"""initial: all tables

Revision ID: 732a263a9f09
Revises:
Create Date: 2026-06-14 14:40:55.825637
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '732a263a9f09'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -- users ---------------------------------------------------------------
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('oauth_provider', sa.String(20), nullable=True),
        sa.Column('oauth_id', sa.String(255), nullable=True),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False,
                  server_default=sa.text('true')),
        sa.Column('email_verified', sa.Boolean(), nullable=False,
                  server_default=sa.text('false')),
        sa.Column('notification_email', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # -- api_keys ------------------------------------------------------------
    op.create_table(
        'api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id'), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('label', sa.String(200), nullable=False),
        sa.Column('key_encrypted', sa.Text(), nullable=False),
        sa.Column('key_prefix', sa.String(20), nullable=False),
        sa.Column('last_4', sa.String(4), nullable=False),
        sa.Column('tags', postgresql.JSONB(), nullable=True,
                  server_default=sa.text("'[]'::jsonb")),
        sa.Column('is_active', sa.Boolean(), nullable=False,
                  server_default=sa.text('true')),
        sa.Column('status', sa.String(20), nullable=False,
                  server_default=sa.text("'ok'")),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )
    op.create_index('ix_api_keys_user_id', 'api_keys', ['user_id'])

    # -- usage_records -------------------------------------------------------
    op.create_table(
        'usage_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('key_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('api_keys.id'), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('fetched_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('calls', sa.Integer(), nullable=False,
                  server_default=sa.text('0')),
        sa.Column('tokens_in', sa.BigInteger(), nullable=False,
                  server_default=sa.text('0')),
        sa.Column('tokens_out', sa.BigInteger(), nullable=False,
                  server_default=sa.text('0')),
        sa.Column('cost_estimate', sa.Numeric(10, 4), nullable=True),
        sa.Column('raw_response', postgresql.JSONB(), nullable=True),
    )
    op.create_index('ix_usage_records_key_id', 'usage_records', ['key_id'])

    # -- key_shares ----------------------------------------------------------
    op.create_table(
        'key_shares',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('key_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('api_keys.id'), nullable=False),
        sa.Column('shared_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id'), nullable=False),
        sa.Column('shared_with', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id'), nullable=False),
        sa.Column('permission', sa.String(10), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )

    # -- alert_rules ---------------------------------------------------------
    op.create_table(
        'alert_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id'), nullable=False),
        sa.Column('key_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('api_keys.id'), nullable=True),
        sa.Column('provider', sa.String(50), nullable=True),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('threshold', sa.Numeric(12, 4), nullable=False),
        sa.Column('notify_email', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False,
                  server_default=sa.text('true')),
    )

    # -- alert_events --------------------------------------------------------
    op.create_table(
        'alert_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('rule_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('alert_rules.id'), nullable=False),
        sa.Column('triggered_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column('threshold_pct', sa.Numeric(5, 2), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False,
                  server_default=sa.text('false')),
        sa.Column('email_sent', sa.Boolean(), nullable=False,
                  server_default=sa.text('false')),
    )

    # -- audit_logs ----------------------------------------------------------
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id'), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )


def downgrade() -> None:
    # Must drop tables in reverse dependency order (children before parents).
    op.drop_table('audit_logs')
    op.drop_table('alert_events')
    op.drop_table('alert_rules')
    op.drop_table('key_shares')
    op.drop_index('ix_usage_records_key_id', table_name='usage_records')
    op.drop_table('usage_records')
    op.drop_index('ix_api_keys_user_id', table_name='api_keys')
    op.drop_table('api_keys')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
