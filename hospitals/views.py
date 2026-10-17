from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Count, Case, When, IntegerField
from django.http import JsonResponse
from accounts.models import User
from .models import HospitalProfile
from .forms import HospitalRegistrationForm, HospitalProfileForm, BloodRequestForm
from blood_requests.models import BloodRequest
from blood_requests.services import BloodRequestService
from core.models import Notification
from donors.models import DonorProfile

def hospital_register(request):
    """Hospital Registration Step 1: Account Creation"""
    
    if request.user.is_authenticated:
        return redirect('hospitals:dashboard')
    
    if request.method == 'POST':
        user_form = HospitalRegistrationForm(request.POST)
        profile_form = HospitalProfileForm(request.POST, request.FILES)
        
        if user_form.is_valid() and profile_form.is_valid():
            # Create user
            user = user_form.save()
            
            # Create hospital profile
            hospital_profile = profile_form.save(commit=False)
            hospital_profile.user = user
            hospital_profile.hospital_name = user_form.cleaned_data['hospital_name']
            hospital_profile.email = user_form.cleaned_data['email']
            hospital_profile.phone_number = user_form.cleaned_data['phone_number']
            hospital_profile.save()
            
            messages.success(
                request,
                'Hospital registration successful. Please login to continue.'
            )
            return redirect('hospitals:login')
    else:
        user_form = HospitalRegistrationForm()
        profile_form = HospitalProfileForm()
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }
    return render(request, 'auth/hospital_register.html', context)


def hospital_login(request):
    """Hospital Login"""
    
    if request.user.is_authenticated:
        return redirect('hospitals:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Block admin users from logging in here
            if user.is_staff or user.is_superuser:
                messages.error(request, 'Admin users should login through admin panel at /admin/')
                return render(request, 'auth/hospital_login.html')
            
            if user.role == User.Role.HOSPITAL:
                login(request, user)
                return redirect('hospitals:dashboard')
            else:
                messages.error(request, 'Invalid credentials for hospital login.')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'auth/hospital_login.html')


def hospital_logout(request):
    """Hospital Logout"""
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
    return redirect('core:home')


@login_required
def hospital_dashboard(request):
    """Hospital Dashboard - Optimized"""
    
    # Block admin users
    if request.user.is_staff or request.user.is_superuser:
        messages.warning(request, 'Admin users should use the admin panel.')
        logout(request)
        return redirect('/admin/')
    
    if not request.user.is_hospital():
        raise PermissionDenied
    
    hospital_profile = get_object_or_404(HospitalProfile, user=request.user)
    
    # Use single aggregated query for statistics (faster)
    from django.db.models import Q, Count, Case, When, IntegerField
    stats = BloodRequest.objects.filter(hospital=hospital_profile).aggregate(
        total=Count('id'),
        pending=Count(Case(When(status='pending', then=1), output_field=IntegerField())),
        fulfilled=Count(Case(When(status='fulfilled', then=1), output_field=IntegerField())),
        active=Count(Case(When(Q(status__in=['pending', 'accepted', 'partially_fulfilled']), then=1), output_field=IntegerField()))
    )
    
    # Get recent requests with optimized select_related
    recent_requests = BloodRequest.objects.filter(
        hospital=hospital_profile
    ).select_related('assigned_ngo').order_by('-created_at')[:5]
    
    # Get recent donation confirmations
    from blood_requests.models import DonationConfirmation
    recent_donations = DonationConfirmation.objects.filter(
        hospital=hospital_profile,
        status='completed'
    ).select_related('donor').order_by('-donation_datetime')[:10]
    
    # Get unread notifications count (cached)
    from django.core.cache import cache
    cache_key = f'unread_notif_hospital_{request.user.id}'
    unread_notifications_count = cache.get(cache_key)
    if unread_notifications_count is None:
        unread_notifications_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        cache.set(cache_key, unread_notifications_count, 60)  # Cache for 1 minute
    
    context = {
        'hospital_profile': hospital_profile,
        'total_requests': stats['total'],
        'pending_requests': stats['pending'],
        'fulfilled_requests': stats['fulfilled'],
        'active_requests': stats['active'],
        'recent_requests': recent_requests,
        'recent_donations': recent_donations,
        'unread_notifications_count': unread_notifications_count,
    }
    
    return render(request, 'hospital/dashboard.html', context)


@login_required
def hospital_profile(request):
    """View Hospital Profile"""
    
    if not request.user.is_hospital():
        raise PermissionDenied
    
    hospital_profile = get_object_or_404(HospitalProfile, user=request.user)
    
    context = {'hospital_profile': hospital_profile}
    return render(request, 'hospital/profile.html', context)


