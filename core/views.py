from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Count
from django.core.cache import cache
from accounts.models import User
from donors.models import DonorProfile
from hospitals.models import HospitalProfile
from ngos.models import NGOProfile
from blood_requests.models import BloodRequest
from camps.models import BloodCamp
from .forms import ContactForm
from .models import ContactMessage
from datetime import date

def home(request):
    """Home Page with Statistics - Optimized with caching"""
    
    # Try to get stats from cache (cached for 30 seconds for real-time updates)
    stats = cache.get('home_stats')
    if stats is None:
        stats = {
            'total_donors': DonorProfile.objects.filter(is_active=True).count(),
            'total_hospitals': HospitalProfile.objects.filter(is_active=True).count(),
            'total_ngos': NGOProfile.objects.filter(is_active=True).count(),
            'total_requests_fulfilled': BloodRequest.objects.filter(status='fulfilled').count(),
        }
        cache.set('home_stats', stats, 30)  # Cache for 30 seconds
    
    # Get upcoming blood camps (cached for 1 minute)
    upcoming_camps = cache.get('upcoming_camps')
    if upcoming_camps is None:
        upcoming_camps = BloodCamp.objects.filter(
            status='upcoming',
            camp_date__gte=date.today()
        ).select_related('organized_by').order_by('camp_date')[:3]
        cache.set('upcoming_camps', list(upcoming_camps), 60)  # Cache for 1 minute
    
    # Blood group statistics (cached for 30 seconds for real-time updates)
    blood_group_stats = cache.get('blood_group_stats')
    if blood_group_stats is None:
        blood_group_stats = list(DonorProfile.objects.filter(
            is_active=True,
            is_available=True
        ).values('blood_group').annotate(
            count=Count('id')
        ).order_by('blood_group'))
        cache.set('blood_group_stats', blood_group_stats, 30)  # Cache for 30 seconds
    
    context = {
        'stats': stats,
        'upcoming_camps': upcoming_camps,
        'blood_group_stats': blood_group_stats,
    }
    
    return render(request, 'core/home.html', context)


def about(request):
    """About Page"""
    return render(request, 'core/about.html')


def contact(request):
    """Contact Page"""
    
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thank you for contacting us. We will get back to you soon.')
            return redirect('core:contact')
    else:
        form = ContactForm()
    
    context = {'form': form}
    return render(request, 'core/contact.html', context)


def blood_camps_public(request):
    """Public Blood Camps Page"""
    
    # Filter upcoming camps
    camps = BloodCamp.objects.filter(
        status='upcoming',
        camp_date__gte=date.today()
    ).order_by('camp_date')
    
    # Get filter parameters
    state = request.GET.get('state', '')
    district = request.GET.get('district', '')
    
    if state:
        camps = camps.filter(state__icontains=state)
    if district:
        camps = camps.filter(district__icontains=district)
    
    context = {'camps': camps}
    return render(request, 'core/blood_camps.html', context)


def login_redirect(request):
    """Redirect to appropriate login page based on user type"""
    return render(request, 'auth/login_redirect.html')


def article_save_lives(request):
    """Article: Save Lives Through Blood Donation"""
    return render(request, 'core/articles/save_lives.html')


def article_health_benefits(request):
    """Article: Health Benefits of Blood Donation"""
    return render(request, 'core/articles/health_benefits.html')


def article_community_service(request):
    """Article: Community Service Through Blood Donation"""
    return render(request, 'core/articles/community_service.html')


def article_quick_process(request):
    """Article: Quick & Easy Blood Donation Process"""
    return render(request, 'core/articles/quick_process.html')
