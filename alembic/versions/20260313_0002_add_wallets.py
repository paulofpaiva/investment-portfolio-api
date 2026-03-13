"""add wallets support

Revision ID: 20260313_0002
Revises: 20260313_0001
Create Date: 2026-03-13 00:30:00
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "20260313_0002"
down_revision = "20260313_0001"
branch_labels = None
depends_on = None


users_table = sa.table(
    "users",
    sa.column("id", sa.Uuid()),
)

wallets_table = sa.table(
    "wallets",
    sa.column("id", sa.Uuid()),
    sa.column("user_id", sa.Uuid()),
    sa.column("name", sa.String(length=255)),
    sa.column("is_default", sa.Boolean()),
    sa.column("created_at", sa.DateTime(timezone=True)),
)

transactions_table = sa.table(
    "transactions",
    sa.column("user_id", sa.Uuid()),
    sa.column("wallet_id", sa.Uuid()),
)


def upgrade() -> None:
    op.create_table(
        "wallets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_wallets_user_id"), "wallets", ["user_id"], unique=False)
    op.add_column("transactions", sa.Column("wallet_id", sa.Uuid(), nullable=True))
    op.create_index(op.f("ix_transactions_wallet_id"), "transactions", ["wallet_id"], unique=False)
    op.create_foreign_key(
        "fk_transactions_wallet_id_wallets",
        "transactions",
        "wallets",
        ["wallet_id"],
        ["id"],
    )

    bind = op.get_bind()
    users = list(bind.execute(sa.select(users_table.c.id)).mappings())
    now = datetime.now(timezone.utc)

    for user in users:
        wallet_id = uuid4()
        bind.execute(
            wallets_table.insert().values(
                id=wallet_id,
                user_id=user["id"],
                name="Default",
                is_default=True,
                created_at=now,
            )
        )
        bind.execute(
            transactions_table.update()
            .where(transactions_table.c.user_id == user["id"])
            .values(wallet_id=wallet_id)
        )

    op.alter_column("transactions", "wallet_id", nullable=False)


def downgrade() -> None:
    op.drop_constraint("fk_transactions_wallet_id_wallets", "transactions", type_="foreignkey")
    op.drop_index(op.f("ix_transactions_wallet_id"), table_name="transactions")
    op.drop_column("transactions", "wallet_id")
    op.drop_index(op.f("ix_wallets_user_id"), table_name="wallets")
    op.drop_table("wallets")
