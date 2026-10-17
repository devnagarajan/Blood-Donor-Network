"""
Test Email Configuration
Run this script to test if Gmail SMTP is working correctly.

Usage: python test_email.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_email():
    """Test email sending"""
    
    print("=" * 60)
    print("TESTING EMAIL CONFIGURATION")
    print("=" * 60)
    
    # Display current settings
    print(f"\nEmail Backend: {settings.EMAIL_BACKEND}")
    print(f"SMTP Host: {settings.EMAIL_HOST}")
    print(f"SMTP Port: {settings.EMAIL_PORT}")
    print(f"Use TLS: {settings.EMAIL_USE_TLS}")
    print(f"From Email: {settings.DEFAULT_FROM_EMAIL}")
    print(f"Host User: {settings.EMAIL_HOST_USER}")
    
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        print("\n❌ ERROR: Email credentials not configured!")
        print("Please update EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env file")
        return
    
    if settings.EMAIL_HOST_PASSWORD == 'your_app_password_here':
        print("\n❌ ERROR: Please replace 'your_app_password_here' with actual app password!")
        print("See GMAIL_SETUP_INSTRUCTIONS.md for details")
        return
    
    # Get test recipient email
    recipient_email = input("\nEnter recipient email address to test: ").strip()
    
    if not recipient_email:
        print("❌ No email address provided!")
        return
    
    print(f"\n📧 Sending test email to: {recipient_email}")
    print("Please wait...")
    
    try:
        # Send test email
        send_mail(
            subject='RedFusion - Test Email',
            message='This is a test email from RedFusion. If you receive this, your email configuration is working correctly! 🎉',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        
        print("\n✅ SUCCESS! Test email sent successfully!")
        print(f"Check inbox of {recipient_email}")
        print("\n📬 Email Configuration is working correctly!")
        
    except Exception as e:
        print(f"\n❌ ERROR: Failed to send email")
        print(f"Error details: {str(e)}")
        print("\nCommon issues:")
        print("1. Wrong app password (must be 16-digit app password from Google)")
        print("2. 2-Step Verification not enabled on Gmail")
        print("3. Wrong email address")
        print("4. Internet connection issue")
        print("\nSee GMAIL_SETUP_INSTRUCTIONS.md for help")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    test_email()
