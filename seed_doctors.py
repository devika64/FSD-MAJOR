import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital_portal.settings')
django.setup()

from django.contrib.auth.models import User
from appointments.models import Doctor, Appointment

def seed_data():
    print("Clearing old appointment and doctor records for a clean slate...")
    Appointment.objects.all().delete()
    Doctor.objects.all().delete()
    
    # We will clean up any existing doctor User accounts to prevent stale/incorrect mappings.
    usernames = ['arjun_sharma', 'priya_reddy', 'vikram_patel', 'neha_iyer', 'rahul_mehta', 'ananya_nair']
    User.objects.filter(username__in=usernames).delete()

    doctors_data = [
        {
            'username': 'arjun_sharma',
            'name': 'Arjun Sharma',
            'department': 'CARDIO',
            'specialization': 'Interventional Cardiology',
            'consultation_fee': 800.00,
            'available_days': 'Monday, Wednesday, Friday',
            'is_active': True
        },
        {
            'username': 'priya_reddy',
            'name': 'Priya Reddy',
            'department': 'PEDIA',
            'specialization': 'Pediatric Allergy & Immunology',
            'consultation_fee': 600.00,
            'available_days': 'Tuesday, Thursday, Saturday',
            'is_active': True
        },
        {
            'username': 'vikram_patel',
            'name': 'Vikram Patel',
            'department': 'ORTHO',
            'specialization': 'Sports Medicine & Joint Replacement',
            'consultation_fee': 700.00,
            'available_days': 'Monday, Thursday',
            'is_active': True
        },
        {
            'username': 'neha_iyer',
            'name': 'Neha Iyer',
            'department': 'NEURO',
            'specialization': 'Neuromuscular Medicine',
            'consultation_fee': 1000.00,
            'available_days': 'Wednesday, Friday',
            'is_active': True
        },
        {
            'username': 'rahul_mehta',
            'name': 'Rahul Mehta',
            'department': 'CARDIO',
            'specialization': 'Electrophysiology',
            'consultation_fee': 900.00,
            'available_days': 'Tuesday, Friday',
            'is_active': True
        },
        {
            'username': 'ananya_nair',
            'name': 'Ananya Nair',
            'department': 'PEDIA',
            'specialization': 'General Pediatrics',
            'consultation_fee': 650.00,
            'available_days': 'Monday, Wednesday, Saturday',
            'is_active': True
        }
    ]

    for doc_data in doctors_data:
        # Create a Django user for the doctor
        username = doc_data['username']
        email = f"{username}@novacare.in"
        password = "doctor123"
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        user.first_name = "Dr. " + doc_data['name'].split()[0]
        user.last_name = doc_data['name'].split()[-1]
        user.save()
        
        # Create Doctor profile linking to User
        doctor = Doctor.objects.create(
            user=user,
            name=doc_data['name'],
            department=doc_data['department'],
            specialization=doc_data['specialization'],
            consultation_fee=doc_data['consultation_fee'],
            available_days=doc_data['available_days'],
            is_active=doc_data['is_active']
        )
        print(f"Successfully seeded Doctor: {doctor} (Username: {username}, Pass: {password})")

if __name__ == '__main__':
    seed_data()

