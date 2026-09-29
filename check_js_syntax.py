import re

with open(r'c:\Users\ruancanling\Desktop\ERP VIBE CODING\frontend\purchase.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Check for potential issues
issues = []

# 1. Check for unescaped </script> in strings/templates
for i, line in enumerate(content.split('\n'), 1):
    if '</script>' in line.lower() and '<\/script>' not in line.lower():
        issues.append(f'Line {i}: Possible unescaped </script> tag')
    if '<\/script>' in line:
        issues.append(f'Line {i}: Found <\/script> escape (OK)')

# 2. Check line lengths
for i, line in enumerate(content.split('\n'), 1):
    if len(line) > 500:
        issues.append(f'Line {i}: Very long line ({len(line)} chars)')

# 3. Check for template literals that might have issues - look for backtick count per line
for i, line in enumerate(content.split('\n'), 1):
    # Count backticks (not in comments)
    stripped = re.sub(r'//.*$', '', line)
    bt_count = stripped.count('`')
    if bt_count % 2 != 0:
        issues.append(f'Line {i}: Odd number of backticks ({bt_count}) - potential issue')

# 4. Check for common JS syntax issues
for i, line in enumerate(content.split('\n'), 1):
    # Missing closing ) 
    opens = line.count('(') - line.count(')')
    closes = line.count(')') - line.count('(')
    if opens > 1:
        issues.append(f'Line {i}: Unbalanced parentheses ({opens} more opens)')

# 5. Check the end of file
if not content.rstrip().endswith(';') and not content.rstrip().endswith('}'):
    last_line = content.strip().split('\n')[-1]
    issues.append(f'Last line may not end properly: "{last_line[:80]}"')

# 6. Check for window._renderPurchaseImpl
if 'window._renderPurchaseImpl' in content:
    issues.append('Found window._renderPurchaseImpl registration (OK)')
else:
    issues.append('MISSING: window._renderPurchaseImpl registration')

print(f'File: {len(content)} chars, {len(content.split(chr(10)))} lines')
print(f'Issues found: {len(issues)}')
for issue in issues:
    print(f'  - {issue}')
