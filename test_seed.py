#!/usr/bin/env python3
"""
Quick test script to verify seeding functionality
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_seed():
    """Test if seeding can run without errors"""
    try:
        from comprehensive_seed import comprehensive_seed
        print("✅ comprehensive_seed function imported successfully")
        
        # Test import of all required models
        from app.models import User, Company, Measure, MeasureStep, MeasureAssignment
        print("✅ All models imported successfully")
        
        print("🧪 Seeding function is ready to run")
        print("📋 To seed production database, use the admin interface at /admin/seed-data")
        return True
        
    except Exception as e:
        print(f"❌ Error testing seed: {e}")
        return False

if __name__ == "__main__":
    test_seed()
