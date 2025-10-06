#!/usr/bin/env python3
"""
Remove duplicate model and use existing one
"""

import sys
import os

def fix_models_file():
    """Remove duplicate Benchmarking model and use existing structure"""
    
    models_file = r"c:\Users\CENAT00068\Desktop\Projects\ptsa_tracker\app\models.py"
    
    try:
        # Read the current file
        with open(models_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the duplicate Benchmarking class I added
        start_marker = "class Benchmarking(db.Model):"
        
        if start_marker in content:
            print("🔍 Found duplicate Benchmarking model, removing...")
            
            # Find the start and end of the duplicate class
            start_pos = content.find(start_marker)
            
            # Find the end (next class or end of file)
            remaining = content[start_pos:]
            lines = remaining.split('\n')
            
            # Find where this class ends (next class definition or end)
            end_line = 0
            in_class = True
            for i, line in enumerate(lines[1:], 1):  # Skip the class definition line
                # If we hit a non-indented line that's not empty and not a comment, we've left the class
                if line.strip() and not line.startswith(' ') and not line.startswith('\t') and not line.startswith('#'):
                    end_line = i
                    break
            
            if end_line == 0:
                # Class goes to end of file
                new_content = content[:start_pos].rstrip()
            else:
                end_pos = start_pos + len('\n'.join(lines[:end_line]))
                new_content = content[:start_pos] + content[end_pos:]
            
            # Write back the cleaned file
            with open(models_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("✅ Removed duplicate Benchmarking model")
            return True
        else:
            print("ℹ️  No duplicate Benchmarking model found")
            return True
            
    except Exception as e:
        print(f"❌ Error fixing models file: {e}")
        return False

if __name__ == '__main__':
    print("🔧 Fixing models.py file...")
    success = fix_models_file()
    
    if success:
        print("✅ Models file cleaned successfully!")
        print("🔍 Now run: python check_existing_models.py")
    else:
        print("❌ Failed to clean models file")
        sys.exit(1)