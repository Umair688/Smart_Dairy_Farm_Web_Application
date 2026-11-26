#!/usr/bin/env bash
# One-command setup and run for macOS / Linux.
set -e
cd "$(dirname "$0")"
[ -d venv ] || python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
echo
echo "Open http://127.0.0.1:8000  -  demo login: demo / demo12345"
python manage.py runserver
