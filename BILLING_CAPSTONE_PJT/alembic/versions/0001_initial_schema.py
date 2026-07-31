"""Create the billing data model."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_initial_schema"

down_revision: Union[str, None] = None

branch_labels: Union[
    str,
    Sequence[str],
    None,
] = None

depends_on: Union[
    str,
    Sequence[str],
    None,
] = None


def upgrade() -> None:
    op.create_table(
        "plans",
        sa.Column(
            "code",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "monthly_price_cents",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "api_call_limit",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "ai_token_limit",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "stripe_price_id",
            sa.String(length=255),
            nullable=True,
        ),
        sa.CheckConstraint(
            "monthly_price_cents >= 0",
            name=(
                "ck_plan_price_nonnegative"
            ),
        ),
        sa.CheckConstraint(
            "api_call_limit >= 0",
            name=(
                "ck_plan_call_limit_nonnegative"
            ),
        ),
        sa.CheckConstraint(
            "ai_token_limit >= 0",
            name=(
                "ck_plan_token_limit_nonnegative"
            ),
        ),
        sa.PrimaryKeyConstraint("code"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint(
            "stripe_price_id"
        ),
    )

    op.create_table(
        "tenants",
        sa.Column(
            "id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=120),
            nullable=False,
        ),
        sa.Column(
            "email",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "plan_code",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "subscription_status",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "stripe_customer_id",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["plan_code"],
            ["plans.code"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint(
            "stripe_customer_id"
        ),
    )

    op.create_index(
        "ix_tenants_email",
        "tenants",
        ["email"],
    )

    op.create_index(
        "ix_tenants_plan_code",
        "tenants",
        ["plan_code"],
    )

    op.create_index(
        "ix_tenants_stripe_customer_id",
        "tenants",
        ["stripe_customer_id"],
    )

    op.create_table(
        "usage_events",
        sa.Column(
            "id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "usage_type",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "idempotency_key",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "quantity",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "input_tokens",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "cached_input_tokens",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "output_tokens",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "reasoning_tokens",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "cost_nano_usd",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "pricing_version",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "quantity > 0",
            name="ck_usage_quantity_positive",
        ),
        sa.CheckConstraint(
            "input_tokens >= 0",
            name="ck_usage_input_nonnegative",
        ),
        sa.CheckConstraint(
            "cached_input_tokens >= 0",
            name="ck_usage_cached_nonnegative",
        ),
        sa.CheckConstraint(
            "output_tokens >= 0",
            name="ck_usage_output_nonnegative",
        ),
        sa.CheckConstraint(
            "reasoning_tokens >= 0",
            name=(
                "ck_usage_reasoning_nonnegative"
            ),
        ),
        sa.CheckConstraint(
            (
                "cached_input_tokens "
                "<= input_tokens"
            ),
            name="ck_usage_cached_within_input",
        ),
        sa.CheckConstraint(
            (
                "reasoning_tokens "
                "<= output_tokens"
            ),
            name=(
                "ck_usage_reasoning_within_output"
            ),
        ),
        sa.CheckConstraint(
            "cost_nano_usd >= 0",
            name="ck_usage_cost_nonnegative",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "idempotency_key",
            name=(
                "uq_usage_tenant_idempotency"
            ),
        ),
    )

    op.create_index(
        "ix_usage_events_tenant_id",
        "usage_events",
        ["tenant_id"],
    )

    op.create_index(
        "ix_usage_events_usage_type",
        "usage_events",
        ["usage_type"],
    )

    op.create_index(
        "ix_usage_events_occurred_at",
        "usage_events",
        ["occurred_at"],
    )

    op.create_table(
        "subscriptions",
        sa.Column(
            "id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "stripe_subscription_id",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "stripe_checkout_session_id",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "stripe_price_id",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "current_period_end",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "cancel_at_period_end",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "stripe_subscription_id"
        ),
        sa.UniqueConstraint(
            "stripe_checkout_session_id"
        ),
        sa.UniqueConstraint("tenant_id"),
    )

    op.create_index(
        "ix_subscriptions_tenant_id",
        "subscriptions",
        ["tenant_id"],
    )

    op.create_index(
        (
            "ix_subscriptions_"
            "stripe_subscription_id"
        ),
        "subscriptions",
        ["stripe_subscription_id"],
    )

    op.create_table(
        "stripe_webhook_events",
        sa.Column(
            "stripe_event_id",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "event_type",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "stripe_event_id"
        ),
    )


def downgrade() -> None:
    op.drop_table(
        "stripe_webhook_events"
    )

    op.drop_index(
        (
            "ix_subscriptions_"
            "stripe_subscription_id"
        ),
        table_name="subscriptions",
    )

    op.drop_index(
        "ix_subscriptions_tenant_id",
        table_name="subscriptions",
    )

    op.drop_table("subscriptions")

    op.drop_index(
        "ix_usage_events_occurred_at",
        table_name="usage_events",
    )

    op.drop_index(
        "ix_usage_events_usage_type",
        table_name="usage_events",
    )

    op.drop_index(
        "ix_usage_events_tenant_id",
        table_name="usage_events",
    )

    op.drop_table("usage_events")

    op.drop_index(
        "ix_tenants_stripe_customer_id",
        table_name="tenants",
    )

    op.drop_index(
        "ix_tenants_plan_code",
        table_name="tenants",
    )

    op.drop_index(
        "ix_tenants_email",
        table_name="tenants",
    )

    op.drop_table("tenants")
    op.drop_table("plans")