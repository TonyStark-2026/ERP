with open(r'c:\Users\ruancanling\Desktop\ERP VIBE CODING\frontend\purchase.js', 'rb') as f:
    raw = f.read(20)
    print('First 20 bytes:', raw[:20].hex())
    print('Has BOM:', raw[:3] == b'\xef\xbb\xbf')

# Check for null bytes
with open(r'c:\Users\ruancanling\Desktop\ERP VIBE CODING\frontend\purchase.js', 'rb') as f:
    content = f.read()
    null_count = content.count(b'\x00')
    print(f'Null bytes: {null_count}')
    print(f'File size: {len(content)} bytes')

# Check last 20 bytes
print('Last 20 bytes:', content[-20:])
