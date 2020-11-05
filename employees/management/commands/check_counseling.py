from django.core.management.base import BaseCommand
from employees.models import Counseling
import datetime


class Command(BaseCommand):
    help = 'This command goes through all the Counseling Records and deletes anything older than 6 months'

    def handle(self, *args, **options):
        counseling_records = Counseling.objects.order_by('issued_date')
        today = datetime.datetime.today().date()
        deleted_records = 0
        for counseling_record in counseling_records:
            days_passed = today - counseling_record.issued_date
            if days_passed.days > 182.5:
                counseling_record.delete()
                deleted_records += 1
            else:
                break

        success_message = 'Deleted 1 record.' if deleted_records == 1 else f'Deleted {deleted_records} records.'
        self.stdout.write(self.style.SUCCESS(success_message))
