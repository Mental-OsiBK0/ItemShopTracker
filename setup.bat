@echo off
pip install -r requirements.txt
if not exist .env copy .env.example .env
echo.
echo Setup complete! Open the .env file and add your password.
pause