@echo off
cd /d "c:\Users\ruancanling\Desktop\ERP VIBE CODING"
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8080
pause