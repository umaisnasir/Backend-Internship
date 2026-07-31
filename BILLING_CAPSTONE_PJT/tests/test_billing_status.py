from app.constants import PlanCode
from app.models import Tenant
from tests.conftest import TEST_TENANT_ID


def test_inactive_pro_subscription_returns_402(
    client,
    session_factory,
) -> None:
    with session_factory.begin() as session:
        tenant = session.get(
            Tenant,
            TEST_TENANT_ID,
        )

        assert tenant is not None

        tenant.plan_code = (
            PlanCode.PRO.value
        )

        tenant.subscription_status = (
            "past_due"
        )

    response = client.post(
        "/v1/actions/call",
        headers={
            "X-Tenant-ID": TEST_TENANT_ID,
            "Idempotency-Key": (
                "past-due-0001"
            ),
        },
    )

    assert response.status_code == 402