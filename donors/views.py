from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.cache import cache
from accounts.models import User
from .models import DonorProfile, DonationHistory
from .forms import DonorRegistrationForm, DonorProfileForm
from blood_requests.models import BloodRequest, DonorMatch
from core.models import Notification

def donor_register(request):
    """Donor Registration"""
    
    if request.user.is_authenticated:
        return redirect('donors:dashboard')
    
    if request.method == 'POST':
        form = DonorRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                'Donor registration successful. Please login to continue.'
            )
            return redirect('donors:login')
    else:
        form = DonorRegistrationForm()
    
    context = {'form': form}
    return render(request, 'auth/donor_register.html', context)


def donor_login(request):
    """Donor Login"""
    
    if request.user.is_authenticated:
        return redirect('donors:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Block admin users from logging in here
            if user.is_staff or user.is_superuser:
                messages.error(request, 'Admin users should login through admin panel at /admin/')
                return render(request, 'auth/donor_login.html')
            
            if user.role == User.Role.DONOR:
                login(request, user)
                
                # Check if profile is completed
                try:
                    donor_profile = user.donor_profile
                    if donor_profile.profile_completed:
                        return redirect('donors:dashboard')
                    else:
                        return redirect('donors:become_donor')
                except DonorProfile.DoesNotExist:
                    return redirect('donors:become_donor')
            else:
                messages.error(request, 'Invalid credentials for donor login.')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'auth/donor_login.html')


def donor_logout(request):
    """Donor Logout"""
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
    return redirect('core:home')


@login_required
def become_donor(request):
    """Complete Donor Profile (First Time)"""
    
    # Check if user is donor
    if not request.user.is_donor():
        raise PermissionDenied
    
    # Check if profile already exists
    try:
        donor_profile = request.user.donor_profile
        if donor_profile.profile_completed:
            return redirect('donors:dashboard')
    except DonorProfile.DoesNotExist:
        donor_profile = None
    
    if request.method == 'POST':
        if donor_profile:
            form = DonorProfileForm(request.POST, instance=donor_profile)
        else:
            form = DonorProfileForm(request.POST)
        
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.profile_completed = True
            profile.save()
            
            # Clear homepage cache to update donor statistics immediately
            from django.core.cache import cache
            cache.delete('blood_group_stats')
            cache.delete('home_stats')
            
            # Send email notification to all NGOs about new donor
            from blood_requests.services import EmailService
            EmailService.send_donor_registration_to_ngo(profile)
            
            messages.success(
                request,
                'Donor profile completed successfully! NGOs have been notified. Welcome to RedFusion!'
            )
            return redirect('donors:dashboard')
    else:
        if donor_profile:
            form = DonorProfileForm(instance=donor_profile)
        else:
            # Pre-fill form with user data
            initial_data = {
                'email': request.user.email,
                'phone_number': request.user.phone_number,
                'full_name': request.user.first_name,
            }
            form = DonorProfileForm(initial=initial_data)
    
    context = {'form': form}
    return render(request, 'donor/become_donor.html', context)


@login_required
def donor_dashboard(request):
    """Donor Dashboard - Optimized"""
    
    # Block admin users
    if request.user.is_staff or request.user.is_superuser:
        messages.warning(request, 'Admin users should use the admin panel.')
        logout(request)
        return redirect('/admin/')
    
    # Check if user is donor
    if not request.user.is_donor():
        raise PermissionDenied
    
    # Check if profile is completed
    try:
        donor_profile = request.user.donor_profile
        if not donor_profile.profile_completed:
            return redirect('donors:become_donor')
    except DonorProfile.DoesNotExist:
        return redirect('donors:become_donor')
    
    # Get statistics
    total_donations = donor_profile.total_donations
    is_eligible = donor_profile.is_eligible_to_donate()
    next_eligible = donor_profile.next_eligible_date()
    
    # Get recent blood requests - OPTIMIZED with select_related
    recent_requests = DonorMatch.objects.filter(
        donor=donor_profile
    ).select_related(
        'blood_request__hospital',
        'blood_request__assigned_ngo'
    ).order_by('-notified_at')[:5]
    
    # Get unread notifications count (cached)
    cache_key = f'unread_notif_count_{request.user.id}'
    unread_notifications_count = cache.get(cache_key)
    if unread_notifications_count is None:
        unread_notifications_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        cache.set(cache_key, unread_notifications_count, 60)  # Cache for 1 minute
    
    # Calculate card validity (1 year from now)
    from datetime import date, timedelta
    next_year = date.today() + timedelta(days=365)
    
    context = {
        'donor_profile': donor_profile,
        'total_donations': total_donations,
        'is_eligible': is_eligible,
        'next_eligible': next_eligible,
        'recent_requests': recent_requests,
        'unread_notifications_count': unread_notifications_count,
        'next_year': next_year,
    }
    
    return render(request, 'donor/dashboard.html', context)


