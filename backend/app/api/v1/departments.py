"""Department management endpoints."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.permissions.rbac import require_admin, require_any_role
from app.repositories.organization_repository import DepartmentRepository
from app.schemas.organization import DepartmentCreate, DepartmentPublic
from app.services.employee_service import EmployeeService

router = APIRouter()


@router.get("", response_model=list[DepartmentPublic], dependencies=[Depends(require_any_role)])
async def list_departments(db: AsyncSession = Depends(get_db)) -> list[DepartmentPublic]:
    departments = await DepartmentRepository(db).list_all()
    return [DepartmentPublic.model_validate(d) for d in departments]


@router.post(
    "",
    response_model=DepartmentPublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_department(
    payload: DepartmentCreate, db: AsyncSession = Depends(get_db)
) -> DepartmentPublic:
    department = await EmployeeService(db).create_department(
        name=payload.name, code=payload.code, branch_id=payload.branch_id
    )
    return DepartmentPublic.model_validate(department)
