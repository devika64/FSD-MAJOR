import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital_portal.settings')
django.setup()

from django.contrib.auth.models import User

def create_admin():
    username = os.environ.get('SUPERUSER_USERNAME', 'admin')
    email = os.environ.get('SUPERUSER_EMAIL', 'admin@example.com')
    password = os.environ.get('SUPERUSER_PASSWORD', 'admin123')

    # Use User.objects.db_manager('default') as required by system spec
    manager = User.objects.db_manager('default')
    
    if not manager.filter(username=username).exists():
        print(f"Creating admin superuser: {username} ({email})...")
        manager.create_superuser(
            username=username,
            email=email,
            password=password
        )
        print("Superuser created successfully.")
    else:
        print(f"Superuser with username '{username}' already exists.")

if __name__ == '__main__':
    create_admin()
