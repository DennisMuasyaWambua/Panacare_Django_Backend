"""
Management command to create a test clinician user
Usage: python manage.py create_test_clinician [--email EMAIL] [--username USERNAME]
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from users.models import User, Role, Clinician
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Create a test clinician user for system testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='testclinician@panacare.com',
            help='Email address for the test clinician'
        )
        parser.add_argument(
            '--username',
            type=str,
            default='test_clinician',
            help='Username for the test clinician'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='TestClinician123!',
            help='Password for the test clinician'
        )
        parser.add_argument(
            '--verified',
            action='store_true',
            help='Create user as verified'
        )

    def handle(self, *args, **options):
        email = options['email']
        username = options['username']
        password = options['password']
        verified = options['verified']

        self.stdout.write(self.style.WARNING('Creating test clinician user...'))

        try:
            with transaction.atomic():
                # Check if user already exists
                if User.objects.filter(email=email).exists():
                    self.stdout.write(self.style.ERROR(f'User with email {email} already exists!'))
                    return

                if User.objects.filter(username=username).exists():
                    self.stdout.write(self.style.ERROR(f'User with username {username} already exists!'))
                    return

                # Create user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name='Test',
                    last_name='Clinician',
                    phone_number='+254700000000',
                    address='123 Test Hospital Road, Nairobi',
                    is_verified=verified
                )
                self.stdout.write(self.style.SUCCESS(f'✓ User created: {user.email}'))

                # Assign clinician role
                try:
                    clinician_role = Role.objects.get(name='clinician')
                    user.roles.add(clinician_role)
                    self.stdout.write(self.style.SUCCESS('✓ Clinician role assigned'))
                except Role.DoesNotExist:
                    self.stdout.write(self.style.ERROR('✗ Clinician role does not exist in database!'))
                    self.stdout.write(self.style.WARNING('Run: python manage.py migrate users'))
                    return

                # Get the auto-created clinician profile
                try:
                    clinician = Clinician.objects.get(user=user)

                    # Update clinician profile with test data
                    clinician.license_number = 'TEST-RN-12345'
                    clinician.license_type = 'Registered Nurse (Test)'
                    clinician.issuing_authority = 'Kenya Nursing Council (Test)'
                    clinician.license_expiry_date = date.today() + timedelta(days=365)
                    clinician.qualification = 'Bachelor of Science in Nursing (BSN)'
                    clinician.years_of_experience = 5
                    clinician.specialization = 'Emergency Care'
                    clinician.professional_bio = (
                        'Test clinician account created for system testing and validation. '
                        'This account demonstrates the clinician role functionality including '
                        'license management, specialization tracking, and FHIR compliance.'
                    )
                    clinician.skills = (
                        'Emergency response, Patient assessment, IV therapy, '
                        'Wound care, Medication administration, Vital signs monitoring'
                    )
                    clinician.certifications = 'BLS, ACLS, PALS, TNCC'
                    clinician.facility_name = 'Panacare Test Hospital'
                    clinician.department = 'Emergency Department'
                    clinician.is_active = True

                    # Verify if requested
                    if verified:
                        clinician.is_verified = True
                        # Note: verified_by and verification_date should be set by admin in real scenario

                    clinician.save()
                    self.stdout.write(self.style.SUCCESS('✓ Clinician profile updated with test data'))

                except Clinician.DoesNotExist:
                    self.stdout.write(self.style.ERROR('✗ Clinician profile was not auto-created!'))
                    self.stdout.write(self.style.WARNING('Check signal handler in users/models.py'))
                    return

                # Print summary
                self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
                self.stdout.write(self.style.SUCCESS('TEST CLINICIAN CREATED SUCCESSFULLY'))
                self.stdout.write(self.style.SUCCESS('=' * 60))
                self.stdout.write(f'User ID:         {user.id}')
                self.stdout.write(f'Username:        {user.username}')
                self.stdout.write(f'Email:           {user.email}')
                self.stdout.write(f'Password:        {password}')
                self.stdout.write(f'Verified:        {user.is_verified}')
                self.stdout.write(f'')
                self.stdout.write(f'Clinician ID:    {clinician.id}')
                self.stdout.write(f'License:         {clinician.license_number}')
                self.stdout.write(f'License Type:    {clinician.license_type}')
                self.stdout.write(f'Specialization:  {clinician.specialization}')
                self.stdout.write(f'Experience:      {clinician.years_of_experience} years')
                self.stdout.write(f'Facility:        {clinician.facility_name}')
                self.stdout.write(f'Department:      {clinician.department}')
                self.stdout.write(self.style.SUCCESS('=' * 60))

                self.stdout.write(self.style.WARNING('\nLogin at:'))
                self.stdout.write('https://panacaredjangobackend-production.up.railway.app/api/users/login/')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error creating test clinician: {str(e)}'))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
