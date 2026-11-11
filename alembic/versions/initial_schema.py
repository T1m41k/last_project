"""Початкова схема: користувачі, книги, стани діалогів, оброблені події.

Revision ID: 0001_initial
Revises:
Create Date: 2026-11-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _now_column(name: str) -> sa.Column[sa.DateTime]:
    """Створити колонку часу із значенням за замовчуванням now()."""
    return sa.Column(name, sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)


def upgrade() -> None:
    """Створити таблиці."""
    op.create_table(
        "bot_users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("platform_user_id", sa.BigInteger(), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=True),
        _now_column("created_at"),
        sa.PrimaryKeyConstraint("id", name="pk_bot_users"),
        sa.UniqueConstraint("platform_user_id", name="uq_bot_users_platform_user_id"),
    )
    op.create_table(
        "books",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("author", sa.String(length=120), nullable=False),
        sa.Column("pages", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("note", sa.String(length=1000), nullable=True),
        _now_column("created_at"),
        _now_column("updated_at"),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["bot_users.id"], name="fk_books_owner_id_bot_users", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_books"),
    )
    op.create_index("ix_books_owner_id_id", "books", ["owner_id", "id"])
    op.create_table(
        "dialog_states",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("flow", sa.String(length=50), nullable=False),
        sa.Column("step", sa.String(length=50), nullable=False),
        sa.Column("data", postgresql.JSONB(), nullable=False),
        _now_column("updated_at"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["bot_users.id"],
            name="fk_dialog_states_user_id_bot_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_dialog_states"),
        sa.UniqueConstraint("user_id", name="uq_dialog_states_user_id"),
    )
    op.create_table(
        "processed_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("platform", sa.String(length=20), nullable=False),
        sa.Column("platform_event_id", sa.BigInteger(), nullable=False),
        _now_column("created_at"),
        sa.PrimaryKeyConstraint("id", name="pk_processed_events"),
        sa.UniqueConstraint(
            "platform", "platform_event_id", name="uq_processed_events_platform_event"
        ),
    )


def downgrade() -> None:
    """Видалити таблиці."""
    op.drop_table("processed_events")
    op.drop_table("dialog_states")
    op.drop_index("ix_books_owner_id_id", table_name="books")
    op.drop_table("books")
    op.drop_table("bot_users")
