#!/usr/bin/env python3
"""
Test script to verify entrypoint functionality locally
"""
import os
import subprocess
import sys

def test_entrypoint():
    """Test if entrypoint script can run successfully"""
    print("🧪 Testing entrypoint script...")
    
    # Check if entrypoint.sh exists
    if not os.path.exists("entrypoint.sh"):
        print("❌ entrypoint.sh not found")
        return False
    
    # Check if it's executable
    if not os.access("entrypoint.sh", os.X_OK):
        print("❌ entrypoint.sh is not executable")
        return False
    
    print("✅ entrypoint.sh exists and is executable")
    
    # Test WSGI import
    try:
        import wsgi
        print("✅ WSGI module can be imported")
        print(f"✅ App object: {wsgi.app}")
        return True
    except Exception as e:
        print(f"❌ WSGI import failed: {e}")
        return False

if __name__ == "__main__":
    success = test_entrypoint()
    sys.exit(0 if success else 1)
