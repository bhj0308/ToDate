"""phone-first sign-up: optional email, phone invites

Sign-up now starts with a phone number (design/screens/01, 05, 06), so an
account can exist before it has an email. Invites can target a phone too.

Batch mode so the same migration runs on SQLite (local) and Postgres.

Revision ID: 88ba35795967
Revises: d1c9c3ba7600
Create Date: 2026-09-30 20:13:37.463956
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '88ba35795967'
down_revision: Union[str, None] = 'd1c9c3ba7600'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("beta_invites") as batch:
        batch.add_column(sa.Column("phone", sa.String(length=32), nullable=True))
        batch.alter_column("email", existing_type=sa.String(length=320), nullable=True)
        batch.create_unique_constraint("uq_beta_invites_phone", ["phone"])
    with op.batch_alter_table("users") as batch:
        batch.alter_column("email", existing_type=sa.String(length=320), nullable=True)


def downgrade() -> None:
    # Reinstating NOT NULL fails on rows created after the upgrade, so make them
    # fit first: phone-only users get an undeliverable placeholder email (the
    # same pattern as account deletion), and phone-only invites are dropped.
    op.execute(
        "UPDATE users SET email = 'no-email+' || id || '@placeholder.invalid' "
        "WHERE email IS NULL"
    )
    op.execute("DELETE FROM beta_invites WHERE email IS NULL")
    with op.batch_alter_table("users") as batch:
        batch.alter_column("email", existing_type=sa.String(length=320), nullable=False)
    with op.batch_alter_table("beta_invites") as batch:
        batch.drop_constraint("uq_beta_invites_phone", type_="unique")
        batch.alter_column("email", existing_type=sa.String(length=320), nullable=False)
        batch.drop_column("phone")
