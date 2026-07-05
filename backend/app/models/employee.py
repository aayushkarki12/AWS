"""Organizational structure: branches, departments, and employees."""
import uuid
from datetime import date
from enum import StrEnum

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class EmploymentStatus(StrEnum):
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"


class Branch(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "branches"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)

    departments: Mapped[list["Department"]] = relationship(back_populates="branch")


class Department(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "departments"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)

    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False
    )
    branch: Mapped["Branch"] = relationship(back_populates="departments", lazy="selectin")

    employees: Mapped[list["Employee"]] = relationship(back_populates="department")


class Employee(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "employees"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )
    user: Mapped["User"] = relationship(back_populates="employee", lazy="selectin")  # noqa: F821

    employee_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    job_title: Mapped[str | None] = mapped_column(String(150), nullable=True)
    profile_picture_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    date_of_joining: Mapped[date | None] = mapped_column(Date, nullable=True)
    employment_status: Mapped[str] = mapped_column(
        String(20), default=EmploymentStatus.ACTIVE, nullable=False
    )

    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True
    )
    department: Mapped["Department | None"] = relationship(
        back_populates="employees", lazy="selectin"
    )

    manager_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True
    )
    manager: Mapped["Employee | None"] = relationship(
        remote_side="Employee.id", lazy="selectin"
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def email(self) -> str:
        return self.user.email

    @property
    def is_active(self) -> bool:
        return self.user.is_active

    @property
    def role_name(self) -> str:
        return self.user.role.name

    @property
    def department_name(self) -> str | None:
        return self.department.name if self.department else None

    @property
    def branch_name(self) -> str | None:
        return self.department.branch.name if self.department else None

    @property
    def manager_name(self) -> str | None:
        return self.manager.full_name if self.manager else None