@login_required
def edit_hospital_profile(request):
    """Edit Hospital Profile"""
    
    if not request.user.is_hospital():
        raise PermissionDenied
    
    hospital_profile = get_object_or_404(HospitalProfile, user=request.user)
    
    if request.method == 'POST':
        form = HospitalProfileForm(request.POST, request.FILES, instance=hospital_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Hospital profile updated successfully!')
            return redirect('hospitals:profile')
    else:
        form = HospitalProfileForm(instance=hospital_profile)
    
    context = {
        'form': form,
        'hospital_profile': hospital_profile
    }
    return render(request, 'hospital/edit_profile.html', context)


@login_required
def create_blood_request(request):
    """Create Blood Request - Ultra Simple: Blood Group + Units Only"""
    
    if not request.user.is_hospital():
        raise PermissionDenied
    
    hospital_profile = get_object_or_404(HospitalProfile, user=request.user)
    
    # Check if hospital is verified
    if not hospital_profile.is_verified():
        messages.warning(
            request,
            'Your hospital profile is pending verification. You can create requests after verification.'
        )
        return redirect('hospitals:dashboard')
    
    if request.method == 'POST':
        form = BloodRequestForm(request.POST)
        if form.is_valid():
            blood_request = form.save(commit=False)
            blood_request.hospital = hospital_profile
            
            # Auto-fill ALL other fields
            blood_request.urgency = 'normal'  # Default urgency
            blood_request.contact_person = hospital_profile.contact_person_name
            blood_request.contact_number = hospital_profile.emergency_contact_number
            blood_request.patient_name = "Patient"
            blood_request.patient_age = 0
            blood_request.patient_gender = "other"
            blood_request.reason = f"Blood requirement for {hospital_profile.hospital_name}"
            
            # Required date is now provided by user in form (no auto-setting)
            
            blood_request.save()
            
            # Process blood request: Match donors, assign NGO, send emails
            result = BloodRequestService.process_blood_request(blood_request)
            
            if result['success']:
                messages.success(
                    request,
                    f'✅ Blood request {blood_request.request_id} created successfully! '
                    f'NGO and {result["matching_donors_count"]} matching donors notified via email.'
                )
            else:
                messages.warning(
                    request,
                    f'Blood request {blood_request.request_id} created. NGO notified to find donors.'
                )
            
            return redirect('hospitals:blood_request_detail', pk=blood_request.id)
    else:
        form = BloodRequestForm()
    
    context = {'form': form, 'hospital_profile': hospital_profile}
    return render(request, 'hospital/create_blood_request.html', context)


@login_required
def create_emergency_request(request):
    """Create Emergency Blood Request - Blood Group + Units Only"""
    
    if not request.user.is_hospital():
        raise PermissionDenied
    
    hospital_profile = get_object_or_404(HospitalProfile, user=request.user)
    
    # Check if hospital is verified
    if not hospital_profile.is_verified():
        messages.warning(
            request,
            'Your hospital profile is pending verification. You can create requests after verification.'
        )
        return redirect('hospitals:dashboard')
    
    if request.method == 'POST':
        form = BloodRequestForm(request.POST)
        if form.is_valid():
            blood_request = form.save(commit=False)
            blood_request.hospital = hospital_profile
            blood_request.urgency = 'critical'  # Emergency = Critical
            
            # Auto-fill all other fields
            blood_request.contact_person = hospital_profile.contact_person_name
            blood_request.contact_number = hospital_profile.emergency_contact_number
            blood_request.patient_name = "Emergency Patient"
            blood_request.patient_age = 0
            blood_request.patient_gender = "other"
            blood_request.reason = f"🚨 EMERGENCY blood requirement at {hospital_profile.hospital_name}"
            
            # Required date is now provided by user in form (no auto-setting)
            
            blood_request.save()
            
            # Process emergency blood request
            result = BloodRequestService.process_blood_request(blood_request)
            
            if result['success']:
                messages.success(
                    request,
                    f'🚨 EMERGENCY Blood Request {blood_request.request_id} created! '
                    f'NGO and {result["matching_donors_count"]} donors notified immediately.'
                )
            else:
                messages.warning(
                    request,
                    f'Emergency request {blood_request.request_id} created. '
                    f'NGO has been notified to search for donors urgently.'
                )
            
            return redirect('hospitals:blood_request_detail', pk=blood_request.id)
    else:
        form = BloodRequestForm()
    
    context = {
        'form': form,
        'hospital_profile': hospital_profile,
        'is_emergency': True
    }
    return render(request, 'hospital/create_blood_request.html', context)


@login_required
def blood_requests_list(request):
    """List All Blood Requests"""
    
    if not request.user.is_hospital():
        raise PermissionDenied
    
    hospital_profile = get_object_or_404(HospitalProfile, user=request.user)
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    blood_group_filter = request.GET.get('blood_group', '')
    
    requests = BloodRequest.objects.filter(hospital=hospital_profile)
    
    if status_filter:
        requests = requests.filter(status=status_filter)
    if blood_group_filter:
        requests = requests.filter(blood_group=blood_group_filter)
    
    requests = requests.order_by('-created_at')
    
    context = {
        'hospital_profile': hospital_profile,
        'requests': requests,
        'status_filter': status_filter,
        'blood_group_filter': blood_group_filter,
    }
    return render(request, 'hospital/blood_requests_list.html', context)


@login_required
def blood_request_detail(request, pk):
    """View Blood Request Details"""
    
    if not request.user.is_hospital():
        raise PermissionDenied
    
    hospital_profile = get_object_or_404(HospitalProfile, user=request.user)
    blood_request = get_object_or_404(
        BloodRequest,
        pk=pk,
        hospital=hospital_profile
    )
    
    # Get matched donors
    matched_donors = blood_request.matched_donors.all()
    
    context = {
        'hospital_profile': hospital_profile,
        'blood_request': blood_request,
        'matched_donors': matched_donors,
    }
    return render(request, 'hospital/blood_request_detail.html', context)


@login_required
def cancel_blood_request(request, pk):
    """Cancel Blood Request"""
    
    if not request.user.is_hospital():
        raise PermissionDenied
    
    hospital_profile = get_object_or_404(HospitalProfile, user=request.user)
    blood_request = get_object_or_404(
        BloodRequest,
        pk=pk,
        hospital=hospital_profile
    )
    
    if blood_request.status in ['pending', 'accepted']:
        blood_request.status = 'cancelled'
        blood_request.save()
        messages.success(request, f'Blood request {blood_request.request_id} cancelled successfully.')
    else:
        messages.error(request, 'Cannot cancel this request.')
    
    return redirect('hospitals:blood_request_detail', pk=pk)


@login_required
def notifications(request):
    """View Notifications"""
    
    if not request.user.is_hospital():
        raise PermissionDenied
    
    notifications_list = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')
    
    # Mark all as read
    notifications_list.filter(is_read=False).update(is_read=True)
    
    context = {'notifications': notifications_list}
    return render(request, 'hospital/notifications.html', context)



@login_required
def donation_history(request):
    """View Donation History - Donors who donated to this hospital"""
    
    if not request.user.is_hospital():
        raise PermissionDenied
    
    hospital_profile = get_object_or_404(HospitalProfile, user=request.user)
    
    # Get all blood requests from this hospital
    # Get donors who have donated (status='donated' in DonorMatch)
    from blood_requests.models import DonorMatch
    from django.db.models import Count, Q
    
    # Get all donations for this hospital
    donations = DonorMatch.objects.filter(
        blood_request__hospital=hospital_profile,
        match_status='donated'
    ).select_related(
        'donor',
        'donor__user',
        'blood_request'
    ).order_by('-updated_at')
    
    # Get filter parameters
    blood_group_filter = request.GET.get('blood_group', '')
    donor_search = request.GET.get('donor_search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if blood_group_filter:
        donations = donations.filter(donor__blood_group=blood_group_filter)
    
    if donor_search:
        donations = donations.filter(
            Q(donor__full_name__icontains=donor_search) |
            Q(donor__donor_id__icontains=donor_search)
        )
    
    if date_from:
        donations = donations.filter(updated_at__gte=date_from)
    
    if date_to:
        donations = donations.filter(updated_at__lte=date_to)
    
    # Statistics
    total_donations = donations.count()
    
    # Group by blood group
    blood_group_stats = donations.values('donor__blood_group').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'hospital_profile': hospital_profile,
        'donations': donations,
        'total_donations': total_donations,
        'blood_group_stats': blood_group_stats,
        'blood_group_filter': blood_group_filter,
        'donor_search': donor_search,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'hospital/donation_history.html', context)


@login_required
def export_donation_history_pdf(request):
    """Export Donation History as PDF"""
    
    if not request.user.is_hospital():
        raise PermissionDenied
    
    hospital_profile = get_object_or_404(HospitalProfile, user=request.user)
    
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from blood_requests.models import DonorMatch
    from datetime import datetime
    
    # Get filter parameters from query string
    blood_group_filter = request.GET.get('blood_group', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Get donations
    donations = DonorMatch.objects.filter(
        blood_request__hospital=hospital_profile,
        match_status='donated'
    ).select_related(
        'donor',
        'donor__user',
        'blood_request'
    ).order_by('-updated_at')
    
    if blood_group_filter:
        donations = donations.filter(donor__blood_group=blood_group_filter)
    
    if date_from:
        donations = donations.filter(updated_at__gte=date_from)
    
    if date_to:
        donations = donations.filter(updated_at__lte=date_to)
    
    # Create HTTP response with PDF headers
    response = HttpResponse(content_type='application/pdf')
    filename = f'Donation_History_{hospital_profile.hospital_name.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Create PDF document
    doc = SimpleDocTemplate(response, pagesize=A4,
                            rightMargin=30, leftMargin=30,
                            topMargin=50, bottomMargin=30)
    
    # Container for PDF elements
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#dc3545'),
        alignment=TA_CENTER,
        spaceAfter=12
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubTitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c3e50'),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#dc3545'),
        spaceAfter=8
    )
    
    # Title
    elements.append(Paragraph("RedFusion Blood Donor Network", title_style))
    elements.append(Paragraph("Donation History Report", subtitle_style))
    elements.append(Spacer(1, 12))
    
    # Hospital Information
    hospital_data = [
        ['Hospital Name:', hospital_profile.hospital_name],
        ['Hospital Type:', hospital_profile.get_hospital_type_display()],
        ['Contact:', hospital_profile.phone_number],
        ['Email:', hospital_profile.email],
        ['Report Generated:', datetime.now().strftime('%d %b %Y, %I:%M %p')],
    ]
    
    hospital_table = Table(hospital_data, colWidths=[2*inch, 4*inch])
    hospital_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(hospital_table)
    elements.append(Spacer(1, 20))
    
    # Filters Applied
    if blood_group_filter or date_from or date_to:
        elements.append(Paragraph("Filters Applied:", heading_style))
        filter_data = []
        if blood_group_filter:
            filter_data.append(['Blood Group:', blood_group_filter])
        if date_from:
            filter_data.append(['From Date:', date_from])
        if date_to:
            filter_data.append(['To Date:', date_to])
        
        filter_table = Table(filter_data, colWidths=[2*inch, 4*inch])
        filter_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#fff3cd')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        elements.append(filter_table)
        elements.append(Spacer(1, 20))
    
    # Statistics
    elements.append(Paragraph("Summary Statistics:", heading_style))
    stats_data = [
        ['Total Donations:', str(donations.count())],
        ['Unique Donors:', str(donations.values('donor').distinct().count())],
    ]
    
    stats_table = Table(stats_data, colWidths=[2*inch, 4*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#d4edda')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 20))
    
    # Donation Details Table
    elements.append(Paragraph("Donation Details:", heading_style))
    
    # Table header
    table_data = [['#', 'Donor Name', 'Blood Group', 'Request ID', 'Donation Date', 'Contact']]
    
    # Table rows
    for idx, donation in enumerate(donations, 1):
        table_data.append([
            str(idx),
            donation.donor.full_name,
            donation.donor.blood_group,
            donation.blood_request.request_id,
            donation.updated_at.strftime('%d %b %Y'),
            donation.donor.phone_number,
        ])
    
    # Create table
    donations_table = Table(table_data, colWidths=[0.5*inch, 1.8*inch, 0.8*inch, 1.2*inch, 1.2*inch, 1.3*inch])
    donations_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc3545')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Body
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (2, 1), (2, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Alternating row colors
        *[('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8f9fa')) for i in range(2, len(table_data), 2)]
    ]))
    elements.append(donations_table)
    elements.append(Spacer(1, 20))
    
    # Footer
    footer_text = f"<para align=center><font size=8 color='grey'>This is a computer-generated document from RedFusion Blood Donor Network.<br/>Report generated on {datetime.now().strftime('%d %B %Y at %I:%M %p')}</font></para>"
    elements.append(Spacer(1, 30))
    elements.append(Paragraph(footer_text, styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    
    return response



@login_required
def get_donor_details_api(request, donor_id):
    """API endpoint to get donor details by donor_id for auto-filling form"""
    
    if not request.user.is_hospital():
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        donor = DonorProfile.objects.get(donor_id=donor_id, is_active=True)
        
        # Prepare donor data
        donor_data = {
            'success': True,
            'donor_id': donor.donor_id,
            'pk': donor.pk,
            'full_name': donor.full_name,
            'blood_group': donor.blood_group,
            'phone_number': donor.phone_number,
            'email': donor.email,
            'address': donor.address,
            'city': donor.city,
            'district': donor.district,
            'state': donor.state,
            'pincode': donor.pincode,
            'age': donor.age,
            'gender': donor.get_gender_display(),
            'last_donation_date': donor.last_donation_date.strftime('%Y-%m-%d') if donor.last_donation_date else None,
            'total_donations': donor.total_donations,
            'is_available': donor.is_available,
            'emergency_contact_name': donor.emergency_contact_name or '',
            'emergency_contact_number': donor.emergency_contact_number or '',
        }
        
        return JsonResponse(donor_data)
        
    except DonorProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Donor not found with this ID'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def confirm_donation(request):
    """Hospital Staff - Confirm Donation (Direct Confirmation - No OTP)"""
    
    if not request.user.is_hospital():
        raise PermissionDenied
    
    hospital_profile = get_object_or_404(HospitalProfile, user=request.user)
    
    from blood_requests.forms import DonationConfirmationForm
    from blood_requests.models import DonationConfirmation
    from datetime import datetime
    
    if request.method == 'POST':
        # Get donor from hidden field
        donor_id = request.POST.get('donor')
        
        if not donor_id:
            messages.error(request, 'Please fetch donor details first.')
            return redirect('hospitals:confirm_donation')
        
        try:
            donor = DonorProfile.objects.get(pk=donor_id, is_active=True)
        except DonorProfile.DoesNotExist:
            messages.error(request, 'Invalid donor selected.')
            return redirect('hospitals:confirm_donation')
        
        form = DonationConfirmationForm(request.POST)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.hospital = hospital_profile
            donation.donor = donor  # Set donor from hidden field
            donation.confirmed_by = request.user
            
            # Combine date and time with timezone awareness
            donation_date = form.cleaned_data['donation_date']
            donation_time = form.cleaned_data['donation_time']
            from django.utils import timezone
            naive_datetime = datetime.combine(donation_date, donation_time)
            donation.donation_datetime = timezone.make_aware(naive_datetime)
            
            # Direct completion - No OTP
            donation.status = 'completed'
            donation.save()
            
            # Update donor's last donation date and total donations
            donor = donation.donor
            donor.last_donation_date = donation.donation_datetime.date()
            donor.total_donations += 1
            donor.save()
            
            # Create donation history entry
            from donors.models import DonationHistory
            DonationHistory.objects.create(
                donor=donor,
                donation_date=donation.donation_datetime.date(),
                blood_group=donation.blood_group,
                units_donated=donation.units_donated,
                venue=donation.hospital.hospital_name,
                remarks=f"Blood Bag ID: {donation.blood_bag_id}. {donation.notes}"
            )
            
            # If linked to blood request, update DonorMatch status
            if donation.blood_request:
                from blood_requests.models import DonorMatch
                match, created = DonorMatch.objects.get_or_create(
                    blood_request=donation.blood_request,
                    donor=donor,
                    defaults={'match_status': 'donated'}
                )
                if not created:
                    match.match_status = 'donated'
                    match.save()
            
            messages.success(
                request,
                f'🎉 Donation confirmed successfully! Donation ID: {donation.donation_id}'
            )
            return redirect('hospitals:donation_success', pk=donation.id)
    else:
        form = DonationConfirmationForm()
    
    context = {
        'hospital_profile': hospital_profile,
        'form': form,
    }
    return render(request, 'hospital/confirm_donation.html', context)


@login_required
def verify_donation_otp(request, pk):
    """Hospital Staff - Verify Donor OTP (Step 2: OTP Verification)"""
    
    if not request.user.is_hospital():
        raise PermissionDenied
    
    hospital_profile = get_object_or_404(HospitalProfile, user=request.user)
    
    from blood_requests.models import DonationConfirmation
    from blood_requests.forms import OTPVerificationForm
    
    donation = get_object_or_404(
        DonationConfirmation,
        pk=pk,
        hospital=hospital_profile
    )
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            entered_otp = form.cleaned_data['otp_code']
            success, message = donation.verify_otp(entered_otp)
            
            if success:
                # Update donation status to completed
                donation.status = 'completed'
                donation.save()
                
                # Update donor's last donation date and total donations
                donor = donation.donor
                donor.last_donation_date = donation.donation_datetime.date()
                donor.total_donations += 1
                donor.save()
                
                # Create donation history entry
                from donors.models import DonationHistory
                DonationHistory.objects.create(
                    donor=donor,
                    donation_date=donation.donation_datetime.date(),
                    blood_group=donation.blood_group,
                    units_donated=donation.units_donated,
                    venue=donation.hospital.hospital_name,
                    remarks=f"Blood Bag ID: {donation.blood_bag_id}. {donation.notes}"
                )
                
                # If linked to blood request, update DonorMatch status
                if donation.blood_request:
                    from blood_requests.models import DonorMatch
                    match, created = DonorMatch.objects.get_or_create(
                        blood_request=donation.blood_request,
                        donor=donor,
                        defaults={'match_status': 'donated'}
                    )
                    if not created:
                        match.match_status = 'donated'
                        match.save()
                
                messages.success(
                    request,
                    f'🎉 Donation completed successfully! '
                    f'Donation ID: {donation.donation_id}'
                )
                return redirect('hospitals:donation_success', pk=donation.id)
            else:
                messages.error(request, f'❌ {message}')
    else:
        form = OTPVerificationForm()
    
    context = {
        'hospital_profile': hospital_profile,
        'donation': donation,
        'form': form,
    }
    return render(request, 'hospital/verify_donation_otp.html', context)


@login_required
def resend_donation_otp(request, pk):
    """Resend OTP for donation confirmation"""
    
    if not request.user.is_hospital():
        raise PermissionDenied
    
    hospital_profile = get_object_or_404(HospitalProfile, user=request.user)
    
    from blood_requests.models import DonationConfirmation
    
    donation = get_object_or_404(
        DonationConfirmation,
        pk=pk,
        hospital=hospital_profile
    )
    
    # Reset OTP attempts
    donation.otp_attempts = 0
    donation.save()
    
    # Generate new OTP
    otp = donation.generate_otp()
    
    messages.success(
        request,
        f'📱 New OTP sent to {donation.donor.phone_number}. '
        f'(Demo OTP: {otp})'
    )
    
    return redirect('hospitals:verify_donation_otp', pk=donation.id)


@login_required
def donation_success(request, pk):
    """Donation Success Page"""
    
    if not request.user.is_hospital():
        raise PermissionDenied
    
    hospital_profile = get_object_or_404(HospitalProfile, user=request.user)
    
    from blood_requests.models import DonationConfirmation
    
    donation = get_object_or_404(
        DonationConfirmation,
        pk=pk,
        hospital=hospital_profile
    )
    
    context = {
        'hospital_profile': hospital_profile,
        'donation': donation,
    }
    return render(request, 'hospital/donation_success.html', context)


@login_required
def donation_confirmations_list(request):
    """List all donation confirmations"""
    
    if not request.user.is_hospital():
        raise PermissionDenied
    
    hospital_profile = get_object_or_404(HospitalProfile, user=request.user)
    
    from blood_requests.models import DonationConfirmation
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    blood_group_filter = request.GET.get('blood_group', '')
    
    confirmations = DonationConfirmation.objects.filter(
        hospital=hospital_profile
    ).select_related('donor', 'confirmed_by')
    
    if status_filter:
        confirmations = confirmations.filter(status=status_filter)
    if blood_group_filter:
        confirmations = confirmations.filter(blood_group=blood_group_filter)
    
    confirmations = confirmations.order_by('-donation_datetime')
    
    # Statistics
    from django.db.models import Count, Q
    stats = confirmations.aggregate(
        total=Count('id'),
        completed=Count(Case(When(status='completed', then=1), output_field=IntegerField())),
        verified=Count(Case(When(status='verified', then=1), output_field=IntegerField())),
    )
    
    context = {
        'hospital_profile': hospital_profile,
        'confirmations': confirmations,
        'status_filter': status_filter,
        'blood_group_filter': blood_group_filter,
        'stats': stats,
    }
    return render(request, 'hospital/donation_confirmations_list.html', context)


@login_required
def donation_confirmation_detail(request, pk):
    """View donation confirmation details"""
    
    if not request.user.is_hospital():
        raise PermissionDenied
    
    hospital_profile = get_object_or_404(HospitalProfile, user=request.user)
    
    from blood_requests.models import DonationConfirmation
    
    confirmation = get_object_or_404(
        DonationConfirmation,
        pk=pk,
        hospital=hospital_profile
    )
    
    context = {
        'hospital_profile': hospital_profile,
        'confirmation': confirmation,
    }
    return render(request, 'hospital/donation_confirmation_detail.html', context)


@login_required
def export_confirmations_csv(request):
    """Export Donation Confirmations as CSV"""
    
    if not request.user.is_hospital():
        raise PermissionDenied
    
    hospital_profile = get_object_or_404(HospitalProfile, user=request.user)
    
    import csv
    from django.http import HttpResponse
    from blood_requests.models import DonationConfirmation
    from datetime import datetime
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    blood_group_filter = request.GET.get('blood_group', '')
    
    # Get confirmations
    confirmations = DonationConfirmation.objects.filter(
        hospital=hospital_profile
    ).select_related('donor', 'donor__user').order_by('-donation_datetime')
    
    if status_filter:
        confirmations = confirmations.filter(status=status_filter)
    if blood_group_filter:
        confirmations = confirmations.filter(blood_group=blood_group_filter)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    filename = f'Donation_Confirmations_{hospital_profile.hospital_name.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'S.No',
        'Donation ID',
        'Donor ID',
        'Donor Name',
        'Blood Group',
        'Phone Number',
        'Email',
        'Address',
        'City',
        'District',
        'State',
        'Donation Date',
        'Donation Time',
        'Units Donated',
        'Blood Bag ID',
        'Staff Name',
        'Staff ID',
        'Status',
        'Notes',
    ])
    
    # Write data
    for idx, conf in enumerate(confirmations, 1):
        writer.writerow([
            idx,
            conf.donation_id,
            conf.donor.donor_id or 'N/A',
            conf.donor.full_name,
            conf.blood_group,
            conf.donor.phone_number,
            conf.donor.email,
            conf.donor.address or 'N/A',
            conf.donor.city or 'N/A',
            conf.donor.district or 'N/A',
            conf.donor.state or 'N/A',
            conf.donation_datetime.strftime('%d %b %Y'),
            conf.donation_datetime.strftime('%I:%M %p'),
            conf.units_donated,
            conf.blood_bag_id,
            conf.staff_name,
            conf.staff_id or 'N/A',
            conf.get_status_display(),
            conf.notes or 'N/A',
        ])
    
    return response


@login_required
def export_confirmations_pdf(request):
    """Export Donation Confirmations as PDF"""
    
    if not request.user.is_hospital():
        raise PermissionDenied
    
    hospital_profile = get_object_or_404(HospitalProfile, user=request.user)
    
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from blood_requests.models import DonationConfirmation
    from datetime import datetime
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    blood_group_filter = request.GET.get('blood_group', '')
    
    # Get confirmations
    confirmations = DonationConfirmation.objects.filter(
        hospital=hospital_profile
    ).select_related('donor', 'donor__user').order_by('-donation_datetime')
    
    if status_filter:
        confirmations = confirmations.filter(status=status_filter)
    if blood_group_filter:
        confirmations = confirmations.filter(blood_group=blood_group_filter)
    
    # Create PDF response
    response = HttpResponse(content_type='application/pdf')
    filename = f'Donation_Confirmations_{hospital_profile.hospital_name.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Create PDF document (landscape for more columns)
    doc = SimpleDocTemplate(response, pagesize=landscape(A4),
                            rightMargin=20, leftMargin=20,
                            topMargin=40, bottomMargin=30)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#dc3545'),
        alignment=TA_CENTER,
        spaceAfter=8
    )
    
    elements.append(Paragraph("RedFusion Blood Donor Network", title_style))
    elements.append(Paragraph("Donation Confirmations Report", title_style))
    elements.append(Spacer(1, 12))
    
    # Hospital Info
    hospital_info = f"<para align=center><b>Hospital:</b> {hospital_profile.hospital_name} | <b>Generated:</b> {datetime.now().strftime('%d %b %Y, %I:%M %p')}</para>"
    elements.append(Paragraph(hospital_info, styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Table data with ALL columns
    table_data = [[
        '#', 
        'Donation ID', 
        'Donor ID',
        'Donor Name', 
        'Blood\nGroup', 
        'Phone', 
        'City',
        'Date & Time', 
        'Units', 
        'Blood Bag ID',
        'Staff',
        'Status'
    ]]
    
    for idx, conf in enumerate(confirmations, 1):
        table_data.append([
            str(idx),
            conf.donation_id,
            conf.donor.donor_id or 'N/A',
            conf.donor.full_name[:20],  # Truncate long names
            conf.blood_group,
            conf.donor.phone_number,
            (conf.donor.city or 'N/A')[:15],
            conf.donation_datetime.strftime('%d %b %Y\n%I:%M %p'),
            str(conf.units_donated),
            conf.blood_bag_id,
            (conf.staff_name or 'N/A')[:15],
            conf.get_status_display()[:10],
        ])
    
    # Create table with adjusted column widths
    table = Table(table_data, colWidths=[
        0.3*inch,  # #
        0.9*inch,  # Donation ID
        0.85*inch, # Donor ID
        1.2*inch,  # Donor Name
        0.5*inch,  # Blood Group
        0.9*inch,  # Phone
        0.8*inch,  # City
        0.9*inch,  # Date & Time
        0.45*inch, # Units
        0.85*inch, # Blood Bag ID
        0.8*inch,  # Staff
        0.65*inch, # Status
    ])
    
    table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc3545')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        
        # Body
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (4, 1), (4, -1), 'CENTER'),
        ('ALIGN', (8, 1), (8, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 6.5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        
        # Alternating rows
        *[('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8f9fa')) for i in range(2, len(table_data), 2)]
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 15))
    
    # Footer
    footer = f"<para align=center><font size=7 color='grey'>Total Records: {len(confirmations)} | Generated on {datetime.now().strftime('%d %B %Y at %I:%M %p')}</font></para>"
    elements.append(Paragraph(footer, styles['Normal']))
    
    doc.build(elements)
    return response


