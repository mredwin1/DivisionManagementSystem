from django.core.management.base import BaseCommand
from employees.models import TimeOffRequest
import datetime


class Command(BaseCommand):
    help = 'This command goes through all the Time Off Records and deletes anything older than 6 months'

    def handle(self, *args, **options):
        time_off_records = TimeOffRequest.objects.order_by('incident_date')
        today = datetime.datetime.today().date()
        deleted_records = 0

        for time_off_record in time_off_records:
            days_passed = today - time_off_record.request_date
            if days_passed.days > 182.5:
                time_off_record.delete()
                deleted_records += 1
            else:
                break

        success_message = 'Deleted 1 record.' if deleted_records == 1 else f'Deleted {deleted_records} records.'
        self.stdout.write(self.style.SUCCESS(success_message))
