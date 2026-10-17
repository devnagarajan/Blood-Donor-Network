from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import BloodCamp, CampRegistration
from donors.models import DonorProfile
from datetime import date

def camps_list(request):
    """Public Blood Camps List"""
    camps = BloodCamp.objects.filter(
        status='upcoming',
        camp_date__gte=date.today()
    ).order_by('camp_date')
    
    return render(request, 'camps/camps_list.html', {'camps': camps})

def camp_detail(request, pk):
    """Camp Detail Page"""
    camp = get_object_or_404(BloodCamp, pk=pk)
    
    # Check if user is donor and already registered
    is_registered = False
    if request.user.is_authenticated and hasattr(request.user, 'donor_profile'):
        is_registered = CampRegistration.objects.filter(
            camp=camp,
            donor=request.user.donor_profile
        ).exists()
    
    return render(request, 'camps/camp_detail.html', {
        'camp': camp,
        'is_registered': is_registered
    })

@login_required
def register_for_camp(request, pk):
    """Register Donor for Camp"""
    camp = get_object_or_404(BloodCamp, pk=pk)
    
    if not hasattr(request.user, 'donor_profile'):
        messages.error(request, 'Only donors can register for camps.')
        return redirect('camps:camp_detail', pk=pk)
    
    donor_profile = request.user.donor_profile
    
    # Check if already registered
    if CampRegistration.objects.filter(camp=camp, donor=donor_profile).exists():
        messages.warning(request, 'You are already registered for this camp.')
        return redirect('camps:camp_detail', pk=pk)
    
    # Check if camp is full
    if camp.is_full():
        messages.error(request, 'This camp is full.')
        return redirect('camps:camp_detail', pk=pk)
    
    # Check if registration is open
    if not camp.can_register():
        messages.error(request, 'Registration is not open for this camp.')
        return redirect('camps:camp_detail', pk=pk)
    
    # Create registration
    registration = CampRegistration.objects.create(camp=camp, donor=donor_profile)
    camp.registered_count += 1
    camp.save()
    
    # Send email notification to NGO
    from blood_requests.services import CampNotificationService
    CampNotificationService.notify_ngo_donor_registered(camp, donor_profile, registration)
    
    messages.success(request, 'Successfully registered for the camp! NGO has been notified.')
    return redirect('camps:camp_detail', pk=pk)

@login_required
def my_registrations(request):
    """View Donor's Camp Registrations"""
    if not hasattr(request.user, 'donor_profile'):
        messages.error(request, 'Only donors can view registrations.')
        return redirect('core:home')
    
    donor_profile = request.user.donor_profile
    registrations = CampRegistration.objects.filter(
        donor=donor_profile
    ).select_related('camp').order_by('-registration_date')
    
    return render(request, 'camps/my_registrations.html', {
        'registrations': registrations
    })
