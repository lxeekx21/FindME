"""
Add comments table with moderation fields

Revision ID: 004_comments
Revises: 003_submission_schema_update
Create Date: 2025-10-16
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PGEnum

# revision identifiers, used by Alembic.
revision = '004_comments'
down_revision = '003_submission_schema_update'
branch_labels = None
depends_on = None


def _table_exists(bind, table: str) -> bool:
    insp = sa.inspect(bind)
    return table in insp.get_table_names()


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == 'postgresql':
        op.execute(
            """
            DO $$ BEGIN
              CREATE TYPE comment_status_enum AS ENUM ('pending','approved','rejected');
            EXCEPTION WHEN duplicate_object THEN NULL; END $$;
            """
        )

    if not _table_exists(bind, 'comment'):
        status_col = (
            sa.Column('status', PGEnum('pending','approved','rejected', name='comment_status_enum', create_type=False), nullable=False, server_default='pending')
            if dialect == 'postgresql' else
            sa.Column('status', sa.Enum('pending','approved','rejected', name='comment_status_enum'), nullable=False, server_default='pending')
        )
        op.create_table(
            'comment',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('submission_id', sa.Integer(), sa.ForeignKey('submission.id', ondelete='CASCADE'), nullable=False),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id', ondelete='SET NULL'), nullable=True),
            sa.Column('body', sa.Text(), nullable=False),
            sa.Column('image_url', sa.String(length=1024), nullable=True),
            status_col,
            sa.Column('rejection_reason', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        )
        op.create_index('ix_comment_submission_id', 'comment', ['submission_id'])
        op.create_index('ix_comment_user_id', 'comment', ['user_id'])
        op.create_index('ix_comment_status', 'comment', ['status'])


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if _table_exists(bind, 'comment'):
        op.drop_index('ix_comment_status', table_name='comment')
        op.drop_index('ix_comment_user_id', table_name='comment')
        op.drop_index('ix_comment_submission_id', table_name='comment')
        op.drop_table('comment')

    if dialect == 'postgresql':
        op.execute(
            """
            DO $$ BEGIN
              DROP TYPE IF EXISTS comment_status_enum;
            EXCEPTION WHEN others THEN NULL; END $$;
            """
        )
