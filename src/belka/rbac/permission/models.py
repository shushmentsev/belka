from sqlalchemy import ForeignKey, Integer, PrimaryKeyConstraint, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from belka.infrastructure.database.base import Base
from belka.rbac.role.models import Role


class Permission(Base):
    __tablename__ = "permission"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    roles: Mapped[list["Role"]] = relationship(
        secondary="permission_relation_role",
        back_populates="permissions",
    )


class PermissionRelationRole(Base):
    __tablename__ = "permission_relation_role"
    __table_args__ = (PrimaryKeyConstraint("role_id", "permission_id"),)

    role_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("role.id", ondelete="CASCADE"),
        nullable=False,
    )
    permission_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("permission.id", ondelete="CASCADE"),
        nullable=False,
    )
