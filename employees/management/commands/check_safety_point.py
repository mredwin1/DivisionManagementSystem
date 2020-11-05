from django.core.management.base import BaseCommand
from employees.models import SafetyPoint
import datetime


class Command(BaseCommand):
    help = 'This command goes through all the Safety Point Records and deletes anything older than 18 months'

    def handle(self, *args, **options):
        safety_points = SafetyPoint.objects.order_by('incident_date')
        today = datetime.datetime.today().date()
        deleted_records = 0

        for safety_point_record in safety_points:
            days_passed = today - safety_point_record.incident_date
            if days_passed.days > 547.501:
                safety_point_record.delete()
                deleted_records += 1
            else:
                break

        success_message = 'Deleted 1 record.' if deleted_records == 1 else f'Deleted {deleted_records} records.'
        self.stdout.write(self.style.SUCCESS(success_message))
