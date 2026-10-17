@echo off
echo ====================================
echo Blood Donor System - Deployment
echo ====================================
echo.

echo Checking if git is initialized...
if not exist ".git" (
    echo Initializing git repository...
    git init
    git branch -M main
)

echo.
echo Adding all files to git...
git add .

echo.
set /p commit_msg="Enter commit message (or press Enter for default): "
if "%commit_msg%"=="" set commit_msg=Deploy to production

git commit -m "%commit_msg%"

echo.
echo ====================================
echo Next Steps:
echo ====================================
echo.
echo 1. Create a GitHub repository at: https://github.com/new
echo 2. Run these commands:
echo.
echo    git remote add origin https://github.com/devnagarajan/Blood-Donor-Network.git
echo    git push -u origin main
echo.
echo 3. Deploy to Railway:
echo    - Go to: https://railway.app
echo    - Click "New Project" -^> "Deploy from GitHub repo"
echo    - Select your repository
echo    - Add MySQL database
echo    - Set environment variables (see .env.example)
echo.
echo 4. Your app will be live at: your-app.railway.app
echo.
echo For detailed instructions, see: README_DEPLOYMENT.md
echo.
pause
