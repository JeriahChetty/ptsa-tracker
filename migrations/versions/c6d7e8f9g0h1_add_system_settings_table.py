"""add_system_settings_table

Revision ID: c6d7e8f9g0h1
Revises: b5c6d7e8f9g0
Create Date: 2025-11-10 13:54:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'c6d7e8f9g0h1'
down_revision = 'b5c6d7e8f9g0'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Check if table already exists
    if 'system_settings' not in inspector.get_table_names():
        op.create_table('system_settings',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('progress_report_enabled', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('progress_report_frequency', sa.String(length=32), nullable=False, server_default='weekly'),
            sa.Column('progress_report_day', sa.Integer(), nullable=True, server_default='1'),
            sa.Column('progress_report_hour', sa.Integer(), nullable=True, server_default='8'),
            sa.Column('progress_report_additional_emails', sa.Text(), nullable=True),
            sa.Column('assistance_email_enabled', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('assistance_email_immediate', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('last_progress_report_sent', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Insert default settings row
        op.execute("""
            INSERT INTO system_settings (id, progress_report_enabled, progress_report_frequency, 
                                         progress_report_day, progress_report_hour, 
                                         assistance_email_enabled, assistance_email_immediate,
                                         created_at, updated_at)
            VALUES (1, true, 'weekly', 1, 8, true, true, now(), now())
            ON CONFLICT (id) DO NOTHING
        """)


def downgrade():
    op.drop_table('system_settings')
