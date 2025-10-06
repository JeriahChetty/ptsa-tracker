#!/usr/bin/env python3
"""
Fix Jinja2 template syntax errors in company_profile.html
"""

import re

def fix_template_syntax():
    """Find and fix unclosed if blocks in the template"""
    
    template_file = r"c:\Users\CENAT00068\Desktop\Projects\ptsa_tracker\app\templates\admin\company_profile.html"
    
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("🔍 Analyzing template syntax...")
        
        # Track if/endif pairs
        lines = content.split('\n')
        if_stack = []
        errors = []
        
        for i, line in enumerate(lines, 1):
            # Find {% if %} statements
            if_matches = re.findall(r'{%\s*if\s+[^%]+%}', line)
            for match in if_matches:
                if_stack.append((i, match, line.strip()))
            
            # Find {% elif %} and {% else %} statements
            elif_matches = re.findall(r'{%\s*(elif|else)\s*[^%]*%}', line)
            if elif_matches and not if_stack:
                errors.append(f"Line {i}: Found {elif_matches[0]} without matching if: {line.strip()}")
            
            # Find {% endif %} statements
            endif_matches = re.findall(r'{%\s*endif\s*%}', line)
            for match in endif_matches:
                if if_stack:
                    if_stack.pop()
                else:
                    errors.append(f"Line {i}: Found endif without matching if: {line.strip()}")
        
        # Check for unclosed if blocks
        if if_stack:
            print("❌ Found unclosed if blocks:")
            for line_num, if_stmt, line_content in if_stack:
                print(f"  Line {line_num}: {if_stmt}")
                print(f"    Content: {line_content}")
        
        if errors:
            print("❌ Found template errors:")
            for error in errors:
                print(f"  {error}")
        
        # Look for specific patterns that might be broken
        print(f"\n🔍 Looking for common patterns...")
        
        # Check for {% if benchmarks %} without {% endif %}
        if_benchmark_count = len(re.findall(r'{%\s*if\s+benchmarks\s*%}', content))
        endif_after_benchmark = content.count('{% endif %}')
        
        print(f"  {{% if benchmarks %}} count: {if_benchmark_count}")
        print(f"  {{% endif %}} count in file: {endif_after_benchmark}")
        
        # Look for the specific area around benchmarks
        benchmark_start = content.find('{% if benchmarks %}')
        if benchmark_start != -1:
            # Find the section around this
            before_context = content[max(0, benchmark_start-200):benchmark_start]
            after_context = content[benchmark_start:benchmark_start+1000]
            
            print(f"\n📋 Context around {{% if benchmarks %}}:")
            print("Before:")
            print(before_context[-100:])
            print("\nAfter (first 200 chars):")
            print(after_context[:200])
            
            # Check if there's a matching endif in the after context
            if '{% endif %}' not in after_context:
                print("\n🔧 ISSUE: No {% endif %} found after {% if benchmarks %}")
                print("Need to add {% endif %} before {% endblock %}")
                
                # Find the {% endblock %} that's causing the problem
                endblock_pos = content.find('{% endblock %}', benchmark_start)
                if endblock_pos != -1:
                    # Insert {% endif %} before {% endblock %}
                    fixed_content = content[:endblock_pos] + "{% endif %}\n" + content[endblock_pos:]
                    
                    # Write the fixed content
                    with open(template_file, 'w', encoding='utf-8') as f:
                        f.write(fixed_content)
                    
                    print("✅ Added missing {% endif %} before {% endblock %}")
                    return True
        
        if not if_stack and not errors:
            print("✅ Template syntax looks correct!")
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Error analyzing template: {e}")
        return False

if __name__ == '__main__':
    print("🔧 Fixing Jinja2 template syntax...")
    success = fix_template_syntax()
    
    if success:
        print("\n✅ Template syntax fixed!")
        print("🔄 Try accessing the company profile again")
    else:
        print("\n❌ Could not automatically fix the template")
        print("Manual inspection may be required")