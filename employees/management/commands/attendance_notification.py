from django.core.management.base import BaseCommand
from employees.models import Attendance, Employee
import datetime
import logging


class Command(BaseCommand):
    help = 'This command goes through all the Attendance Records and checks if there are any attendance records that' \
           'have not been uploaded. Dependant on the amount of days it has been since the creation of the record it' \
           'will send a notification'

    def handle(self, *args, **options):
        logging.info('Running attendance notification...')
        attendance_records = Attendance.objects.order_by('issued_date')

        today = datetime.datetime.today().date()
        deleted_records = 0

        for attendance_record in attendance_records:
            if not attendance_record.uploaded:
                days_passed = today - attendance_record.issued_date
                logging.info(str(days_passed))

        success_message = 'It ran'
        logging.info(success_message)
