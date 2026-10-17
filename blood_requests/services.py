"""
Blood Request Services
- Donor matching
- Email notifications
- Request management
"""

from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import Q
from donors.models import DonorProfile
from ngos.models import NGOProfile
from core.models import Notification
from .models import BloodRequest, DonorMatch


class BloodRequestService:
    """Service for managing blood requests"""
    
    @staticmethod
    def find_matching_donors(blood_request):
        """
        Find donors matching blood group and district
        - Same blood group (exact match)
        - Same district (case-insensitive)
        - Active donors only
        """
        donors = DonorProfile.objects.filter(
            blood_group=blood_request.blood_group,
            is_active=True,
            district__iexact=blood_request.hospital.district  # Case-insensitive district match
        ).order_by('-created_at')  # Latest donors first
        
        return donors
    
    @staticmethod
    def assign_ngo(blood_request):
        """
        Assign an active NGO to the blood request
        For now, assign the first verified and active NGO
        In production, this could be based on location, workload, etc.
        """
        ngo = NGOProfile.objects.filter(
            is_active=True,
            verification_status='verified'
        ).first()
        
        if ngo:
            blood_request.assigned_ngo = ngo
            blood_request.save()
        
        return ngo
    
    @staticmethod
    def create_donor_matches(blood_request, donors):
        """
        Create DonorMatch entries for matched donors
        """
        matches = []
        for donor in donors:
            match, created = DonorMatch.objects.get_or_create(
                blood_request=blood_request,
                donor=donor,
                defaults={'match_status': 'notified'}
            )
            matches.append(match)
        
        return matches
    
    @staticmethod
    def process_blood_request(blood_request):
        """
        Main workflow for processing a blood request:
        1. Find matching donors
        2. Assign NGO
        3. Create donor matches
        4. Send notifications
        5. Send emails (in background)
        """
        # Find matching donors
        matching_donors = BloodRequestService.find_matching_donors(blood_request)
        
        # Assign NGO
        assigned_ngo = BloodRequestService.assign_ngo(blood_request)
        
        # Create donor matches
        if matching_donors.exists():
            BloodRequestService.create_donor_matches(blood_request, matching_donors)
        
        # Create in-app notifications immediately
        if assigned_ngo:
            NotificationService.notify_ngo_new_request(assigned_ngo.user, blood_request)
        
        if matching_donors.exists():
            NotificationService.notify_donors_new_request(matching_donors, blood_request)
        
        # Send emails in background thread (non-blocking)
        import threading
        
        def send_emails_async():
            """Send emails in background"""
            if assigned_ngo:
                try:
                    EmailService.send_request_to_ngo(blood_request, assigned_ngo)
                except Exception as e:
                    print(f"Error sending email to NGO: {e}")
            
            if matching_donors.exists():
                try:
                    EmailService.send_request_to_donors(blood_request, matching_donors)
                except Exception as e:
                    print(f"Error sending emails to donors: {e}")
        
        # Start email thread
        email_thread = threading.Thread(target=send_emails_async)
        email_thread.daemon = True  # Thread will close when main program exits
        email_thread.start()
        
        return {
            'matching_donors_count': matching_donors.count(),
            'assigned_ngo': assigned_ngo,
            'success': True
        }


