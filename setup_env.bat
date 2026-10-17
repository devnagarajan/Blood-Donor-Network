@echo off
echo ====================================
echo Environment Setup for Deployment
echo ====================================
echo.

if exist ".env" (
    echo .env file already exists!
    set /p overwrite="Overwrite? (y/n): "
    if not "%overwrite%"=="y" (
        echo Setup cancelled.
        pause
        exit /b
    )
)

echo Creating .env file...
echo.

:: Generate a random SECRET_KEY
set "chars=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%%^&*"
set "secret_key="
for /L %%i in (1,1,50) do (
    set /a "rand=!RANDOM! %% 64"
    for %%j in (!rand!) do set "secret_key=!secret_key!!chars:~%%j,1!"
)

echo # Django Settings > .env
echo SECRET_KEY=django-insecure-%RANDOM%%RANDOM%%RANDOM% >> .env
echo DEBUG=True >> .env
echo ALLOWED_HOSTS=localhost,127.0.0.1 >> .env
echo. >> .env
echo # Database Configuration >> .env
echo DB_NAME=blood_donor_db >> .env
echo DB_USER=root >> .env
set /p db_password="Enter MySQL password (or press Enter for empty): "
echo DB_PASSWORD=%db_password% >> .env
echo DB_HOST=127.0.0.1 >> .env
echo DB_PORT=3306 >> .env
echo. >> .env
echo # Email Configuration >> .env
echo EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend >> .env
echo EMAIL_HOST=smtp.gmail.com >> .env
echo EMAIL_PORT=587 >> .env
echo EMAIL_USE_TLS=True >> .env
echo EMAIL_HOST_USER= >> .env
echo EMAIL_HOST_PASSWORD= >> .env
echo DEFAULT_FROM_EMAIL=noreply@blooddonor.com >> .env

echo.
echo ====================================
echo .env file created successfully!
echo ====================================
echo.
echo Next steps:
echo 1. Review and edit .env file if needed
echo 2. Make sure MySQL is running
echo 3. Run: python manage.py migrate
echo 4. Run: python manage.py createsuperuser
echo 5. Run: python manage.py runserver
echo.
echo For deployment, see: CLOUDFLARE_DEPLOYMENT.md
echo.
pause
