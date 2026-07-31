from app.config import get_settings
from app.constants import PlanCode
from app.db import SessionLocal
from app.models import Plan, Tenant


DEMO_TENANT_ID = (
    "11111111-1111-1111-1111-111111111111"
)


def seed() -> None:
    settings = get_settings()

    with SessionLocal.begin() as session:
        free = session.get(
            Plan,
            PlanCode.FREE.value,
        )

        if free is None:
            session.add(
                Plan(
                    code=PlanCode.FREE.value,
                    name="Free",
                    monthly_price_cents=0,
                    api_call_limit=1_000,
                    ai_token_limit=100_000,
                    stripe_price_id=None,
                )
            )

        pro = session.get(
            Plan,
            PlanCode.PRO.value,
        )

        if pro is None:
            session.add(
                Plan(
                    code=PlanCode.PRO.value,
                    name="Pro",
                    monthly_price_cents=2_900,
                    api_call_limit=10_000,
                    ai_token_limit=1_000_000,
                    stripe_price_id=(
                        settings
                        .stripe_pro_price_id
                    ),
                )
            )
        else:
            pro.stripe_price_id = (
                settings.stripe_pro_price_id
            )

        demo = session.get(
            Tenant,
            DEMO_TENANT_ID,
        )

        if demo is None:
            session.add(
                Tenant(
                    id=DEMO_TENANT_ID,
                    name="Demo Tenant",
                    email="demo@example.com",
                    plan_code=(
                        PlanCode.FREE.value
                    ),
                    subscription_status=(
                        "active"
                    ),
                )
            )


if __name__ == "__main__":
    seed()