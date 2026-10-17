"""
Quick Email Test - Send a test email to verify Gmail SMTP is working
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

print("=" * 70)
print("TESTING EMAIL CONFIGURATION")
print("=" * 70)

print(f"\nEmail Backend: {settings.EMAIL_BACKEND}")
print(f"SMTP Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
print(f"From Email: {settings.EMAIL_HOST_USER}")
print(f"Password Length: {len(settings.EMAIL_HOST_PASSWORD)} characters")

if settings.EMAIL_HOST_PASSWORD == 'your_app_password_here':
    print("\n❌ ERROR: App password not set!")
    print("Please update EMAIL_HOST_PASSWORD in .env file")
    exit()

print("\n📧 Sending test email...")

try:
    send_mail(
        subject='RedFusion - Test Email',
        message='This is a test email. If you receive this, email is working! ✅',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=['peacemaker876r@gmail.com'],  # Send to yourself
        fail_silently=False,
    )
    
    print("\n✅ SUCCESS! Email sent successfully!")
    print("Check your inbox: peacemaker876r@gmail.com")
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    print("\nPossible issues:")
    print("1. Wrong app password (must be 16 characters, no spaces)")
    print("2. 2-Step Verification not enabled on Gmail")
    print("3. App password was deleted/revoked")
    print("\nTo fix:")
    print("1. Go to: https://myaccount.google.com/apppasswords")
    print("2. Generate NEW app password")
    print("3. Update .env file: EMAIL_HOST_PASSWORD=your_new_password")
    print("4. Remove all spaces from password")
    print("5. Run this script again")

print("\n" + "=" * 70)
