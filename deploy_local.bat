@echo off
echo Starting PTSA Tracker Local Deployment...

cd /d "c:\Users\CENAT00068\Desktop\Projects\ptsa_tracker"

echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing dependencies...
pip install -r requirements.txt

echo Creating instance directory...
if not exist "instance" mkdir instance

echo Running database deployment...
python deploy_db.py

echo Starting Flask application...
echo.
echo ======================================
echo PTSA Tracker is starting...
echo Open your browser to: http://localhost:5000
echo.
echo Login Credentials:
echo Admin: admin@ptsa.co.za / admin123
echo Company: company@sample.co.za / company123
echo ======================================
echo.

set FLASK_APP=app.py
set FLASK_ENV=development
python app.py

pause
