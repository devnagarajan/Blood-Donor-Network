"""
Script to generate donor IDs for existing donors
Run this once after migration to populate donor_id for existing donors
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from donors.models import DonorProfile
from datetime import datetime

def generate_donor_ids():
    """Generate donor IDs for all donors without one"""
    donors_without_id = DonorProfile.objects.filter(donor_id__isnull=True).order_by('created_at')
    count = donors_without_id.count()
    
    if count == 0:
        print("✓ All donors already have IDs!")
        return
    
    print(f"Found {count} donors without IDs. Generating...")
    
    year = datetime.now().year
    counter = 1
    
    # Check if there are existing IDs for this year
    last_donor = DonorProfile.objects.filter(
        donor_id__startswith=f'DNR-{year}-'
    ).exclude(donor_id__isnull=True).order_by('-created_at').first()
    
    if last_donor:
        last_number = int(last_donor.donor_id.split('-')[-1])
        counter = last_number + 1
        print(f"Last donor ID: {last_donor.donor_id}, starting from {counter}")
    
    # Generate IDs
    for donor in donors_without_id:
        donor.donor_id = f'DNR-{year}-{counter:06d}'
        donor.save(update_fields=['donor_id'])
        print(f"Generated ID {donor.donor_id} for {donor.full_name}")
        counter += 1
    
    print(f"\n✓ Successfully generated {count} donor IDs!")

if __name__ == '__main__':
    generate_donor_ids()
