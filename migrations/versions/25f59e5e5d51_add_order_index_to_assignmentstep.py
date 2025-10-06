"""Add order_index to AssignmentStep

Revision ID: 25f59e5e5d51
Revises: e0aca6e43b39
Create Date: 2025-08-26 13:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '25f59e5e5d51'
down_revision = 'e0aca6e43b39'
branch_labels = None
depends_on = None


def upgrade():
    # Column already added manually - skip the operation
    # with op.batch_alter_table('assignment_steps', schema=None) as batch_op:
    #     batch_op.add_column(sa.Column('order_index', sa.Integer(), nullable=True))
    pass


def downgrade():
    # Skip the downgrade as well to stay in sync
    # with op.batch_alter_table('assignment_steps', schema=None) as batch_op:
    #     batch_op.drop_column('order_index')
    pass
