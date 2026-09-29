import sys
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

try:
    print("Step 1: Importing modules...")
    from uvicorn.main import main
    print("Step 2: Import successful")
    sys.argv = ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "info"]
    print("Step 3: Running uvicorn...")
    main()
except Exception as e:
    import traceback
    traceback.print_exc()
    input("Press Enter to exit")
