import sys
sys.path.insert(0, 'c:/Users/ruancanling/Desktop/ERP VIBE CODING/backend')
from database import SessionLocal
from models import PurchaseSuggestion

db = SessionLocal()
try:
    count = db.query(PurchaseSuggestion).count()
    print(f'Total suggestions: {count}')
    
    items = db.query(PurchaseSuggestion).order_by(PurchaseSuggestion.suggestion_no).all()
    for item in items:
        print(f'  {item.suggestion_no} | {item.material_name or item.material_spec} | {item.status}')
    
    # Test the query
    from sqlalchemy import and_
    prefix = 'SUG-20260826-'
    test = db.query(PurchaseSuggestion.suggestion_no).filter(
        PurchaseSuggestion.suggestion_no >= prefix,
        PurchaseSuggestion.suggestion_no < prefix + 'Z'
    ).order_by(PurchaseSuggestion.suggestion_no.desc()).all()
    print(f'\nQuery results: {len(test)}')
    for t in test:
        print(f'  {t[0]}')
        
finally:
    db.close()
