from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Header,
    Query,
)
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import UsageReport
from app.services.reporting import (
    ReportingService,
)


router = APIRouter(
    prefix="/v1/usage",
    tags=["Usage"],
)

service = ReportingService()


@router.get(
    "",
    response_model=UsageReport,
    summary="Get monthly usage, limits, and cost",
)
def get_usage(
    tenant_id: Annotated[
        str,
        Header(alias="X-Tenant-ID"),
    ],
    month: str | None = Query(
        default=None,
        description=(
            "Optional YYYY-MM month; "
            "defaults to current UTC month"
        ),
    ),
    session: Session = Depends(get_db),
) -> UsageReport:
    report = service.monthly_report(
        session,
        tenant_id=tenant_id,
        month=month,
    )

    return UsageReport.model_validate(
        report
    )