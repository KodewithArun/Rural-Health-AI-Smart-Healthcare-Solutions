from django.core.management.base import BaseCommand
from django.utils import timezone
from appointments.views import auto_cancel_no_show_appointments

class Command(BaseCommand):
    help = 'Automatically cancel appointments that are 30+ minutes past their scheduled time'

    def handle(self, *args, **options):
        count = auto_cancel_no_show_appointments()
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully cancelled {count} overdue appointments.'
            )
        )