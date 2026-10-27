$env:DATABASE_URL="postgresql://postgres:WYBkGHTOYUscswwZgFLRpjAznGKCYydy@mainline.proxy.rlwy.net:55942/railway"
py manage.py migrate
py manage.py load_questions
Remove-Item Env:DATABASE_URL