@login_required
def download_donation_receipt(request, pk):
    """Download single donation receipt as PDF"""
    
    if not request.user.is_hospital():
        raise PermissionDenied
    
    hospital_profile = get_object_or_404(HospitalProfile, user=request.user)
    
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from blood_requests.models import DonationConfirmation
    from datetime import datetime
    
    # Get the specific confirmation
    confirmation = get_object_or_404(
        DonationConfirmation,
        pk=pk,
        hospital=hospital_profile
    )
    
    # Create PDF response
    response = HttpResponse(content_type='application/pdf')
    filename = f'Donation_Receipt_{confirmation.donation_id}_{confirmation.donor.full_name.replace(" ", "_")}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Create PDF document
    doc = SimpleDocTemplate(response, pagesize=A4,
                            rightMargin=50, leftMargin=50,
                            topMargin=50, bottomMargin=50)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#dc3545'),
        alignment=TA_CENTER,
        spaceAfter=10
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubTitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=colors.HexColor('#dc3545'),
        spaceAfter=10,
        spaceBefore=15
    )
    
    # Header
    elements.append(Paragraph("💓 RedFusion", title_style))
    elements.append(Paragraph("Blood Donor Network", subtitle_style))
    elements.append(Paragraph("Blood Donation Receipt", subtitle_style))
    elements.append(Spacer(1, 20))
    
    # Donation ID Box
    donation_id_data = [[f"Donation ID: {confirmation.donation_id}"]]
    donation_id_table = Table(donation_id_data, colWidths=[6*inch])
    donation_id_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#dc3545')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 16),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#dc3545')),
    ]))
    elements.append(donation_id_table)
    elements.append(Spacer(1, 25))
    
    # Hospital Information
    elements.append(Paragraph("Hospital Information", heading_style))
    hospital_data = [
        ['Hospital Name:', hospital_profile.hospital_name],
        ['Hospital Type:', hospital_profile.get_hospital_type_display()],
        ['Phone:', hospital_profile.phone_number],
        ['Email:', hospital_profile.email],
        ['Address:', f"{hospital_profile.city}, {hospital_profile.district}, {hospital_profile.state}"],
    ]
    
    hospital_table = Table(hospital_data, colWidths=[2*inch, 4*inch])
    hospital_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(hospital_table)
    elements.append(Spacer(1, 20))
    
    # Donor Information
    elements.append(Paragraph("Donor Information", heading_style))
    donor_data = [
        ['Donor ID:', confirmation.donor.donor_id or 'N/A'],
        ['Name:', confirmation.donor.full_name],
        ['Blood Group:', confirmation.blood_group],
        ['Phone:', confirmation.donor.phone_number],
        ['Email:', confirmation.donor.email],
        ['Address:', f"{confirmation.donor.address or 'N/A'}"],
        ['City:', f"{confirmation.donor.city}, {confirmation.donor.district}, {confirmation.donor.state}"],
        ['Total Donations:', str(confirmation.donor.total_donations)],
    ]
    
    donor_table = Table(donor_data, colWidths=[2*inch, 4*inch])
    donor_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(donor_table)
    elements.append(Spacer(1, 20))
    
    # Donation Details
    elements.append(Paragraph("Donation Details", heading_style))
    donation_data = [
        ['Donation Date:', confirmation.donation_datetime.strftime('%d %B %Y')],
        ['Donation Time:', confirmation.donation_datetime.strftime('%I:%M %p')],
        ['Blood Group:', confirmation.blood_group],
        ['Units Donated:', f"{confirmation.units_donated} unit(s)"],
        ['Blood Bag ID:', confirmation.blood_bag_id],
        ['Staff Name:', confirmation.staff_name],
        ['Staff ID:', confirmation.staff_id or 'N/A'],
        ['Status:', confirmation.get_status_display()],
    ]
    
    if confirmation.notes:
        donation_data.append(['Notes:', confirmation.notes])
    
    donation_table = Table(donation_data, colWidths=[2*inch, 4*inch])
    donation_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(donation_table)
    elements.append(Spacer(1, 30))
    
    # Thank You Message
    thank_you_style = ParagraphStyle(
        'ThankYou',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#28a745'),
        alignment=TA_CENTER,
        spaceAfter=10
    )
    elements.append(Paragraph("✓ Thank you for saving lives!", thank_you_style))
    elements.append(Spacer(1, 40))
    
    # Footer
    footer_text = f"<para align=center><font size=9 color='grey'>This is a computer-generated receipt from RedFusion Blood Donor Network.<br/>Generated on {datetime.now().strftime('%d %B %Y at %I:%M %p')}<br/><br/>For queries, contact: {hospital_profile.phone_number} | {hospital_profile.email}</font></para>"
    elements.append(Paragraph(footer_text, styles['Normal']))
    
    doc.build(elements)
    return response


