from django.core.management.base import BaseCommand
from employees.models import Counseling, Employee
import datetime
import logging
from notifications.signals import notify


class Command(BaseCommand):
    help = 'This command goes through all the Counseling Records and checks if there are any signed documents that' \
           'have not been uploaded. Dependant on the amount of days it has been since the creation of the record it' \
           'will send a notification.'

    def handle(self, *args, **options):
        logging.info('Running counseling notification...')
        counseling_records = Counseling.objects.filter(is_active=True).order_by('issued_date')

        today = datetime.datetime.today().date()

        for counseling_record in counseling_records:
            if not counseling_record.uploaded:
                days_passed = (today - counseling_record.issued_date).days
                verb = f'A counseling was given to {counseling_record.employee.get_full_name()} {days_passed} days' \
                       f'ago and no signed document has been uploaded yet.'
                notification_types = []

                if days_passed >= 10:
                    notification_types = ['email_counseling_doc_day3', 'email_counseling_doc_day5',
                                          'email_counseling_doc_day7', 'email_counseling_doc_day10']
                elif days_passed == 7:
                    notification_types = ['email_counseling_doc_day3', 'email_counseling_doc_day5',
                                          'email_counseling_doc_day7']
                elif days_passed == 5:
                    notification_types = ['email_counseling_doc_day3', 'email_counseling_doc_day5']
                elif days_passed == 3:
                    notification_types = ['email_counseling_doc_day3']

                if notification_types:
                    self.send_notification(counseling_record, notification_types, verb)

        success_message = 'Counseling notification successfully ran'
        logging.info(success_message)

    @staticmethod
    def send_notification(sender, notification_types, verb):
        for notification_type in notification_types:
            group = Employee.objects.filter(groups__name=notification_type)
            notify.send(sender=sender, recipient=group,
                        verb=verb, type=notification_type, employee_id=sender.employee_id)
