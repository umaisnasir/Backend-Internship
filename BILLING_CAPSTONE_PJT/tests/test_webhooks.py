import json

import stripe
from sqlalchemy import func, select

from app.constants import PlanCode
from app.models import (
    StripeWebhookEvent,
    Tenant,
)
from tests.conftest import TEST_TENANT_ID


def test_forged_webhook_is_rejected(
    client,
) -> None:
    response = client.post(
        "/webhooks/stripe",
        content=b'{"id":"evt_forged"}',
        headers={
            "Content-Type": (
                "application/json"
            ),
            "Stripe-Signature": (
                "t=123,v1=forged"
            ),
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Invalid Stripe webhook signature"
    )


def test_duplicate_webhook_is_ignored(
    client,
    session_factory,
    monkeypatch,
) -> None:
    event = {
        "id": "evt_checkout_completed_001",
        "type": (
            "checkout.session.completed"
        ),
        "data": {
            "object": {
                "id": "cs_test_001",
                "customer": "cus_test_001",
                "subscription": (
                    "sub_test_001"
                ),
                "client_reference_id": (
                    TEST_TENANT_ID
                ),
                "metadata": {
                    "tenant_id": (
                        TEST_TENANT_ID
                    ),
                },
            }
        },
    }

    monkeypatch.setattr(
        stripe.Webhook,
        "construct_event",
        lambda **kwargs: event,
    )

    payload = json.dumps(event).encode()

    headers = {
        "Content-Type": "application/json",
        "Stripe-Signature": (
            "test-signature"
        ),
    }

    first = client.post(
        "/webhooks/stripe",
        content=payload,
        headers=headers,
    )

    second = client.post(
        "/webhooks/stripe",
        content=payload,
        headers=headers,
    )

    assert first.status_code == 200
    assert first.json()["duplicate"] is False

    assert second.status_code == 200
    assert second.json()["duplicate"] is True

    with session_factory() as session:
        tenant = session.get(
            Tenant,
            TEST_TENANT_ID,
        )

        event_count = session.scalar(
            select(func.count())
            .select_from(
                StripeWebhookEvent
            )
        )

    assert tenant is not None

    assert (
        tenant.plan_code
        == PlanCode.PRO.value
    )

    assert (
        tenant.subscription_status
        == "active"
    )

    assert event_count == 1