. setenv.sh
. venv/bin/activate
cd app
uvicorn main:app --reload
$SHELL
cd ..