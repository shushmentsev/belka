from sqlalchemy.orm import Mapped, relationship, synonym

from belka.auth import AuthUserMixin
from belka.infrastructure.database.base import Base
from belka.rbac.role.models import Role


class User(AuthUserMixin, Base):
    __tablename__ = "user"

    user_id = synonym("id")
    roles: Mapped[list["Role"]] = relationship(
        secondary="role_xref_user",
        back_populates="users",
    )
