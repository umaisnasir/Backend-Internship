from datetime import UTC, datetime

import stripe
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.constants import PlanCode
from app.exceptions import (
    PlanNotFoundError,
    TenantNotFoundError,
)
from app.models import (
    Plan,
    StripeWebhookEvent,
    Subscription,
    Tenant,
)


class StripeService:
    def __init__(
        self,
        *,
        secret_key: str,
        webhook_secret: str,
        base_url: str,
    ) -> None:
        stripe.api_key = secret_key

        self.webhook_secret = (
            webhook_secret
        )

        self.base_url = (
            base_url.rstrip("/")
        )

    def create_checkout_session(
        self,
        session: Session,
        *,
        tenant_id: str,
        idempotency_key: str,
    ) -> stripe.checkout.Session:
        tenant = session.get(
            Tenant,
            tenant_id,
        )

        if tenant is None:
            raise TenantNotFoundError(
                f"Tenant {tenant_id} was not found"
            )

        pro_plan = session.get(
            Plan,
            PlanCode.PRO.value,
        )

        if (
            pro_plan is None
            or not pro_plan.stripe_price_id
        ):
            raise PlanNotFoundError(
                "The Pro Stripe price "
                "is not configured"
            )

        params: dict[str, object] = {
            "mode": "subscription",
            "line_items": [
                {
                    "price": (
                        pro_plan.stripe_price_id
                    ),
                    "quantity": 1,
                }
            ],
            "success_url": (
                f"{self.base_url}/checkout/success"
                "?session_id="
                "{CHECKOUT_SESSION_ID}"
            ),
            "cancel_url": (
                f"{self.base_url}/checkout/cancel"
            ),
            "client_reference_id": tenant.id,
            "customer_email": tenant.email,
            "metadata": {
                "tenant_id": tenant.id,
            },
            "subscription_data": {
                "metadata": {
                    "tenant_id": tenant.id,
                }
            },
        }

        if tenant.stripe_customer_id:
            params.pop("customer_email")

            params["customer"] = (
                tenant.stripe_customer_id
            )

        return stripe.checkout.Session.create(
            **params,
            idempotency_key=(
                f"tenant-checkout:"
                f"{tenant.id}:"
                f"{idempotency_key}"
            ),
        )

    def verify_event(
        self,
        *,
        payload: bytes,
        signature: str,
    ) -> stripe.Event:
        return stripe.Webhook.construct_event(
            payload=payload,
            sig_header=signature,
            secret=self.webhook_secret,
        )

    def process_event(
        self,
        session: Session,
        event: stripe.Event | dict,
    ) -> bool:
        event_id = str(event["id"])
        event_type = str(event["type"])

        existing = session.get(
            StripeWebhookEvent,
            event_id,
        )

        if existing is not None:
            return True

        try:
            # A savepoint prevents a concurrent duplicate
            # from rolling back the complete transaction.
            with session.begin_nested():
                session.add(
                    StripeWebhookEvent(
                        stripe_event_id=event_id,
                        event_type=event_type,
                    )
                )

                session.flush()

        except IntegrityError:
            return True

        data_object = (
            event["data"]["object"]
        )

        if (
            event_type
            == "checkout.session.completed"
        ):
            self._handle_checkout_completed(
                session,
                data_object,
            )

        elif (
            event_type
            == "customer.subscription.updated"
        ):
            self._handle_subscription_updated(
                session,
                data_object,
            )

        elif (
            event_type
            == "customer.subscription.deleted"
        ):
            self._handle_subscription_deleted(
                session,
                data_object,
            )

        return False

    def _handle_checkout_completed(
        self,
        session: Session,
        checkout: dict,
    ) -> None:
        metadata = (
            checkout.get("metadata")
            or {}
        )

        tenant_id = (
            metadata.get("tenant_id")
            or checkout.get(
                "client_reference_id"
            )
        )

        tenant = self._find_tenant(
            session,
            tenant_id=tenant_id,
            stripe_customer_id=(
                checkout.get("customer")
            ),
        )

        tenant.stripe_customer_id = (
            checkout.get("customer")
        )

        tenant.plan_code = (
            PlanCode.PRO.value
        )

        tenant.subscription_status = (
            "active"
        )

        subscription = (
            tenant.subscription
            or Subscription(
                tenant_id=tenant.id,
                status="active",
            )
        )

        subscription.stripe_checkout_session_id = (
            checkout.get("id")
        )

        subscription.stripe_subscription_id = (
            checkout.get("subscription")
        )

        subscription.status = "active"

        session.add(subscription)

    def _handle_subscription_updated(
        self,
        session: Session,
        stripe_subscription: dict,
    ) -> None:
        metadata = (
            stripe_subscription.get(
                "metadata"
            )
            or {}
        )

        tenant = self._find_tenant(
            session,
            tenant_id=metadata.get(
                "tenant_id"
            ),
            stripe_customer_id=(
                stripe_subscription.get(
                    "customer"
                )
            ),
            stripe_subscription_id=(
                stripe_subscription.get("id")
            ),
        )

        status = str(
            stripe_subscription.get(
                "status",
                "unknown",
            )
        )

        tenant.subscription_status = status
        tenant.plan_code = PlanCode.PRO.value

        subscription = (
            tenant.subscription
            or Subscription(
                tenant_id=tenant.id,
                status=status,
            )
        )

        subscription.stripe_subscription_id = (
            stripe_subscription.get("id")
        )

        subscription.stripe_price_id = (
            extract_price_id(
                stripe_subscription
            )
        )

        subscription.status = status

        subscription.cancel_at_period_end = bool(
            stripe_subscription.get(
                "cancel_at_period_end",
                False,
            )
        )

        subscription.current_period_end = (
            unix_to_datetime(
                stripe_subscription.get(
                    "current_period_end"
                )
            )
        )

        session.add(subscription)

    def _handle_subscription_deleted(
        self,
        session: Session,
        stripe_subscription: dict,
    ) -> None:
        metadata = (
            stripe_subscription.get(
                "metadata"
            )
            or {}
        )

        tenant = self._find_tenant(
            session,
            tenant_id=metadata.get(
                "tenant_id"
            ),
            stripe_customer_id=(
                stripe_subscription.get(
                    "customer"
                )
            ),
            stripe_subscription_id=(
                stripe_subscription.get("id")
            ),
        )

        tenant.plan_code = (
            PlanCode.FREE.value
        )

        tenant.subscription_status = (
            "canceled"
        )

        subscription = tenant.subscription

        if subscription is None:
            subscription = Subscription(
                tenant_id=tenant.id,
                status="canceled",
            )

        subscription.stripe_subscription_id = (
            stripe_subscription.get("id")
        )

        subscription.status = "canceled"

        subscription.current_period_end = (
            unix_to_datetime(
                stripe_subscription.get(
                    "current_period_end"
                )
            )
        )

        session.add(subscription)

    @staticmethod
    def _find_tenant(
        session: Session,
        *,
        tenant_id: str | None = None,
        stripe_customer_id: str | None = None,
        stripe_subscription_id: (
            str | None
        ) = None,
    ) -> Tenant:
        tenant = (
            session.get(Tenant, tenant_id)
            if tenant_id
            else None
        )

        if (
            tenant is None
            and stripe_customer_id
        ):
            tenant = session.scalar(
                select(Tenant).where(
                    Tenant.stripe_customer_id
                    == stripe_customer_id
                )
            )

        if (
            tenant is None
            and stripe_subscription_id
        ):
            tenant = session.scalar(
                select(Tenant)
                .join(Subscription)
                .where(
                    Subscription
                    .stripe_subscription_id
                    == stripe_subscription_id
                )
            )

        if tenant is None:
            raise TenantNotFoundError(
                "Stripe event could not be "
                "matched to a tenant"
            )

        return tenant


def extract_price_id(
    stripe_subscription: dict,
) -> str | None:
    items = (
        stripe_subscription
        .get("items", {})
        .get("data", [])
    )

    if not items:
        return None

    price = (
        items[0].get("price")
        or {}
    )

    return price.get("id")


def unix_to_datetime(
    value: int | None,
) -> datetime | None:
    if value is None:
        return None

    return datetime.fromtimestamp(
        int(value),
        tz=UTC,
    )