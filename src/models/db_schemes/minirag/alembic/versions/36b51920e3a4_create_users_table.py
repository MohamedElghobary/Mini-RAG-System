"""create users table

Revision ID: 36b51920e3a4
Revises: fee4cd54bd38
Create Date: 2025-04-22 19:43:57.588380

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '36b51920e3a4'
down_revision: Union[str, None] = 'fee4cd54bd38'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Create the 'users' table
    op.create_table(
        'users',
        sa.Column('user_id', sa.Integer, primary_key=True, autoincrement=True),  # Auto-incremented integer ID
        sa.Column('user_uuid', sa.UUID(), nullable=False),  # UUID for uniqueness
        sa.Column('username', sa.String(50), nullable=False, unique=True),
        sa.Column('email', sa.String(100), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),  # Store password hashes
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    )

    # Create the 'projects' table with a foreign key to 'users'


def downgrade():
    # Drop the tables in reverse order of creation
    op.drop_table('projects')
    op.drop_table('users')