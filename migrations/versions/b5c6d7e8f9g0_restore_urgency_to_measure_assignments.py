"""restore urgency to measure assignments

Revision ID: b5c6d7e8f9g0
Revises: a3b4c5d6e7f8
Create Date: 2025-11-10 09:58:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b5c6d7e8f9g0'
down_revision = 'a3b4c5d6e7f8'
branch_labels = None
depends_on = None


def upgrade():
    # Add urgency column back to measure_assignments table
    # Make migration idempotent - only add column if it doesn't exist
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('measure_assignments')]
    
    if 'urgency' not in columns:
        with op.batch_alter_table('measure_assignments', schema=None) as batch_op:
            batch_op.add_column(sa.Column('urgency', sa.Integer(), nullable=True, server_default='1'))
        
        # Set default value for existing records
        op.execute("UPDATE measure_assignments SET urgency = 1 WHERE urgency IS NULL")


def downgrade():
    # Remove urgency column from measure_assignments table
    with op.batch_alter_table('measure_assignments', schema=None) as batch_op:
        batch_op.drop_column('urgency')
