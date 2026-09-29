import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

try:
    print("Initializing database...")
    from backend.database import engine, Base
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")
    
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend.db')
    if os.path.exists(db_path):
        print(f"Database file created: {db_path}")
    else:
        print(f"Database file NOT found at: {db_path}")
        
except Exception as e:
    import traceback
    traceback.print_exc()
    input("Press Enter to exit")