@echo off
REM One-click setup and run for Windows. Double-click or run from VS Code terminal.
cd /d "%~dp0"
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
echo.
echo Open http://127.0.0.1:8000  -  demo login: demo / demo12345
python manage.py runserver
