"""
Management command to create test users for team collaboration
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.team_models import UserRole

User = get_user_model()


class Command(BaseCommand):
    help = 'Create 3 test users with mihael.veber@gmail.com as organization owner'

    def handle(self, *args, **kwargs):
        # Get organization owner
        try:
            org_owner = User.objects.get(email='mihael.veber@gmail.com')
            self.stdout.write(self.style.SUCCESS(f'Found organization owner: {org_owner.email}'))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('Organization owner mihael.veber@gmail.com not found!'))
            return

        # Test users data
        test_users = [
            {'email': 'test1@gmail.com', 'role': 'member'},
            {'email': 'test2@gmail.com', 'role': 'member'},
            {'email': 'test3@gmail.com', 'role': 'admin'},
        ]

        password = 'corelite'

        for user_data in test_users:
            email = user_data['email']
            role = user_data['role']

            # Check if user already exists
            if User.objects.filter(email=email).exists():
                self.stdout.write(self.style.WARNING(f'User {email} already exists, skipping...'))
                continue

            # Create user
            username = email.split('@')[0]  # Extract username from email
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                wizard_completed=True,
                is_organization_owner=False
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Created user: {email}'))

            # Create UserRole
            user_role = UserRole.objects.create(
                user=user,
                role=role,
                organization=org_owner,
                show_all_disclosures=False  # Default: see only assigned
            )
            self.stdout.write(self.style.SUCCESS(f'  - Assigned role: {role}'))
            self.stdout.write(self.style.SUCCESS(f'  - Organization: {org_owner.email}'))

        self.stdout.write(self.style.SUCCESS('\n🎉 All test users created successfully!'))
        self.stdout.write(self.style.SUCCESS('\nTest Users:'))
        self.stdout.write(self.style.SUCCESS('  - test1@gmail.com (member) - password: corelite'))
        self.stdout.write(self.style.SUCCESS('  - test2@gmail.com (member) - password: corelite'))
        self.stdout.write(self.style.SUCCESS('  - test3@gmail.com (admin) - password: corelite'))
        self.stdout.write(self.style.SUCCESS(f'\nOrganization: {org_owner.email}'))
