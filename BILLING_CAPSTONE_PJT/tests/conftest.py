import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import (
    Session,
    sessionmaker,
)
from sqlalchemy.pool import StaticPool

from app.constants import PlanCode
from app.db import Base, get_db
from app.main import app
from app.models import Plan, Tenant


TEST_TENANT_ID = (
    "22222222-2222-2222-2222-222222222222"
)


@pytest.fixture()
def engine():
    test_engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    Base.metadata.create_all(test_engine)

    yield test_engine

    Base.metadata.drop_all(test_engine)
    test_engine.dispose()


@pytest.fixture()
def session_factory(engine):
    factory = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
        class_=Session,
    )

    with factory.begin() as session:
        session.add_all(
            [
                Plan(
                    code=PlanCode.FREE.value,
                    name="Free",
                    monthly_price_cents=0,
                    api_call_limit=2,
                    ai_token_limit=100,
                ),
                Plan(
                    code=PlanCode.PRO.value,
                    name="Pro",
                    monthly_price_cents=2900,
                    api_call_limit=10,
                    ai_token_limit=1000,
                    stripe_price_id=(
                        "price_test_pro"
                    ),
                ),
                Tenant(
                    id=TEST_TENANT_ID,
                    name="Test Tenant",
                    email="test@example.com",
                    plan_code=(
                        PlanCode.FREE.value
                    ),
                    subscription_status=(
                        "active"
                    ),
                ),
            ]
        )

    return factory


@pytest.fixture()
def client(session_factory):
    def override_get_db():
        with session_factory() as session:
            yield session

    app.dependency_overrides[
        get_db
    ] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()