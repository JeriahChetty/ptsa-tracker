#!/usr/bin/env python3
"""
Database migration script for PTSA Tracker
"""
import os
import sys
from alembic import command
from alembic.config import Config

def run_migrations():
    """Run database migrations"""
    try:
        # Configure Alembic
        alembic_cfg = Config("alembic.ini")
        
        print("🔄 Running database migrations...")
        command.upgrade(alembic_cfg, "head")
        print("✅ Database migrations completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_migrations()
