"""
Test Blood Request Email Flow
This script simulates the email flow when a hospital creates a blood request.

Usage: python test_blood_request_email.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from blood_requests.models import BloodRequest
from hospitals.models import HospitalProfile
from donors.models import DonorProfile
from ngos.models import NGOProfile

def test_blood_request_email_flow():
    """Test the email flow for blood requests"""
    
    print("=" * 70)
    print("TESTING BLOOD REQUEST EMAIL FLOW")
    print("=" * 70)
    
    # Check email configuration
    print(f"\n📧 Email Configuration:")
    print(f"   Backend: {settings.EMAIL_BACKEND}")
    print(f"   From: {settings.DEFAULT_FROM_EMAIL}")
    print(f"   SMTP: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
    
    if 'console' in settings.EMAIL_BACKEND.lower():
        print("\n❌ ERROR: Email backend is set to console!")
        print("   Emails will only print to console, not actually send.")
        print("   Please check your .env file.")
        return
    
    if not settings.EMAIL_HOST_USER or settings.EMAIL_HOST_PASSWORD == 'your_app_password_here':
        print("\n❌ ERROR: Email credentials not configured!")
        print("   Please update .env file with your Gmail app password.")
        return
    
    print(f"   ✅ Email configured: {settings.EMAIL_HOST_USER}")
    
    # Check for active NGOs
    ngos = NGOProfile.objects.filter(is_active=True, verification_status='verified')
    print(f"\n🏢 Active NGOs: {ngos.count()}")
    if ngos.exists():
        for ngo in ngos:
            print(f"   - {ngo.ngo_name} ({ngo.email})")
    else:
        print("   ❌ No verified NGOs found!")
    
    # Check for donors
    donors = DonorProfile.objects.filter(is_active=True)
    print(f"\n👤 Active Donors: {donors.count()}")
    if donors.exists():
        for donor in donors[:5]:  # Show first 5
            print(f"   - {donor.full_name} ({donor.blood_group}) - {donor.district} ({donor.email})")
    else:
        print("   ❌ No active donors found!")
    
    # Check for hospitals
    hospitals = HospitalProfile.objects.filter(is_active=True)
    print(f"\n🏥 Active Hospitals: {hospitals.count()}")
    if hospitals.exists():
        for hospital in hospitals[:3]:
            print(f"   - {hospital.hospital_name} ({hospital.district})")
    else:
        print("   ❌ No active hospitals found!")
    
    # Check recent blood requests
    recent_requests = BloodRequest.objects.order_by('-created_at')[:3]
    print(f"\n📝 Recent Blood Requests: {BloodRequest.objects.count()} total")
    if recent_requests.exists():
        for req in recent_requests:
            print(f"   - {req.request_id}: {req.blood_group} ({req.units_required} units) - {req.get_status_display()}")
    
    print("\n" + "=" * 70)
    print("WHAT HAPPENS WHEN HOSPITAL CREATES A BLOOD REQUEST:")
    print("=" * 70)
    print("\n1️⃣  Hospital submits blood request (Blood Group + Units)")
    print("2️⃣  System finds donors with:")
    print("    - Same blood group")
    print("    - Same district (case-insensitive)")
    print("3️⃣  Email sent to NGO with:")
    print("    - Blood request details")
    print("    - Hospital information")
    print("    - Urgency level")
    print("4️⃣  Email sent to EACH matched donor with:")
    print("    - Blood group needed")
    print("    - Hospital name and location")
    print("    - Contact details")
    print("    - Urgency level")
    print("\n📬 All emails will be sent from:", settings.DEFAULT_FROM_EMAIL)
    
    print("\n" + "=" * 70)
    print("TO TEST:")
    print("=" * 70)
    print("\n1. Make sure app password is set in .env file")
    print("2. Restart Django server: python manage.py runserver")
    print("3. Login as hospital: http://127.0.0.1:8000/hospital/login/")
    print("4. Click 'Create Blood Request' or 'Emergency Request'")
    print("5. Select blood group and units")
    print("6. Submit")
    print("7. Check email inboxes:")
    print(f"   - NGO emails: {', '.join([ngo.email for ngo in ngos][:3])}")
    print(f"   - Donor emails: {', '.join([d.email for d in donors][:3])}")
    
    print("\n" + "=" * 70)

if __name__ == '__main__':
    test_blood_request_email_flow()
