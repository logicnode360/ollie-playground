@REM  $env:DATABASE_URL="postgresql://postgres:WYBkGHTOYUscswwZgFLRpjAznGKCYydy@mainline.proxy.rlwy.net:55942/railway"
@REM  py manage.py migrate
@REM  py manage.py load_questions
@REM  Remove-Item Env:DATABASE_URL
@echo off
setlocal
set DATABASE_URL=postgresql://postgres:WYBkGHTOYUscswwZgFLRpjAznGKCYydy@mainline.proxy.rlwy.net:55942/railway
py manage.py migrate
py manage.py load_questions
endlocal
pause