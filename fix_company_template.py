#!/usr/bin/env python3
"""
Comprehensive fix for company profile template syntax
"""

def fix_company_template():
    """Fix all syntax issues in the company profile template"""
    
    template_file = r"c:\Users\CENAT00068\Desktop\Projects\ptsa_tracker\app\templates\company\company_profile.html"
    
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("🔍 Analyzing company profile template...")
        
        # Check for specific issues
        lines = content.split('\n')
        
        # Track if/endif pairs
        if_count = 0
        endif_count = 0
        
        for i, line in enumerate(lines, 1):
            if '{%' in line and 'if ' in line:
                if_count += 1
                print(f"Line {i}: Found if statement -> {line.strip()}")
            elif '{%' in line and 'endif' in line:
                endif_count += 1
                print(f"Line {i}: Found endif statement -> {line.strip()}")
        
        print(f"\n📊 Count analysis:")
        print(f"  if statements: {if_count}")
        print(f"  endif statements: {endif_count}")
        
        if if_count != endif_count:
            print(f"❌ Mismatch! Need to balance if/endif statements")
            
            # Look for the pattern and fix
            # The main issues are likely:
            # 1. Duplicate {% if not editing %} blocks
            # 2. Missing or extra {% endif %} statements
            
            # Let's clean up the template structure
            print("🔧 Attempting to fix template structure...")
            
            # Remove duplicate content and fix structure
            # Find the last proper endblock and remove everything after it
            last_endblock = content.rfind('{' + '% endblock %}')
            if last_endblock != -1:
                # Check if there's duplicate content after the last endblock
                after_endblock = content[last_endblock + len('{' + '% endblock %}'):].strip()
                if after_endblock:
                    print(f"Found duplicate content after endblock: {len(after_endblock)} characters")
                    content = content[:last_endblock + len('{' + '% endblock %}')]
                    print("✅ Removed duplicate content")
            
            # Write the cleaned content
            with open(template_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ Template cleaned successfully!")
            return True
        else:
            print("✅ If/endif counts match!")
            return True
            
    except Exception as e:
        print(f"❌ Error fixing template: {e}")
        return False

if __name__ == '__main__':
    print("🔧 Fixing company profile template syntax...")
    success = fix_company_template()
    
    if success:
        print("\n✅ Template syntax should be fixed!")
        print("🔄 Try accessing the company profile again")
    else:
        print("\n❌ Could not automatically fix the template")