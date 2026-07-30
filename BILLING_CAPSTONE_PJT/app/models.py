from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_uuid() -> str:
    return str(uuid4())


class Plan(Base):
    __tablename__ = "plans"

    code: Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
    )

    monthly_price_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    api_call_limit: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    ai_token_limit: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    stripe_price_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
    )

    tenants: Mapped[list["Tenant"]] = relationship(
        back_populates="plan",
    )

    __table_args__ = (
        CheckConstraint(
            "monthly_price_cents >= 0",
            name="ck_plan_price_nonnegative",
        ),
        CheckConstraint(
            "api_call_limit >= 0",
            name="ck_plan_call_limit_nonnegative",
        ),
        CheckConstraint(
            "ai_token_limit >= 0",
            name="ck_plan_token_limit_nonnegative",
        ),
    )


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=new_uuid,
    )

    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    plan_code: Mapped[str] = mapped_column(
        ForeignKey(
            "plans.code",
            ondelete="RESTRICT",
        ),
        nullable=False,
        default="free",
        index=True,
    )

    subscription_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="active",
    )

    stripe_customer_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
        server_default=func.now(),
    )

    plan: Mapped[Plan] = relationship(
        back_populates="tenants",
    )

    usage_events: Mapped[list["UsageEvent"]] = relationship(
        back_populates="tenant",
        cascade="all, delete-orphan",
    )

    subscription: Mapped["Subscription | None"] = relationship(
        back_populates="tenant",
        cascade="all, delete-orphan",
        uselist=False,
    )


class UsageEvent(Base):
    __tablename__ = "usage_events"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=new_uuid,
    )

    tenant_id: Mapped[str] = mapped_column(
        ForeignKey(
            "tenants.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    usage_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    idempotency_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    input_tokens: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )

    cached_input_tokens: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )

    output_tokens: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )

    reasoning_tokens: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )

    cost_nano_usd: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    pricing_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
        index=True,
    )

    tenant: Mapped[Tenant] = relationship(
        back_populates="usage_events",
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "idempotency_key",
            name="uq_usage_tenant_idempotency",
        ),
        CheckConstraint(
            "quantity > 0",
            name="ck_usage_quantity_positive",
        ),
        CheckConstraint(
            "input_tokens >= 0",
            name="ck_usage_input_nonnegative",
        ),
        CheckConstraint(
            "cached_input_tokens >= 0",
            name="ck_usage_cached_nonnegative",
        ),
        CheckConstraint(
            "output_tokens >= 0",
            name="ck_usage_output_nonnegative",
        ),
        CheckConstraint(
            "reasoning_tokens >= 0",
            name="ck_usage_reasoning_nonnegative",
        ),
        CheckConstraint(
            "cached_input_tokens <= input_tokens",
            name="ck_usage_cached_within_input",
        ),
        CheckConstraint(
            "reasoning_tokens <= output_tokens",
            name="ck_usage_reasoning_within_output",
        ),
        CheckConstraint(
            "cost_nano_usd >= 0",
            name="ck_usage_cost_nonnegative",
        ),
    )


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=new_uuid,
    )

    tenant_id: Mapped[str] = mapped_column(
        ForeignKey(
            "tenants.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    stripe_subscription_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
    )

    stripe_checkout_session_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
    )

    stripe_price_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    cancel_at_period_end: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
        server_default=func.now(),
    )

    tenant: Mapped[Tenant] = relationship(
        back_populates="subscription",
    )


class StripeWebhookEvent(Base):
    __tablename__ = "stripe_webhook_events"

    stripe_event_id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )