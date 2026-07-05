"""Business logic for employee, department, and branch management."""
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password
from app.models.employee import Branch, Department, Employee
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.organization_repository import BranchRepository, DepartmentRepository
from app.repositories.user_repository import UserRepository


class EmployeeService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.employees = EmployeeRepository(session)
        self.departments = DepartmentRepository(session)
        self.branches = BranchRepository(session)
        self.users = UserRepository(session)
        self.audit_logs = AuditLogRepository(session)

    async def create_employee(
        self,
        *,
        email: str,
        password: str,
        employee_code: str,
        first_name: str,
        last_name: str,
        role_name: str,
        phone: str | None = None,
        job_title: str | None = None,
        department_id: uuid.UUID | None = None,
        manager_id: uuid.UUID | None = None,
        actor_id: uuid.UUID,
        ip_address: str | None,
        user_agent: str | None,
    ) -> Employee:
        email = email.lower().strip()
        if await self.users.get_by_email(email) is not None:
            raise ConflictError("An account with this email already exists")
        if await self.employees.get_by_employee_code(employee_code) is not None:
            raise ConflictError("Employee code already in use")

        role = await self.users.get_role_by_name(role_name)
        if role is None:
            raise NotFoundError(f"Role '{role_name}' is not configured")

        department = None
        if department_id is not None:
            department = await self.departments.get_by_id(department_id)
            if department is None:
                raise NotFoundError("Department not found")

        manager = None
        if manager_id is not None:
            manager = await self.employees.get_by_id(manager_id)
            if manager is None:
                raise NotFoundError("Manager not found")

        user = User(email=email, hashed_password=hash_password(password), role_id=role.id)
        user.role = role
        await self.users.create(user)

        employee = Employee(
            user_id=user.id,
            employee_code=employee_code,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            job_title=job_title,
            department_id=department_id,
            manager_id=manager_id,
        )
        # Populate in memory so the serializer doesn't trigger an async lazy-load.
        employee.user = user
        employee.department = department
        employee.manager = manager
        await self.employees.create(employee)

        await self.audit_logs.create(
            action="create",
            entity_type="employee",
            entity_id=str(employee.id),
            user_id=actor_id,
            new_values={"employee_code": employee_code, "email": email, "role": role_name},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.session.commit()
        return employee

    async def get_employee_or_404(self, employee_id: uuid.UUID) -> Employee:
        employee = await self.employees.get_by_id(employee_id)
        if employee is None:
            raise NotFoundError("Employee not found")
        return employee

    async def list_employees(
        self,
        page: int,
        page_size: int,
        department_id: uuid.UUID | None = None,
        search: str | None = None,
    ) -> tuple[list[Employee], int]:
        return await self.employees.list_paginated(page, page_size, department_id, search)

    async def update_employee(
        self,
        employee_id: uuid.UUID,
        updates: dict,
        actor_id: uuid.UUID,
        ip_address: str | None,
        user_agent: str | None,
    ) -> Employee:
        employee = await self.get_employee_or_404(employee_id)
        old_values = {
            k: getattr(employee, k) for k in updates if hasattr(employee, k)
        }

        new_department = None
        if "department_id" in updates and updates["department_id"] is not None:
            new_department = await self.departments.get_by_id(updates["department_id"])
            if new_department is None:
                raise NotFoundError("Department not found")

        new_manager = None
        if "manager_id" in updates and updates["manager_id"] is not None:
            if updates["manager_id"] == employee_id:
                raise ConflictError("An employee cannot be their own manager")
            new_manager = await self.employees.get_by_id(updates["manager_id"])
            if new_manager is None:
                raise NotFoundError("Manager not found")

        for key, value in updates.items():
            if value is not None:
                setattr(employee, key, value.value if hasattr(value, "value") else value)

        # Keep the in-memory relationship objects in sync with the FK columns we
        # just set directly, since SQLAlchemy doesn't refresh them automatically —
        # without this, department_name/manager_name would still read the stale value.
        if new_department is not None:
            employee.department = new_department
        if new_manager is not None:
            employee.manager = new_manager

        await self.audit_logs.create(
            action="update",
            entity_type="employee",
            entity_id=str(employee.id),
            user_id=actor_id,
            old_values={k: str(v) for k, v in old_values.items()},
            new_values={k: str(v) for k, v in updates.items()},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.session.commit()
        return employee

    async def deactivate_employee(
        self,
        employee_id: uuid.UUID,
        actor_id: uuid.UUID,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        employee = await self.get_employee_or_404(employee_id)
        await self.employees.soft_delete(employee)
        user = await self.users.get_by_id(employee.user_id)
        if user is not None:
            user.is_active = False
        await self.audit_logs.create(
            action="delete",
            entity_type="employee",
            entity_id=str(employee.id),
            user_id=actor_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.session.commit()

    async def create_branch(
        self, name: str, code: str, address: str | None, timezone: str
    ) -> Branch:
        if await self.branches.get_by_code(code) is not None:
            raise ConflictError("Branch code already in use")
        branch = Branch(name=name, code=code, address=address, timezone=timezone)
        await self.branches.create(branch)
        await self.session.commit()
        return branch

    async def create_department(self, name: str, code: str, branch_id: uuid.UUID) -> Department:
        if await self.branches.get_by_id(branch_id) is None:
            raise NotFoundError("Branch not found")
        if await self.departments.get_by_code(code) is not None:
            raise ConflictError("Department code already in use")
        department = Department(name=name, code=code, branch_id=branch_id)
        await self.departments.create(department)
        await self.session.commit()
        return department
