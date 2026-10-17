@echo off
echo ====================================
echo Pushing Railway Deployment Fixes
echo ====================================
echo.

echo What was fixed:
echo - Removed nixpacks.toml (causing pip error)
echo - Cleaned up railway.toml
echo - Added PyMySQL for MySQL support
echo - Fixed Django 4.2+ compatibility
echo.

echo Adding changes to git...
git add .

echo.
echo Committing changes...
git commit -m "Fix Railway deployment: remove nixpacks, add PyMySQL, fix Django settings"

echo.
echo Pushing to GitHub...
git push origin main

echo.
echo ====================================
echo Changes pushed successfully!
echo ====================================
echo.
echo Next Steps in Railway Dashboard:
echo.
echo 1. Add MySQL Database:
echo    - Click "+ New" -^> "Database" -^> "Add MySQL"
echo.
echo 2. Set Environment Variables:
echo    SECRET_KEY=your-secret-key-here
echo    DEBUG=False
echo    ALLOWED_HOSTS=.railway.app
echo    DATABASE_URL=${MYSQL_URL}
echo.
echo 3. Wait for automatic redeploy
echo.
echo 4. Run migrations:
echo    railway run python manage.py migrate
echo.
echo 5. Create superuser:
echo    railway run python manage.py createsuperuser
echo.
echo For detailed instructions, see: RAILWAY_FIX.md
echo.
pause
