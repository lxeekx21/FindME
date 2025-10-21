"""Local authentication migration

Revision ID: 002_local_auth
Revises: 001_init
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_local_auth'
down_revision = '001_init'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if auth0_sub column exists before trying to drop it
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # Get current table info
    columns = [col['name'] for col in inspector.get_columns('user')]
    indexes = [idx['name'] for idx in inspector.get_indexes('user')]
    
    # Drop the old auth0_sub column and index if they exist
    if 'ix_user_auth0_sub' in indexes:
        op.drop_index('ix_user_auth0_sub', table_name='user')
    elif 'ix_auth0_sub' in indexes:  # Check for the actual index name from 001_init
        op.drop_index('ix_auth0_sub', table_name='user')
    
    if 'auth0_sub' in columns:
        op.drop_column('user', 'auth0_sub')
    
    # Add new columns for local authentication
    op.add_column('user', sa.Column('password_hash', sa.String(255), nullable=False))
    op.add_column('user', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('user', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    
    # Make email unique and required
    op.alter_column('user', 'email', nullable=False)
    op.create_unique_constraint('uq_user_email', 'user', ['email'])
    
    # Add index on email (check if it doesn't already exist)
    if 'ix_user_email' not in indexes and 'ix_email' not in indexes:
        op.create_index('ix_user_email', 'user', ['email'])


def downgrade() -> None:
    # Check what exists before trying to drop
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    columns = [col['name'] for col in inspector.get_columns('user')]
    indexes = [idx['name'] for idx in inspector.get_indexes('user')]
    
    # Remove new columns if they exist
    if 'ix_user_email' in indexes:
        op.drop_index('ix_user_email', table_name='user')
    
    # Drop unique constraint if it exists
    try:
        op.drop_constraint('uq_user_email', 'user', type_='unique')
    except:
        pass  # Constraint might not exist
    
    if 'updated_at' in columns:
        op.drop_column('user', 'updated_at')
    if 'is_active' in columns:
        op.drop_column('user', 'is_active')
    if 'password_hash' in columns:
        op.drop_column('user', 'password_hash')
    
    # Restore auth0_sub column
    op.add_column('user', sa.Column('auth0_sub', sa.String(200), nullable=False))
    op.create_index('ix_auth0_sub', 'user', ['auth0_sub'])
    
    # Make email nullable again
    op.alter_column('user', 'email', nullable=True)
