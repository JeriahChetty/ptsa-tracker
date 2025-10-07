#!/usr/bin/env python3
"""
Test script to check if the app can be imported correctly
"""
import sys
import traceback

try:
    print("🔍 Testing imports...")
    
    # Test basic imports
    print("✅ Testing basic imports...")
    import os
    from dotenv import load_dotenv
    print("✅ Basic imports successful")
    
    # Test app import
    print("✅ Testing app import...")
    from app import create_app
    print("✅ App import successful")
    
    # Test app creation
    print("✅ Testing app creation...")
    app = create_app()
    print("✅ App creation successful")
    
    # Test WSGI attribute
    print("✅ Testing app attribute...")
    print(f"App object: {app}")
    print(f"App type: {type(app)}")
    print(f"App name: {app.name}")
    
    print("🎉 All tests passed! The app should work correctly.")
    
except Exception as e:
    print(f"❌ Error occurred: {e}")
    print("📋 Full traceback:")
    traceback.print_exc()
    sys.exit(1)
