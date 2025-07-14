from django.core.management.base import BaseCommand
from users.models import Role

class Command(BaseCommand):
    help = 'Create default roles for the application'

    def handle(self, *args, **options):
        # Define default roles with descriptions
        default_roles = [
            {'name': 'admin', 'description': 'Administrator with full access'},
            {'name': 'doctor', 'description': 'Medical professional who can manage patients'},
            {'name': 'patient', 'description': 'Regular user who receives healthcare'},
        ]
        
        # Create roles if they don't exist
        roles_created = 0
        roles_existed = 0
        
        for role_data in default_roles:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={'description': role_data['description']}
            )
            
            if created:
                roles_created += 1
                self.stdout.write(self.style.SUCCESS(f"Created role: {role.name}"))
            else:
                roles_existed += 1
                self.stdout.write(self.style.WARNING(f"Role already exists: {role.name}"))
        
        # Summary
        self.stdout.write(self.style.SUCCESS(f"Created {roles_created} new roles, {roles_existed} already existed."))
        self.stdout.write(self.style.SUCCESS("You can now assign these roles to users during registration."))