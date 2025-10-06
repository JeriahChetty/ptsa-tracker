#!/usr/bin/env python3
"""
Check existing models in the PTSA Tracker application
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.models import *
    import inspect
    
    print("🔍 Checking existing models in app.models...")
    print("=" * 50)
    
    # Get all classes from models module
    import app.models as models_module
    
    model_classes = []
    for name, obj in inspect.getmembers(models_module):
        if inspect.isclass(obj) and hasattr(obj, '__tablename__'):
            model_classes.append(name)
    
    print(f"📊 Found {len(model_classes)} model classes:")
    for model in sorted(model_classes):
        print(f"  ✅ {model}")
    
    # Check if Benchmarking exists
    if 'Benchmarking' in model_classes:
        print(f"\n✅ Benchmarking model exists!")
    else:
        print(f"\n❌ Benchmarking model NOT found!")
        print("   Need to add Benchmarking model to models.py")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")