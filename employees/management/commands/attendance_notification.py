from django.core.management.base import BaseCommand
from employees.models import Attendance, Employee
import datetime
import logging
from notifications.signals import notify


class Command(BaseCommand):
    help = 'This command goes through all the Attendance Records and checks if there are any signed documents that' \
           'have not been uploaded. Dependant on the amount of days it has been since the creation of the record it' \
           'will send a notification.'

    def handle(self, *args, **options):
        logging.info('Running attendance notification...')
        attendance_records = Attendance.objects.filter(is_active=True, employee__is_active=True).order_by('issued_date')

        today = datetime.datetime.today().date()

        for attendance_record in attendance_records:
            if not attendance_record.is_signed:
                days_passed = (today - attendance_record.issued_date).days
                verb = f'An attendance point was given to {attendance_record.employee.get_full_name()} {days_passed} ' \
                       f'days ago and has not been signed yet.'
                notification_types = []

                if days_passed >= 10:
                    notification_types = ['email_attendance_doc_day3', 'email_attendance_doc_day5',
                                          'email_attendance_doc_day7', 'email_attendance_doc_day10']
                elif days_passed == 7:
                    notification_types = ['email_attendance_doc_day3', 'email_attendance_doc_day5',
                                          'email_attendance_doc_day7']
                elif days_passed == 5:
                    notification_types = ['email_attendance_doc_day3', 'email_attendance_doc_day5']
                elif days_passed == 3:
                    notification_types = ['email_attendance_doc_day3']

                if notification_types:
                    self.send_notification(attendance_record, notification_types, verb)

        success_message = 'Attendance notification successfully ran'
        logging.info(success_message)

    @staticmethod
    def send_notification(sender, notification_types, verb):
        for notification_type in notification_types:
            group = Employee.objects.filter(groups__name=notification_type)
            notify.send(sender=sender, recipient=group,
                        verb=verb, type=notification_type, employee_id=sender.employee.employee_id)
