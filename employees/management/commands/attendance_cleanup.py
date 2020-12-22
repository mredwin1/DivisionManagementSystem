from django.core.management.base import BaseCommand
from employees.models import Attendance, Employee
import datetime
import logging


class Command(BaseCommand):
    help = 'This command goes through all the Attendance Records and deletes anything older than 1 year and also' \
           'deletes all Attendance Records for an Employee if they have gone 6 months with no Attendance Records'

    def handle(self, *args, **options):
        logging.info('Running attendance cleanup...')
        attendance_records = Attendance.objects.order_by('incident_date')
        employees = Employee.objects.all()
        today = datetime.datetime.today().date()
        deleted_records = 0

        for attendance_record in attendance_records:
            days_passed = today - attendance_record.incident_date

            if days_passed.days > 365:
                attendance_record.delete()
                deleted_records += 1
            else:
                break

        for employee in employees:
            employee_attendance = attendance_records.filter(employee=employee).order_by('-incident_date')

            if employee_attendance:
                days_passed = today - employee_attendance.first().incident_date
                if days_passed.days > 182.5:
                    deleted_records += len(employee_attendance)
                    employee_attendance.delete()

        success_message = 'Deleted 1 record.' if deleted_records == 1 else f'Deleted {deleted_records} records.'
        logging.info(success_message)
