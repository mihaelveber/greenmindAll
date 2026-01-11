"""
Management command to create test company with admin and 3 employees
"""
from django.core.management.base import BaseCommand
from accounts.models import User, UserRole


class Command(BaseCommand):
    help = 'Create test company: admin@gmail.com (owner) with 3 employees (sub1, sub2, sub3)'

    def handle(self, *args, **options):
        password = 'corelite'
        
        # Create company admin (organization owner)
        admin_email = 'admin@gmail.com'
        try:
            admin = User.objects.get(email=admin_email)
            self.stdout.write(self.style.WARNING(f'⚠️  {admin_email} already exists'))
        except User.DoesNotExist:
            admin = User.objects.create_user(
                username='admin',
                email=admin_email,
                password=password,
                first_name='Admin',
                last_name='Company',
                company_type='Medium (50-249)',
                wizard_completed=True,
                is_organization_owner=True
            )
            self.stdout.write(self.style.SUCCESS(f'✅ Created organization owner: {admin_email}'))
        
        # Create UserRole for admin (owner role = admin role in system)
        UserRole.objects.get_or_create(
            user=admin,
            defaults={
                'organization': admin,
                'role': 'admin',
                'show_all_disclosures': True
            }
        )
        
        # Create 3 employees
        employees = [
            {'email': 'sub1@gmail.com', 'username': 'sub1', 'first_name': 'Employee', 'last_name': 'One'},
            {'email': 'sub2@gmail.com', 'username': 'sub2', 'first_name': 'Employee', 'last_name': 'Two'},
            {'email': 'sub3@gmail.com', 'username': 'sub3', 'first_name': 'Employee', 'last_name': 'Three'},
        ]
        
        for emp_data in employees:
            email = emp_data['email']
            try:
                employee = User.objects.get(email=email)
                self.stdout.write(self.style.WARNING(f'⚠️  {email} already exists'))
            except User.DoesNotExist:
                employee = User.objects.create_user(
                    username=emp_data['username'],
                    email=email,
                    password=password,
                    first_name=emp_data['first_name'],
                    last_name=emp_data['last_name'],
                    is_organization_owner=False,  # Employee, not owner
                    wizard_completed=False
                )
                self.stdout.write(self.style.SUCCESS(f'✅ Created employee: {email}'))
            
            # Create UserRole for employee
            UserRole.objects.get_or_create(
                user=employee,
                defaults={
                    'organization': admin,
                    'role': 'member',
                    'show_all_disclosures': False
                }
            )
        
        self.stdout.write(self.style.SUCCESS('\n🎉 Done! Test company created:'))
        self.stdout.write(self.style.SUCCESS(f'  Organization: {admin_email} (password: {password})'))
        self.stdout.write(self.style.SUCCESS(f'  Employees:'))
        self.stdout.write(self.style.SUCCESS(f'    - sub1@gmail.com (password: {password})'))
        self.stdout.write(self.style.SUCCESS(f'    - sub2@gmail.com (password: {password})'))
        self.stdout.write(self.style.SUCCESS(f'    - sub3@gmail.com (password: {password})'))
        self.stdout.write(self.style.SUCCESS(f'\n  Admin panel access: mihael.veber@gmail.com only!'))
