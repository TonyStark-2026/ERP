@echo off
rem ERP 数据库每日备份（由 Windows 任务计划调用）
cd /d "C:\Users\ruancanling\Desktop\ERP VIBE CODING"
"C:\Users\ruancanling\AppData\Local\Programs\Python\Python38\pythonw.exe" scripts\db_backup.py
