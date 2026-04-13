import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, PrimaryKeyConstraint, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from belka.infrastructure.database.base import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    roles: Mapped[list["Role"]] = relationship(
        secondary="role_relation_user",
        back_populates="users",
    )


class Role(Base):
    __tablename__ = "role"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    users: Mapped[list["User"]] = relationship(
        secondary="role_relation_user",
        back_populates="roles",
    )
    permissions: Mapped[list["Permission"]] = relationship(
        secondary="permission_relation_role",
        back_populates="roles",
    )


class Permission(Base):
    __tablename__ = "permission"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    roles: Mapped[list["Role"]] = relationship(
        secondary="permission_relation_role",
        back_populates="permissions",
    )


class RoleRelationUser(Base):
    __tablename__ = "role_relation_user"

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

    __table_args__ = (PrimaryKeyConstraint("user_id", "role_id"),)


class PermissionRelationRole(Base):
    __tablename__ = "permission_relation_role"

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

    __table_args__ = (PrimaryKeyConstraint("role_id", "permission_id"),)
