from django.core.management.base import BaseCommand
from employees.models import Employee
import datetime
import logging


class Command(BaseCommand):
    help = 'This command goes through every employee and resets their floating holidays. However, it only resets it' \
           ' if it has been a year or more since their hire date and it is January 1st.'

    def handle(self, *args, **options):
        today = datetime.datetime.today().date()

        logging.info('Running floating holiday check...')

        if today.month == 1 and today.day == 1:
            employees = Employee.objects.filter(is_active=True).order_by('hire_date')

            for employee in employees:
                tenure = (today - employee.hire_date).days
                if tenure >= 365:
                    employee.floating_holiday = 2

                    employee.save()

        logging.info('Floating holiday check ran successfully.')