@login_required
def donor_profile(request):
    """View Donor Profile"""
    
    if not request.user.is_donor():
        raise PermissionDenied
    
    donor_profile = get_object_or_404(DonorProfile, user=request.user)
    
    context = {'donor_profile': donor_profile}
    return render(request, 'donor/profile.html', context)


@login_required
def edit_profile(request):
    """Edit Donor Profile"""
    
    if not request.user.is_donor():
        raise PermissionDenied
    
    donor_profile = get_object_or_404(DonorProfile, user=request.user)
    
    if request.method == 'POST':
        form = DonorProfileForm(request.POST, instance=donor_profile)
        if form.is_valid():
            form.save()
            
            # Clear homepage cache to update donor statistics immediately
            from django.core.cache import cache
            cache.delete('blood_group_stats')
            cache.delete('home_stats')
            
            messages.success(request, 'Profile updated successfully.')
            return redirect('donors:profile')
    else:
        form = DonorProfileForm(instance=donor_profile)
    
    context = {'form': form, 'donor_profile': donor_profile}
    return render(request, 'donor/edit_profile.html', context)


@login_required
def donation_history(request):
    """Donation History"""
    
    if not request.user.is_donor():
        raise PermissionDenied
    
    donor_profile = get_object_or_404(DonorProfile, user=request.user)
    
    # Get regular donation history
    donations = DonationHistory.objects.filter(donor=donor_profile).order_by('-donation_date')
    
    # Get donation confirmations (with hospital details)
    from blood_requests.models import DonationConfirmation
    confirmed_donations = DonationConfirmation.objects.filter(
        donor=donor_profile,
        status='completed'
    ).select_related('hospital').order_by('-donation_datetime')
    
    context = {
        'donor_profile': donor_profile,
        'donations': donations,
        'confirmed_donations': confirmed_donations,
    }
    return render(request, 'donor/donation_history.html', context)


@login_required
def blood_requests(request):
    """View Blood Requests Received"""
    
    if not request.user.is_donor():
        raise PermissionDenied
    
    donor_profile = get_object_or_404(DonorProfile, user=request.user)
    
    # Get all blood requests matched to this donor
    requests = DonorMatch.objects.filter(
        donor=donor_profile
    ).select_related('blood_request__hospital').order_by('-notified_at')
    
    context = {
        'donor_profile': donor_profile,
        'requests': requests
    }
    return render(request, 'donor/blood_requests.html', context)


@login_required
def notifications(request):
    """View Notifications"""
    
    if not request.user.is_donor():
        raise PermissionDenied
    
    notifications_list = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')
    
    # Mark all as read when viewed
    notifications_list.filter(is_read=False).update(is_read=True)
    
    context = {'notifications': notifications_list}
    return render(request, 'donor/notifications.html', context)


def donor_card_view(request, donor_id):
    """Public view of donor card - accessible via QR code scan"""
    
    try:
        donor_profile = DonorProfile.objects.get(user__id=donor_id, is_active=True)
    except DonorProfile.DoesNotExist:
        messages.error(request, f'Donor ID {donor_id} not found or inactive.')
        return redirect('core:home')
    
    # Calculate valid till date (1 year from today)
    from datetime import date, timedelta
    valid_till = date.today() + timedelta(days=365)
    
    context = {
        'donor_profile': donor_profile,
        'valid_till': valid_till,
    }
    return render(request, 'donor/donor_card_view.html', context)
