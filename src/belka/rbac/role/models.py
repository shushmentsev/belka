import uuid

from sqlalchemy import ForeignKey, Integer, PrimaryKeyConstraint, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym

from belka.infrastructure.database.base import Base
from belka.rbac.permission.models import Permission
from belka.rbac.user.models import User


class Role(Base):
    __tablename__ = "role"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_id = synonym("id")

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    users: Mapped[list["User"]] = relationship(
        secondary="role_xref_user",
        back_populates="roles",
    )
    permissions: Mapped[list["Permission"]] = relationship(
        secondary="permission_xref_role",
        back_populates="roles",
    )


class RoleRelationUser(Base):
    __tablename__ = "role_xref_user"
    __table_args__ = (PrimaryKeyConstraint("user_id", "role_id"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    role_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("role.id", ondelete="CASCADE"),
        nullable=False,
    )
