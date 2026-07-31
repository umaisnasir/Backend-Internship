from sqlalchemy import func, select

from app.models import UsageEvent
from tests.conftest import TEST_TENANT_ID


HEADERS = {
    "X-Tenant-ID": TEST_TENANT_ID,
    "Idempotency-Key": "request-0001",
}


def test_retried_request_does_not_double_count(
    client,
    session_factory,
) -> None:
    first = client.post(
        "/v1/actions/call",
        headers=HEADERS,
    )

    second = client.post(
        "/v1/actions/call",
        headers=HEADERS,
    )

    assert first.status_code == 200
    assert first.json()["duplicate"] is False

    assert second.status_code == 200
    assert second.json()["duplicate"] is True

    assert (
        first.json()["event_id"]
        == second.json()["event_id"]
    )

    with session_factory() as session:
        count = session.scalar(
            select(func.count())
            .select_from(UsageEvent)
        )

        total = session.scalar(
            select(
                func.sum(
                    UsageEvent.quantity
                )
            )
        )

    assert count == 1
    assert total == 1


def test_same_key_with_different_payload_is_conflict(
    client,
) -> None:
    first = client.post(
        "/v1/actions/call",
        headers=HEADERS,
    )

    second = client.post(
        "/v1/actions/ai",
        headers=HEADERS,
        json={
            "input_tokens": 10,
            "cached_input_tokens": 0,
            "output_tokens": 5,
            "reasoning_tokens": 2,
        },
    )

    assert first.status_code == 200
    assert second.status_code == 409


def test_limit_boundary_accepts_at_limit_then_rejects_over(
    client,
) -> None:
    first = client.post(
        "/v1/actions/call",
        headers={
            "X-Tenant-ID": TEST_TENANT_ID,
            "Idempotency-Key": (
                "boundary-0001"
            ),
        },
    )

    second = client.post(
        "/v1/actions/call",
        headers={
            "X-Tenant-ID": TEST_TENANT_ID,
            "Idempotency-Key": (
                "boundary-0002"
            ),
        },
    )

    third = client.post(
        "/v1/actions/call",
        headers={
            "X-Tenant-ID": TEST_TENANT_ID,
            "Idempotency-Key": (
                "boundary-0003"
            ),
        },
    )

    assert first.status_code == 200
    assert second.status_code == 200

    assert second.json()["remaining"] == 0

    assert third.status_code == 429
    assert third.json()["used"] == 2
    assert third.json()["limit"] == 2
    assert third.json()["requested"] == 1