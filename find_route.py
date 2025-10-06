#!/usr/bin/env python3
"""
Find and fix the company profile route to pass benchmarks data
"""

import sys
import os
import re

def find_and_fix_route():
    """Find the company profile route and ensure it passes benchmarks"""
    
    print("🔍 Finding Company Profile Route")
    print("=" * 40)
    
    # Look for the route file
    possible_routes = [
        r"c:\Users\CENAT00068\Desktop\Projects\ptsa_tracker\app\routes\admin_routes.py",
        r"c:\Users\CENAT00068\Desktop\Projects\ptsa_tracker\app\admin_routes.py",
        r"c:\Users\CENAT00068\Desktop\Projects\ptsa_tracker\app\routes.py"
    ]
    
    route_file = None
    for file_path in possible_routes:
        if os.path.exists(file_path):
            route_file = file_path
            break
    
    if not route_file:
        print("❌ Could not find routes file!")
        return False
    
    print(f"📂 Found routes file: {route_file}")
    
    try:
        with open(route_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for company_profile route
        lines = content.split('\n')
        route_start = None
        
        for i, line in enumerate(lines):
            if 'def company_profile' in line:
                route_start = i
                break
        
        if route_start is None:
            print("❌ Could not find company_profile function!")
            return False
        
        print(f"✅ Found company_profile function at line {route_start + 1}")
        
        # Find the render_template call
        render_line = None
        for i in range(route_start, min(route_start + 50, len(lines))):
            if 'render_template' in lines[i] and 'company_profile.html' in lines[i]:
                render_line = i
                break
        
        if render_line is None:
            print("❌ Could not find render_template call!")
            return False
        
        print(f"📋 Found render_template call at line {render_line + 1}")
        print(f"Current line: {lines[render_line].strip()}")
        
        # Check if benchmarks is already passed
        render_content = lines[render_line]
        if 'benchmarks=' in render_content:
            print("✅ benchmarks parameter already exists!")
        else:
            print("❌ benchmarks parameter missing!")
            
            # Show the current template call
            print(f"\n🔧 Current template call:")
            print(f"   {render_content.strip()}")
            
            # Suggest the fix
            print(f"\n💡 Need to add CompanyBenchmark query and pass to template")
            print(f"   Add before render_template:")
            print(f"   benchmarks = CompanyBenchmark.query.filter_by(company_id=company.id).order_by(CompanyBenchmark.data_year).all()")
            print(f"   ")
            print(f"   And add to render_template call:")
            print(f"   benchmarks=benchmarks")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading route file: {e}")
        return False

if __name__ == '__main__':
    find_and_fix_route()