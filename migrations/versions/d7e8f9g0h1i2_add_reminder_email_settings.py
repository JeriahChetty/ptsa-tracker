"""add_reminder_email_settings

Revision ID: d7e8f9g0h1i2
Revises: c6d7e8f9g0h1
Create Date: 2025-11-10 14:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'd7e8f9g0h1i2'
down_revision = 'c6d7e8f9g0h1'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Check if table exists
    if 'system_settings' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('system_settings')]
        
        # Use appropriate boolean default (1 for SQLite, true for PostgreSQL)
        bool_default = '1' if conn.dialect.name == 'sqlite' else 'true'
        
        # Add reminder_email_enabled if not exists
        if 'reminder_email_enabled' not in columns:
            op.add_column('system_settings', 
                sa.Column('reminder_email_enabled', sa.Boolean(), nullable=False, server_default=bool_default))
        
        # Add reminder_days_before if not exists
        if 'reminder_days_before' not in columns:
            op.add_column('system_settings', 
                sa.Column('reminder_days_before', sa.Integer(), nullable=False, server_default='7'))
        
        # Add last_reminder_check if not exists
        if 'last_reminder_check' not in columns:
            op.add_column('system_settings', 
                sa.Column('last_reminder_check', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('system_settings', 'last_reminder_check')
    op.drop_column('system_settings', 'reminder_days_before')
    op.drop_column('system_settings', 'reminder_email_enabled')
