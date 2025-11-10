"""add soft delete to measure assignments

Revision ID: a3b4c5d6e7f8
Revises: f1a2b3c4d5e6
Create Date: 2025-11-10 06:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a3b4c5d6e7f8'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    # Add soft-delete columns to measure_assignments table
    # Make migration idempotent - only add columns if they don't exist
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('measure_assignments')]
    
    with op.batch_alter_table('measure_assignments', schema=None) as batch_op:
        if 'deleted_at' not in columns:
            batch_op.add_column(sa.Column('deleted_at', sa.DateTime(), nullable=True))
        if 'deleted_by' not in columns:
            batch_op.add_column(sa.Column('deleted_by', sa.Integer(), nullable=True))
        # Only create foreign key if deleted_by column was just added or doesn't have the constraint
        if 'deleted_by' not in columns:
            batch_op.create_foreign_key('fk_measure_assignments_deleted_by_users', 'users', ['deleted_by'], ['id'])


def downgrade():
    # Remove soft-delete columns from measure_assignments table
    with op.batch_alter_table('measure_assignments', schema=None) as batch_op:
        batch_op.drop_constraint('fk_measure_assignments_deleted_by_users', type_='foreignkey')
        batch_op.drop_column('deleted_by')
        batch_op.drop_column('deleted_at')
