#!/usr/bin/env python3
"""
Quick fix for turnover formatting issue
"""

def fix_turnover_formatting():
    """Fix the turnover formatting in company profile template"""
    
    template_file = r"c:\Users\CENAT00068\Desktop\Projects\ptsa_tracker\app\templates\admin\company_profile.html"
    
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find and replace the problematic turnover formatting
        old_pattern = 'R {{ "{:,.2f}".format(benchmark.turnover) }}'
        new_pattern = '{{ benchmark.turnover }}'
        
        if old_pattern in content:
            content = content.replace(old_pattern, new_pattern)
            print("✅ Fixed turnover formatting issue")
        else:
            # Try alternative patterns
            patterns_to_fix = [
                ('{{ "{:,.2f}".format(benchmark.turnover) }}', '{{ benchmark.turnover }}'),
                ('R {{ benchmark.turnover|round(2) }}', '{{ benchmark.turnover }}'),
                ('{{ benchmark.turnover|float|round(2) }}', '{{ benchmark.turnover }}')
            ]
            
            for old, new in patterns_to_fix:
                if old in content:
                    content = content.replace(old, new)
                    print(f"✅ Fixed pattern: {old}")
                    break
            else:
                print("⚠️  Could not find exact pattern, searching for turnover formatting...")
                
                # Look for any problematic formatting lines
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'turnover' in line and ('format' in line or '|round' in line or '|float' in line):
                        print(f"Found problematic line {i+1}: {line.strip()}")
                        # Replace with simple display
                        lines[i] = line.replace('{{ "{:,.2f}".format(benchmark.turnover) }}', '{{ benchmark.turnover }}')
                        lines[i] = lines[i].replace('{{ benchmark.turnover|round(2) }}', '{{ benchmark.turnover }}')
                        lines[i] = lines[i].replace('{{ benchmark.turnover|float|round(2) }}', '{{ benchmark.turnover }}')
                        print(f"Fixed to: {lines[i].strip()}")
                
                content = '\n'.join(lines)
        
        # Write back the fixed content
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Template file updated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing template: {e}")
        return False

if __name__ == '__main__':
    print("🔧 Fixing turnover formatting issue...")
    fix_turnover_formatting()