@login_required
def export_donation_history_csv(request):
    """Export Donation History as CSV"""
    
    if not request.user.is_hospital():
        raise PermissionDenied
    
    hospital_profile = get_object_or_404(HospitalProfile, user=request.user)
    
    import csv
    from django.http import HttpResponse
    from blood_requests.models import DonorMatch
    from django.db.models import Q
    from datetime import datetime
    
    # Get filter parameters from query string
    blood_group_filter = request.GET.get('blood_group', '')
    donor_search = request.GET.get('donor_search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Get donations with same filters as view
    donations = DonorMatch.objects.filter(
        blood_request__hospital=hospital_profile,
        match_status='donated'
    ).select_related(
        'donor',
        'donor__user',
        'blood_request'
    ).order_by('-updated_at')
    
    if blood_group_filter:
        donations = donations.filter(donor__blood_group=blood_group_filter)
    
    if donor_search:
        donations = donations.filter(
            Q(donor__full_name__icontains=donor_search) |
            Q(donor__donor_id__icontains=donor_search)
        )
    
    if date_from:
        donations = donations.filter(updated_at__gte=date_from)
    
    if date_to:
        donations = donations.filter(updated_at__lte=date_to)
    
    # Create HTTP response with CSV headers
    response = HttpResponse(content_type='text/csv')
    filename = f'Donation_History_{hospital_profile.hospital_name.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Create CSV writer
    writer = csv.writer(response)
    
    # Write header row
    writer.writerow([
        'S.No',
        'Donor ID',
        'Donor Name',
        'Blood Group',
        'Age',
        'Gender',
        'Phone Number',
        'Email',
        'Address',
        'City',
        'District',
        'State',
        'Pincode',
        'Request ID',
        'Donation Date',
        'Donation Time',
        'Total Donations by Donor',
        'Last Donation Date',
    ])
    
    # Write data rows
    for idx, donation in enumerate(donations, 1):
        writer.writerow([
            idx,
            donation.donor.donor_id or 'N/A',
            donation.donor.full_name,
            donation.donor.blood_group,
            donation.donor.age or 'N/A',
            donation.donor.get_gender_display(),
            donation.donor.phone_number,
            donation.donor.email,
            donation.donor.address or 'N/A',
            donation.donor.city or 'N/A',
            donation.donor.district or 'N/A',
            donation.donor.state or 'N/A',
            donation.donor.pincode or 'N/A',
            donation.blood_request.request_id,
            donation.updated_at.strftime('%d %b %Y'),
            donation.updated_at.strftime('%I:%M %p'),
            donation.donor.total_donations,
            donation.donor.last_donation_date.strftime('%d %b %Y') if donation.donor.last_donation_date else 'N/A',
        ])
    
    return response
