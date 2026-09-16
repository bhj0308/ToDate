"""release readiness: date_of_birth, user_blocks, push_tokens

Store-release requirements: a self-reported birth date for the 18+ gate,
member-to-member blocking (App Store UGC rules), and Expo push tokens.

Revision ID: d1c9c3ba7600
Revises: ec68fcccadaa
Create Date: 2026-09-16 14:45:10.748458
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import app.common.base


revision: str = 'd1c9c3ba7600'
down_revision: Union[str, None] = 'ec68fcccadaa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('push_tokens',
    sa.Column('user_id', app.common.base.GUID(), nullable=False),
    sa.Column('token', sa.String(length=255), nullable=False),
    sa.Column('platform', sa.String(length=16), nullable=True),
    sa.Column('id', app.common.base.GUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('token')
    )
    op.create_table('user_blocks',
    sa.Column('blocker_id', app.common.base.GUID(), nullable=False),
    sa.Column('blocked_id', app.common.base.GUID(), nullable=False),
    sa.Column('id', app.common.base.GUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['blocked_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['blocker_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('blocker_id', 'blocked_id')
    )
    op.add_column('users', sa.Column('date_of_birth', sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'date_of_birth')
    op.drop_table('user_blocks')
    op.drop_table('push_tokens')
