@echo off
setlocal
set DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@mainline.proxy.rlwy.net:55942/railway
py manage.py migrate
py manage.py load_questions
endlocal
pause