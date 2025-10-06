@echo off
REM filepath: c:\Users\CENAT00068\Desktop\Projects\ptsa_tracker\run_notifications.bat
cd C:\Users\CENAT00068\Desktop\Projects\ptsa_tracker
call venv\Scripts\activate.bat
python schedule_notifications.py
echo Notification job completed at %date% %time%