#!/usr/bin/env python3
"""
Complete database reset script for PTSA Tracker.
This script will delete the existing database and create a fresh one with all new features.
"""

import os
import sys
import shutil
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def reset_database():
    """Completely reset the database."""
    print("🔥 PTSA Tracker Complete Database Reset")
    print("=" * 40)
    
    # Database file path
    db_path = os.path.join('instance', 'ptsa_tracker.db')
    
    try:
        # Remove existing database if it exists
        if os.path.exists(db_path):
            # Create backup first
            backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(db_path, backup_path)
            print(f"💾 Backup created: {backup_path}")
            
            # Remove the database
            os.remove(db_path)
            print("🗑️  Removed existing database")
        else:
            print("📄 No existing database found")
        
        # Remove any cached Python files
        cache_dirs = ['__pycache__', 'app/__pycache__', 'app/routes/__pycache__']
        for cache_dir in cache_dirs:
            if os.path.exists(cache_dir):
                shutil.rmtree(cache_dir)
                print(f"🧹 Cleared cache: {cache_dir}")
        
        print("✅ Database reset completed!")
        print("\nNext step: Run 'python init_database.py' to create fresh database")
        
        return True
        
    except Exception as e:
        print(f"❌ Reset failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = reset_database()
    sys.exit(0 if success else 1)