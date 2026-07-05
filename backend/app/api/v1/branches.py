"""Branch management endpoints."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.permissions.rbac import require_admin, require_any_role
from app.repositories.organization_repository import BranchRepository
from app.schemas.organization import BranchCreate, BranchPublic
from app.services.employee_service import EmployeeService

router = APIRouter()


@router.get("", response_model=list[BranchPublic], dependencies=[Depends(require_any_role)])
async def list_branches(db: AsyncSession = Depends(get_db)) -> list[BranchPublic]:
    branches = await BranchRepository(db).list_all()
    return [BranchPublic.model_validate(b) for b in branches]


@router.post(
    "",
    response_model=BranchPublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_branch(
    payload: BranchCreate, db: AsyncSession = Depends(get_db)
) -> BranchPublic:
    branch = await EmployeeService(db).create_branch(
        name=payload.name, code=payload.code, address=payload.address, timezone=payload.timezone
    )
    return BranchPublic.model_validate(branch)
