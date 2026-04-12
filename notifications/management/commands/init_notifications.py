from django.core.management.base import BaseCommand
from notifications.services import NotificationService


class Command(BaseCommand):
    help = 'Initialize default notification templates'

    def handle(self, *args, **options):
        self.stdout.write('Creating default notification templates...')
        NotificationService.create_default_templates()
        self.stdout.write(self.style.SUCCESS('Default notification templates created successfully!'))
