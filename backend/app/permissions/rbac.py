"""Role-based access control dependency factory."""
from fastapi import Depends

from app.auth.dependencies import get_current_active_user
from app.core.exceptions import ForbiddenError
from app.models.user import RoleName, User


def require_roles(*allowed_roles: RoleName):
    """FastAPI dependency that restricts an endpoint to the given roles."""

    async def _check_role(user: User = Depends(get_current_active_user)) -> User:
        if user.role.name not in {role.value for role in allowed_roles}:
            raise ForbiddenError("You do not have permission to perform this action")
        return user

    return _check_role


require_super_admin = require_roles(RoleName.SUPER_ADMIN)
require_admin = require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN)
require_any_role = require_roles(RoleName.SUPER_ADMIN, RoleName.ADMIN, RoleName.EMPLOYEE)