class EmailService:
    """Service for sending emails"""
    
    @staticmethod
    def send_donor_registration_to_ngo(donor_profile):
        """Send new donor registration details to all NGOs"""
        # Get all verified and active NGOs
        ngos = NGOProfile.objects.filter(
            is_active=True,
            verification_status='verified'
        )
        
        if not ngos.exists():
            return False
        
        subject = f"New Donor Registered - {donor_profile.blood_group} - {donor_profile.district}"
        
        for ngo in ngos:
            context = {
                'donor': donor_profile,
                'ngo': ngo,
            }
            
            html_message = render_to_string('email/donor_registration_ngo.html', context)
            plain_message = f"""
Dear {ngo.ngo_name},

A new blood donor has registered in the RedFusion.

Donor Details:
Name: {donor_profile.full_name}
Blood Group: {donor_profile.blood_group}
Location: {donor_profile.district}, {donor_profile.state}
Age: {donor_profile.age} years
Gender: {donor_profile.get_gender_display()}
Phone: {donor_profile.phone_number}
Email: {donor_profile.email}
Status: Available for donation

This donor is now available in the system for blood requests.

Best regards,
RedFusion
            """
            
            try:
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[ngo.email],
                    html_message=html_message,
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error sending donor registration email to NGO {ngo.ngo_name}: {e}")
        
        return True
    
    @staticmethod
    def send_request_to_ngo(blood_request, ngo):
        """Send blood request details to NGO"""
        subject = f"{'Emergency' if blood_request.is_urgent() else 'New'} Blood Request - {blood_request.blood_group} Required - {blood_request.hospital.district}"
        
        context = {
            'blood_request': blood_request,
            'ngo': ngo,
        }
        
        html_message = render_to_string('email/blood_request_ngo.html', context)
        plain_message = f"""
Blood Request ID: {blood_request.request_id}
Hospital: {blood_request.hospital.hospital_name}
Blood Group: {blood_request.blood_group}
Units Required: {blood_request.units_required}
Urgency: {blood_request.get_urgency_display()}
Required Date: {blood_request.required_date}
Patient: {blood_request.patient_name} ({blood_request.patient_age} years)
Contact: {blood_request.contact_person} - {blood_request.contact_number}

Please log in to the portal to manage this request.
        """
        
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[ngo.email],
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Error sending email to NGO: {e}")
            return False
    
    @staticmethod
    def send_request_to_donors(blood_request, donors):
        """Send blood request notification to matched donors"""
        subject = f"Blood Donation Needed - {blood_request.blood_group} - {blood_request.hospital.district}"
        
        for donor in donors:
            context = {
                'donor': donor,
                'blood_request': blood_request,
            }
            
            html_message = render_to_string('email/blood_request_donor.html', context)
            plain_message = f"""
Dear {donor.full_name},

A blood request matching your blood group has been received.

Blood Group: {blood_request.blood_group}
Units Required: {blood_request.units_required}
Hospital: {blood_request.hospital.hospital_name}
Location: {blood_request.hospital.district}, {blood_request.hospital.state}
Required By: {blood_request.required_date}
Urgency: {blood_request.get_urgency_display()}

Your contribution can save a life. Please contact the hospital or log in to the portal for more details.

Contact: {blood_request.contact_person} - {blood_request.contact_number}

Thank you for being a registered blood donor.
            """
            
            try:
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[donor.email],
                    html_message=html_message,
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error sending email to donor {donor.full_name}: {e}")
    
    @staticmethod
    def send_request_status_update(blood_request):
        """Send email when request status changes"""
        subject = f"Blood Request {blood_request.request_id} Status Updated"
        
        message = f"""
Your blood request {blood_request.request_id} has been updated.

New Status: {blood_request.get_status_display()}
Units Required: {blood_request.units_required}
Units Fulfilled: {blood_request.units_fulfilled}

Log in to the portal for more details.
        """
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[blood_request.hospital.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Error sending status update email: {e}")


class NotificationService:
    """Service for creating in-app notifications"""
    
    @staticmethod
    def notify_ngo_new_request(ngo_user, blood_request):
        """Create notification for NGO"""
        Notification.objects.create(
            recipient=ngo_user,
            title=f"New Blood Request - {blood_request.blood_group}",
            message=f"Hospital {blood_request.hospital.hospital_name} has requested {blood_request.units_required} units of {blood_request.blood_group} blood. Urgency: {blood_request.get_urgency_display()}",
            notification_type='blood_request',
            related_blood_request_id=blood_request.id
        )
    
    @staticmethod
    def notify_donors_new_request(donors, blood_request):
        """Create notifications for matched donors"""
        notifications = []
        for donor in donors:
            notification = Notification(
                recipient=donor.user,
                title=f"Blood Donation Needed - {blood_request.blood_group}",
                message=f"A blood request matching your blood group has been received from {blood_request.hospital.district}. Required by {blood_request.required_date}.",
                notification_type='blood_request',
                related_blood_request_id=blood_request.id
            )
            notifications.append(notification)
        
        Notification.objects.bulk_create(notifications)
    
    @staticmethod
    def notify_request_status_change(blood_request):
        """Notify hospital when request status changes"""
        Notification.objects.create(
            recipient=blood_request.hospital.user,
            title=f"Request {blood_request.request_id} Updated",
            message=f"Your blood request status has been updated to {blood_request.get_status_display()}. Units fulfilled: {blood_request.units_fulfilled}/{blood_request.units_required}",
            notification_type='request_update',
            related_blood_request_id=blood_request.id
        )


class CampNotificationService:
    """Service for Blood Camp notifications"""
    
    @staticmethod
    def notify_ngo_donor_registered(camp, donor, registration):
        """Send email to NGO when donor registers for camp"""
        ngo = camp.organized_by
        
        subject = f"New Donor Registration - {camp.camp_name} - {donor.blood_group}"
        
        context = {
            'camp': camp,
            'donor': donor,
            'registration': registration,
            'ngo': ngo,
        }
        
        html_message = render_to_string('email/camp_donor_registration_ngo.html', context)
        plain_message = f"""
Dear {ngo.ngo_name},

A donor has registered for your blood camp!

Camp Details:
Camp Name: {camp.camp_name}
Date: {camp.camp_date}
Time: {camp.start_time} - {camp.end_time}
Venue: {camp.venue_name}, {camp.district}

Donor Details:
Name: {donor.full_name}
Blood Group: {donor.blood_group}
Phone: {donor.phone_number}
Email: {donor.email}
Location: {donor.district}, {donor.state}

Camp Status:
Registered: {camp.registered_count} / {camp.total_capacity} donors
Available Spots: {camp.total_capacity - camp.registered_count}

Log in to the portal to view all registrations.

Best regards,
RedFusion
        """
        
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[ngo.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            # Also create in-app notification
            Notification.objects.create(
                recipient=ngo.user,
                title=f"New Camp Registration - {donor.blood_group}",
                message=f"{donor.full_name} registered for {camp.camp_name} on {camp.camp_date}. Total registrations: {camp.registered_count}/{camp.total_capacity}",
                notification_type='camp_registration',
            )
            
            return True
        except Exception as e:
            print(f"Error sending camp registration email to NGO: {e}")
            return False
