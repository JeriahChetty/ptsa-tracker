#!/usr/bin/env python3
"""
Route inspector to see available Flask routes
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app

def list_routes():
    """List all available Flask routes"""
    
    app = create_app()
    
    with app.app_context():
        print("🔍 Available Flask Routes:")
        print("=" * 60)
        
        # Get all routes
        routes = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint.startswith('admin'):
                routes.append({
                    'endpoint': rule.endpoint,
                    'methods': list(rule.methods - {'HEAD', 'OPTIONS'}),
                    'path': str(rule)
                })
        
        # Sort routes
        routes.sort(key=lambda x: x['endpoint'])
        
        # Group by category
        categories = {}
        for route in routes:
            category = route['endpoint'].split('.')[1] if '.' in route['endpoint'] else 'other'
            if category not in categories:
                categories[category] = []
            categories[category].append(route)
        
        # Print categorized routes
        for category, cat_routes in categories.items():
            print(f"\n📂 {category.upper()} ROUTES:")
            for route in cat_routes:
                methods_str = ', '.join(route['methods'])
                print(f"  ✅ {route['endpoint']:<40} {methods_str:<15} {route['path']}")
        
        # Look for benchmarking routes specifically
        print(f"\n🎯 BENCHMARKING-RELATED ROUTES:")
        benchmark_routes = [r for r in routes if 'benchmark' in r['endpoint'].lower()]
        if benchmark_routes:
            for route in benchmark_routes:
                methods_str = ', '.join(route['methods'])
                print(f"  📊 {route['endpoint']:<40} {methods_str:<15} {route['path']}")
        else:
            print("  ❌ No benchmarking routes found!")

if __name__ == '__main__':
    list_routes()