"""Holiday calendar endpoints."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.holiday import Holiday
from app.permissions.rbac import require_admin, require_any_role
from app.repositories.holiday_repository import HolidayRepository
from app.schemas.holiday import HolidayCreate, HolidayPublic

router = APIRouter()


@router.get("", response_model=list[HolidayPublic], dependencies=[Depends(require_any_role)])
async def list_holidays(db: AsyncSession = Depends(get_db)) -> list[HolidayPublic]:
    holidays = await HolidayRepository(db).list_all()
    return [HolidayPublic.model_validate(h) for h in holidays]


@router.post(
    "",
    response_model=HolidayPublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_holiday(
    payload: HolidayCreate, db: AsyncSession = Depends(get_db)
) -> HolidayPublic:
    holiday = Holiday(
        name=payload.name,
        holiday_date=payload.holiday_date,
        is_optional=payload.is_optional,
        branch_id=payload.branch_id,
    )
    holiday = await HolidayRepository(db).create(holiday)
    await db.commit()
    return HolidayPublic.model_validate(holiday)
