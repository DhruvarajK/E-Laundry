import os
from django.core.management.base import BaseCommand
from myadmin.models import login

class Command(BaseCommand):
    help = 'Seeds the admin user and custom login entry from environment variables'

    def handle(self, *args, **options):
        username = os.getenv('ADMIN_USERNAME')
        password = os.getenv('ADMIN_PASSWORD')

        if not username or not password:
            self.stdout.write(self.style.ERROR('ADMIN_USERNAME or ADMIN_PASSWORD not found in environment variables'))
            return

        # 2. Seed custom login model
        if not login.objects.filter(username=username).exists():
            login.objects.create(username=username, password=password, usertype='admin')
            self.stdout.write(self.style.SUCCESS(f'Successfully created custom login entry for: {username}'))
        else:
            self.stdout.write(self.style.WARNING(f'Custom login entry for "{username}" already exists'))
