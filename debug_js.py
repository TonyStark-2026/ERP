import re

with open(r'c:\Users\ruancanling\Desktop\ERP VIBE CODING\frontend\purchase.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Search for patterns that cause "Invalid left-hand side in assignment"
for i, line in enumerate(lines, 1):
    # Pattern: something = value where something might be invalid
    # Look for template literal expressions used as assignment targets
    matches = re.finditer(r'\$\{[^}]+\}\s*=', line)
    for m in matches:
        print(f'Line {i}: Template literal as assignment target: {line.rstrip()[:120]}')
    
    # Look for optional chaining assignment
    if '?.' in line and '=' in line:
        print(f'Line {i}: Optional chaining with assignment: {line.rstrip()[:120]}')

# Test syntax by trying to parse with execjs-like logic
# Split into function definitions and test each
print('\n--- Testing individual functions ---')
full_code = ''.join(lines)
# Find all function definitions
funcs = re.finditer(r'(?:function\s+(\w+)|(?:var|let|const)\s+(\w+)\s*=\s*(?:function|\()))\s*\{', full_code)

# Simpler: try to find the issue by testing code sections
# Let's just check for common problematic patterns
for i, line in enumerate(lines, 1):
    stripped = line.strip()
    # Check for backtick issues
    bt_count = stripped.count('`')
    if bt_count > 0 and bt_count % 2 != 0:
        print(f'Line {i}: Unpaired backtick ({bt_count}): {stripped[:100]}')
    
    # Check for potential assignment issues
    # e.g., ${...} = ... or computed property as assignment target
    if re.search(r'\$\{[^}]+\}\s*=[^=]', stripped):
        print(f'Line {i}: POTENTIAL BUG - assignment inside template: {stripped[:120]}')

# Show lines around the problematic area (line 520 area)
print('\n--- Lines 518-530 ---')
for i in range(517, min(530, len(lines))):
    print(f'  {i+1}: {lines[i].rstrip()[:120]}')
