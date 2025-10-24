"""init schema and seed roles

Revision ID: 001_init
Revises: 
Create Date: 2025-09-27

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_init'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    # ⬇️ Key change: prevent auto-creation during table DDL
    gender_enum = postgresql.ENUM(
        'male', 'female',
        name='gender_enum',
        create_type=False  # <-- don't auto-create inside op.create_table
    )
    # Create it once, idempotently
    gender_enum.create(bind=bind, checkfirst=True)

    op.create_table(
        'role',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_role')),
        sa.UniqueConstraint('name', name='uq_roles_name')
    )

    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('auth0_sub', sa.String(length=200), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=255), nullable=False),
        sa.Column('last_name', sa.String(length=255), nullable=False),
        sa.Column('gender', gender_enum, nullable=True),  # <-- reuse the same object
        sa.Column('dob', sa.Date(), nullable=True),
        sa.Column('phone', sa.String(length=15), nullable=True),
        sa.Column('profile_image_url', sa.String(length=256), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_user'))
    )
    op.create_index(op.f('ix_auth0_sub'), 'user', ['auth0_sub'], unique=True)
    op.create_index(op.f('ix_email'), 'user', ['email'], unique=False)

    op.create_table(
        'user_roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['role.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_user_roles')),
        sa.UniqueConstraint('user_id', name='uq_user_roles_user')
    )

    op.create_table(
        'submission',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_submission'))
    )

    op.execute("""
               INSERT INTO role (id, name) VALUES
                                               (1, 'admin'),
                                               (2, 'user')
                   ON CONFLICT (id) DO NOTHING
               """)

def downgrade() -> None:
    op.drop_table('submission')
    op.drop_table('user_roles')
    op.drop_index(op.f('ix_email'), table_name='user')
    op.drop_index(op.f('ix_auth0_sub'), table_name='user')
    op.drop_table('user')
    op.drop_table('role')

    bind = op.get_bind()
    postgresql.ENUM(name='gender_enum').drop(bind=bind, checkfirst=True)