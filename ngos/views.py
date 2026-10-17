"""
NGO Views - Blood Request Management and Donor Coordination
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponse
from accounts.models import User
from .models import NGOProfile
from .forms import NGORegistrationForm, NGOProfileForm, BloodCampForm
from blood_requests.models import BloodRequest
from donors.models import DonorProfile
from camps.models import BloodCamp
from core.models import Notification
import csv
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER

def ngo_register(request):
    """NGO Registration"""
    if request.user.is_authenticated:
        return redirect('ngos:dashboard')
    
    if request.method == 'POST':
        user_form = NGORegistrationForm(request.POST)
        profile_form = NGOProfileForm(request.POST, request.FILES)
        
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            ngo_profile = profile_form.save(commit=False)
            ngo_profile.user = user
            ngo_profile.ngo_name = user_form.cleaned_data['ngo_name']
            ngo_profile.email = user_form.cleaned_data['email']
            ngo_profile.phone_number = user_form.cleaned_data['phone_number']
            ngo_profile.save()
            
            messages.success(request, 'NGO registration successful. Please login to continue.')
            return redirect('ngos:login')
    else:
        user_form = NGORegistrationForm()
        profile_form = NGOProfileForm()
    
    return render(request, 'auth/ngo_register.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

def ngo_login(request):
    """NGO Login"""
    if request.user.is_authenticated:
        return redirect('ngos:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Block admin users from logging in here
            if user.is_staff or user.is_superuser:
                messages.error(request, 'Admin users should login through admin panel at /admin/')
                return render(request, 'auth/ngo_login.html')
            
            if user.role == User.Role.NGO:
                login(request, user)
                return redirect('ngos:dashboard')
            else:
                messages.error(request, 'Invalid credentials for NGO login.')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'auth/ngo_login.html')

def ngo_logout(request):
    """NGO Logout"""
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
    return redirect('core:home')

@login_required
def ngo_dashboard(request):
    """NGO Dashboard"""
    
    # Block admin users
    if request.user.is_staff or request.user.is_superuser:
        messages.warning(request, 'Admin users should use the admin panel.')
        logout(request)
        return redirect('/admin/')
    
    if not request.user.is_ngo():
        raise PermissionDenied
    
    ngo_profile = get_object_or_404(NGOProfile, user=request.user)
    
    # Statistics
    total_requests = BloodRequest.objects.filter(assigned_ngo=ngo_profile).count()
    pending_requests = BloodRequest.objects.filter(assigned_ngo=ngo_profile, status='pending').count()
    active_donors = DonorProfile.objects.filter(is_active=True, is_available=True).count()
    total_camps = BloodCamp.objects.filter(organized_by=ngo_profile).count()
    
    # Recent requests
    recent_requests = BloodRequest.objects.filter(assigned_ngo=ngo_profile).order_by('-created_at')[:5]
    
    unread_notifications_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    
    return render(request, 'ngo/dashboard.html', {
        'ngo_profile': ngo_profile,
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'active_donors': active_donors,
        'total_camps': total_camps,
        'recent_requests': recent_requests,
        'unread_notifications_count': unread_notifications_count,
    })

@login_required
def ngo_profile(request):
    """View NGO Profile"""
    if not request.user.is_ngo():
        raise PermissionDenied
    ngo_profile = get_object_or_404(NGOProfile, user=request.user)
    return render(request, 'ngo/profile.html', {'ngo_profile': ngo_profile})


@login_required
def edit_ngo_profile(request):
    """Edit NGO Profile"""
    if not request.user.is_ngo():
        raise PermissionDenied
    
    ngo_profile = get_object_or_404(NGOProfile, user=request.user)
    
    if request.method == 'POST':
        form = NGOProfileForm(request.POST, request.FILES, instance=ngo_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'NGO profile updated successfully!')
            return redirect('ngos:profile')
    else:
        form = NGOProfileForm(instance=ngo_profile)
    
    context = {
        'form': form,
        'ngo_profile': ngo_profile
    }
    return render(request, 'ngo/edit_profile.html', context)

@login_required
def blood_requests_list(request):
    """List Blood Requests Assigned to NGO"""
    if not request.user.is_ngo():
        raise PermissionDenied
    
    ngo_profile = get_object_or_404(NGOProfile, user=request.user)
    requests = BloodRequest.objects.filter(assigned_ngo=ngo_profile).order_by('-created_at')
    
    return render(request, 'ngo/blood_requests_list.html', {'ngo_profile': ngo_profile, 'requests': requests})

@login_required
def blood_request_detail(request, pk):
    """View Blood Request Detail"""
    if not request.user.is_ngo():
        raise PermissionDenied
    
    ngo_profile = get_object_or_404(NGOProfile, user=request.user)
    blood_request = get_object_or_404(BloodRequest, pk=pk, assigned_ngo=ngo_profile)
    matched_donors = blood_request.matched_donors.all()
    
    return render(request, 'ngo/blood_request_detail.html', {
        'ngo_profile': ngo_profile,
        'blood_request': blood_request,
        'matched_donors': matched_donors
    })

@login_required
def accept_request(request, pk):
    """Accept Blood Request"""
    if not request.user.is_ngo():
        raise PermissionDenied
    
    ngo_profile = get_object_or_404(NGOProfile, user=request.user)
    blood_request = get_object_or_404(BloodRequest, pk=pk, assigned_ngo=ngo_profile)
    
    if blood_request.status == 'pending':
        blood_request.status = 'accepted'
        blood_request.save()
        messages.success(request, f'Blood request {blood_request.request_id} accepted successfully.')
    
    return redirect('ngos:blood_request_detail', pk=pk)

@login_required
def update_request_status(request, pk):
    """Update Blood Request Status"""
    if not request.user.is_ngo():
        raise PermissionDenied
    
    ngo_profile = get_object_or_404(NGOProfile, user=request.user)
    blood_request = get_object_or_404(BloodRequest, pk=pk, assigned_ngo=ngo_profile)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        units_fulfilled = request.POST.get('units_fulfilled')
        
        if new_status:
            blood_request.status = new_status
        if units_fulfilled:
            blood_request.units_fulfilled = units_fulfilled
        
        blood_request.save()
        messages.success(request, 'Request status updated successfully.')
    
    return redirect('ngos:blood_request_detail', pk=pk)

@login_required
def donor_management(request):
    """Donor Management - Search and Filter - Show ALL Donors"""
    if not request.user.is_ngo():
        raise PermissionDenied
    
    ngo_profile = get_object_or_404(NGOProfile, user=request.user)
    
    # Get ALL donors - Remove profile_completed filter temporarily for debugging
    donors = DonorProfile.objects.filter(
        is_active=True
    ).order_by('-created_at')  # Latest first
    
    # Filters
    blood_group = request.GET.get('blood_group', '')
    district = request.GET.get('district', '')
    is_available = request.GET.get('is_available', '')
    
    if blood_group and blood_group != '':
        donors = donors.filter(blood_group=blood_group)
    if district and district != '':
        donors = donors.filter(district__icontains=district)
    if is_available and is_available == '1':
        donors = donors.filter(is_available=True)
    
    # Get statistics - show all active donors
    total_donors = DonorProfile.objects.filter(is_active=True).count()
    available_donors = DonorProfile.objects.filter(is_active=True, is_available=True).count()
    
    return render(request, 'ngo/donor_management.html', {
        'ngo_profile': ngo_profile,
        'donors': donors,
        'total_donors': total_donors,
        'available_donors': available_donors,
        'blood_group_filter': blood_group,
        'district_filter': district,
        'is_available_filter': is_available,
    })

@login_required
def donor_detail(request, pk):
    """View Donor Detail"""
    if not request.user.is_ngo():
        raise PermissionDenied
    
    ngo_profile = get_object_or_404(NGOProfile, user=request.user)
    donor = get_object_or_404(DonorProfile, pk=pk)
    
    return render(request, 'ngo/donor_detail.html', {
        'ngo_profile': ngo_profile,
        'donor': donor
    })

@login_required
def camps_list(request):
    """List Blood Camps Organized by NGO"""
    if not request.user.is_ngo():
        raise PermissionDenied
    
    ngo_profile = get_object_or_404(NGOProfile, user=request.user)
    camps = BloodCamp.objects.filter(organized_by=ngo_profile).order_by('-camp_date')
    
    return render(request, 'ngo/camps_list.html', {'ngo_profile': ngo_profile, 'camps': camps})

@login_required
def create_camp(request):
    """Create Blood Camp"""
    if not request.user.is_ngo():
        raise PermissionDenied
    
    ngo_profile = get_object_or_404(NGOProfile, user=request.user)
    
    if request.method == 'POST':
        form = BloodCampForm(request.POST, request.FILES)
        if form.is_valid():
            camp = form.save(commit=False)
            camp.organized_by = ngo_profile
            camp.save()
            messages.success(request, 'Blood camp created successfully.')
            return redirect('ngos:camps_list')
    else:
        form = BloodCampForm()
    
    return render(request, 'ngo/create_camp.html', {'form': form, 'ngo_profile': ngo_profile})

@login_required
def camp_detail(request, pk):
    """View Camp Detail with Registered Donors"""
    if not request.user.is_ngo():
        raise PermissionDenied
    
    ngo_profile = get_object_or_404(NGOProfile, user=request.user)
    camp = get_object_or_404(BloodCamp, pk=pk, organized_by=ngo_profile)
    
    # Get all registered donors for this camp
    from camps.models import CampRegistration
    registrations = CampRegistration.objects.filter(
        camp=camp
    ).select_related('donor').order_by('-registration_date')
    
    return render(request, 'ngo/camp_detail.html', {
        'ngo_profile': ngo_profile,
        'camp': camp,
        'registrations': registrations,
        'total_registrations': registrations.count(),
    })

@login_required
def edit_camp(request, pk):
    """Edit Blood Camp"""
    if not request.user.is_ngo():
        raise PermissionDenied
    
    ngo_profile = get_object_or_404(NGOProfile, user=request.user)
    camp = get_object_or_404(BloodCamp, pk=pk, organized_by=ngo_profile)
    
    if request.method == 'POST':
        form = BloodCampForm(request.POST, request.FILES, instance=camp)
        if form.is_valid():
            form.save()
            messages.success(request, 'Camp updated successfully.')
            return redirect('ngos:camp_detail', pk=pk)
    else:
        form = BloodCampForm(instance=camp)
    
    return render(request, 'ngo/edit_camp.html', {'form': form, 'ngo_profile': ngo_profile, 'camp': camp})

@login_required
def notifications(request):
    """View Notifications"""
    if not request.user.is_ngo():
        raise PermissionDenied
    
    notifications_list = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    notifications_list.filter(is_read=False).update(is_read=True)
    
    return render(request, 'ngo/notifications.html', {'notifications': notifications_list})

@login_required
def export_donors_csv(request):
    """Export Donors List to CSV with ALL details"""
    if not request.user.is_ngo():
        raise PermissionDenied
    
    # Get filtered donors (same logic as donor_management view)
    donors = DonorProfile.objects.filter(is_active=True).order_by('-created_at')
    
    # Apply same filters
    blood_group = request.GET.get('blood_group', '')
    district = request.GET.get('district', '')
    is_available = request.GET.get('is_available', '')
    
    if blood_group:
        donors = donors.filter(blood_group=blood_group)
    if district:
        donors = donors.filter(district__icontains=district)
    if is_available == '1':
        donors = donors.filter(is_available=True)
    
    # Create CSV response
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="Donors_List_{timestamp}.csv"'
    
    writer = csv.writer(response)
    
    # Write header with ALL fields (18 columns)
    writer.writerow([
        'S.No', 'Donor ID', 'Full Name', 'Blood Group', 'Age', 'Gender',
        'Phone', 'Email', 'Address', 'City', 'District', 'State', 'Pincode',
        'Last Donation Date', 'Total Donations', 'Profile Status', 'Availability', 'Registered On'
    ])
    
    # Write data rows
    for idx, donor in enumerate(donors, start=1):
        writer.writerow([
            idx,
            donor.donor_id or 'N/A',
            donor.full_name or 'N/A',
            donor.blood_group or 'N/A',
            donor.age or 0,
            donor.get_gender_display() if donor.gender else 'N/A',
            donor.phone_number or 'N/A',
            donor.email or 'N/A',
            donor.address or 'N/A',
            donor.city or 'N/A',
            donor.district or 'N/A',
            donor.state or 'N/A',
            donor.pincode or 'N/A',
            donor.last_donation_date.strftime('%Y-%m-%d') if donor.last_donation_date else 'Never',
            donor.total_donations,
            'Complete' if donor.profile_completed else 'Incomplete',
            'Available' if donor.is_available else 'Not Available',
            donor.created_at.strftime('%Y-%m-%d %H:%M') if donor.created_at else 'N/A'
        ])
    
    return response

@login_required
def export_donors_pdf(request):
    """Export Donors List to PDF (Landscape, 12 columns)"""
    if not request.user.is_ngo():
        raise PermissionDenied
    
    # Get filtered donors
    donors = DonorProfile.objects.filter(is_active=True).order_by('-created_at')
    
    # Apply filters
    blood_group = request.GET.get('blood_group', '')
    district = request.GET.get('district', '')
    is_available = request.GET.get('is_available', '')
    
    if blood_group:
        donors = donors.filter(blood_group=blood_group)
    if district:
        donors = donors.filter(district__icontains=district)
    if is_available == '1':
        donors = donors.filter(is_available=True)
    
    # Create PDF
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Donors_List_{timestamp}.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=landscape(A4), topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#dc3545'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    elements.append(Paragraph('RedFusion Blood Donor Network - Donors List', title_style))
    elements.append(Paragraph(f'Generated on: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}', styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Table data (12 columns for landscape PDF)
    table_data = [[
        '#', 'Donor ID', 'Name', 'Blood', 'Age', 'Gender',
        'Phone', 'City', 'District', 'Last Donation', 'Total', 'Status'
    ]]
    
    for idx, donor in enumerate(donors, start=1):
        table_data.append([
            str(idx),
            donor.donor_id or 'N/A',
            donor.full_name or 'N/A',
            donor.blood_group or 'N/A',
            str(donor.age or 0),
            donor.get_gender_display()[:1] if donor.gender else 'N/A',
            donor.phone_number or 'N/A',
            donor.city or 'N/A',
            donor.district or 'N/A',
            donor.last_donation_date.strftime('%Y-%m-%d') if donor.last_donation_date else 'Never',
            str(donor.total_donations),
            'Avail' if donor.is_available else 'N/A'
        ])
    
    # Create table with optimized column widths for landscape
    table = Table(table_data, colWidths=[
        0.3*inch,  # #
        0.8*inch,  # Donor ID
        1.2*inch,  # Name
        0.5*inch,  # Blood
        0.4*inch,  # Age
        0.5*inch,  # Gender
        0.9*inch,  # Phone
        0.8*inch,  # City
        0.9*inch,  # District
        0.9*inch,  # Last Donation
        0.4*inch,  # Total
        0.5*inch   # Status
    ])
    
    # Table styling
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc3545')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('FONTSIZE', (0, 1), (-1, -1), 6.5),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    return response

@login_required
def download_donor_receipt(request, pk):
    """Download Individual Donor Details as PDF Receipt"""
    if not request.user.is_ngo():
        raise PermissionDenied
    
    donor = get_object_or_404(DonorProfile, pk=pk)
    ngo_profile = get_object_or_404(NGOProfile, user=request.user)
    
    # Create PDF
    response = HttpResponse(content_type='application/pdf')
    filename = f'Donor_Details_{donor.donor_id or donor.pk}_{donor.full_name.replace(" ", "_")}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    doc = SimpleDocTemplate(response, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#dc3545'),
        spaceAfter=10,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#dc3545'),
        spaceAfter=10,
        spaceBefore=15,
        fontName='Helvetica-Bold'
    )
    
    # Header
    elements.append(Paragraph('RedFusion Blood Donor Network', title_style))
    elements.append(Paragraph('Donor Information Report', styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Donor ID Box
    donor_id_data = [[f"Donor ID: {donor.donor_id or 'N/A'}"]]
    donor_id_table = Table(donor_id_data, colWidths=[5*inch])
    donor_id_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#dc3545')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(donor_id_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Personal Information Section
    elements.append(Paragraph('1. Personal Information', header_style))
    personal_data = [
        ['Full Name:', donor.full_name or 'N/A'],
        ['Blood Group:', donor.blood_group or 'N/A'],
        ['Age:', f"{donor.age or 0} years"],
        ['Gender:', donor.get_gender_display() if donor.gender else 'N/A'],
        ['Date of Birth:', donor.date_of_birth.strftime('%B %d, %Y') if donor.date_of_birth else 'N/A'],
    ]
    personal_table = Table(personal_data, colWidths=[2*inch, 4*inch])
    personal_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(personal_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Contact Information Section
    elements.append(Paragraph('2. Contact Information', header_style))
    contact_data = [
        ['Phone Number:', donor.phone_number or 'N/A'],
        ['Email Address:', donor.email or 'N/A'],
        ['Address:', donor.address or 'N/A'],
        ['City:', donor.city or 'N/A'],
        ['District:', donor.district or 'N/A'],
        ['State:', donor.state or 'N/A'],
        ['Pincode:', donor.pincode or 'N/A'],
    ]
    contact_table = Table(contact_data, colWidths=[2*inch, 4*inch])
    contact_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(contact_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Donation History Section
    elements.append(Paragraph('3. Donation History', header_style))
    donation_data = [
        ['Last Donation Date:', donor.last_donation_date.strftime('%B %d, %Y') if donor.last_donation_date else 'Never donated'],
        ['Total Donations:', str(donor.total_donations)],
        ['Current Availability:', 'Available' if donor.is_available else 'Not Available'],
        ['Profile Status:', 'Complete' if donor.profile_completed else 'Incomplete'],
    ]
    donation_table = Table(donation_data, colWidths=[2*inch, 4*inch])
    donation_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(donation_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Footer
    elements.append(Spacer(1, 0.3*inch))
    footer_text = f"""
    <para align=center>
    <b>Thank you for your commitment to saving lives!</b><br/>
    Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br/>
    Requested by: {ngo_profile.ngo_name}<br/>
    Contact: redfusion@blooddonor.org | Phone: +91-XXXX-XXXXXX
    </para>
    """
    elements.append(Paragraph(footer_text, styles['Normal']))
    
    doc.build(elements)
    return response

@login_required
def export_blood_requests_csv(request):
    """Export NGO Blood Requests to CSV with ALL details"""
    if not request.user.is_ngo():
        raise PermissionDenied
    
    ngo_profile = get_object_or_404(NGOProfile, user=request.user)
    requests = BloodRequest.objects.filter(assigned_ngo=ngo_profile).order_by('-created_at')
    
    # Create CSV response
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="Blood_Requests_{timestamp}.csv"'
    
    writer = csv.writer(response)
    
    # Write header with ALL fields (16 columns)
    writer.writerow([
        'S.No', 'Request ID', 'Hospital Name', 'Blood Group', 'Units Required', 'Units Fulfilled',
        'Urgency', 'Required Date', 'Contact Person', 'Contact Number', 
        'Patient Name', 'Patient Age', 'Reason', 'Status', 'Created On', 'Updated On'
    ])
    
    # Write data rows
    for idx, req in enumerate(requests, start=1):
        writer.writerow([
            idx,
            req.request_id,
            req.hospital.hospital_name,
            req.blood_group,
            req.units_required,
            req.units_fulfilled,
            req.get_urgency_display(),
            req.required_date.strftime('%Y-%m-%d'),
            req.contact_person or 'N/A',
            req.contact_number or 'N/A',
            req.patient_name or 'N/A',
            req.patient_age or 0,
            req.reason or 'N/A',
            req.get_status_display(),
            req.created_at.strftime('%Y-%m-%d %H:%M'),
            req.updated_at.strftime('%Y-%m-%d %H:%M')
        ])
    
    return response

@login_required
def export_blood_requests_pdf(request):
    """Export NGO Blood Requests to PDF (Landscape, 10 columns)"""
    if not request.user.is_ngo():
        raise PermissionDenied
    
    ngo_profile = get_object_or_404(NGOProfile, user=request.user)
    requests = BloodRequest.objects.filter(assigned_ngo=ngo_profile).order_by('-created_at')
    
    # Create PDF
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Blood_Requests_{timestamp}.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=landscape(A4), topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#dc3545'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    elements.append(Paragraph('RedFusion Blood Donor Network - Blood Requests', title_style))
    elements.append(Paragraph(f'NGO: {ngo_profile.ngo_name}', styles['Normal']))
    elements.append(Paragraph(f'Generated on: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}', styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Table data (10 columns for landscape PDF)
    table_data = [[
        '#', 'Request ID', 'Hospital', 'Blood', 'Units', 'Urgency',
        'Required By', 'Contact', 'Status', 'Created'
    ]]
    
    for idx, req in enumerate(requests, start=1):
        table_data.append([
            str(idx),
            req.request_id,
            req.hospital.hospital_name[:15] + '...' if len(req.hospital.hospital_name) > 15 else req.hospital.hospital_name,
            req.blood_group,
            f"{req.units_fulfilled}/{req.units_required}",
            req.get_urgency_display()[:4],
            req.required_date.strftime('%Y-%m-%d'),
            req.contact_number or 'N/A',
            req.get_status_display()[:8],
            req.created_at.strftime('%Y-%m-%d')
        ])
    
    # Create table with optimized column widths for landscape
    table = Table(table_data, colWidths=[
        0.3*inch,  # #
        0.9*inch,  # Request ID
        1.3*inch,  # Hospital
        0.5*inch,  # Blood
        0.6*inch,  # Units
        0.6*inch,  # Urgency
        0.9*inch,  # Required By
        0.9*inch,  # Contact
        0.7*inch,  # Status
        0.8*inch   # Created
    ])
    
    # Table styling
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc3545')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('FONTSIZE', (0, 1), (-1, -1), 6.5),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    return response
