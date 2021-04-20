from django.core.management.base import BaseCommand
from employees.models import SafetyPoint, Employee
import datetime
import logging
from notifications.signals import notify


class Command(BaseCommand):
    help = 'This command goes through all the Safety Point Records and checks if there are any signed documents that' \
           'have not been uploaded. Dependant on the amount of days it has been since the creation of the record it' \
           'will send a notification'

    def handle(self, *args, **options):
        logging.info('Running safety point notification...')
        safety_point_records = SafetyPoint.objects.filter(is_active=True, employee__is_active=True).order_by('issued_date')

        today = datetime.datetime.today().date()

        for safety_point_record in safety_point_records:
            if not safety_point_record.uploaded:
                days_passed = (today - safety_point_record.issued_date).days
                verb = f'A safety point point was given to {safety_point_record.employee.get_full_name()} ' \
                       f' {days_passed} days ago and no signed document has been uploaded yet.'
                notification_types = []

                if days_passed >= 10:
                    notification_types = ['email_safety_doc_day3', 'email_safety_doc_day5',
                                          'email_safety_doc_day7', 'email_safety_doc_day10']
                elif days_passed == 7:
                    notification_types = ['email_safety_doc_day3', 'email_safety_doc_day5',
                                          'email_safety_doc_day7']
                elif days_passed == 5:
                    notification_types = ['email_safety_doc_day3', 'email_safety_doc_day5']
                elif days_passed == 3:
                    notification_types = ['email_safety_doc_day3']

                if notification_types:
                    self.send_notification(safety_point_record, notification_types, verb)

        success_message = 'Safety point notification successfully ran'
        logging.info(success_message)

    @staticmethod
    def send_notification(sender, notification_types, verb):
        for notification_type in notification_types:
            group = Employee.objects.filter(groups__name=notification_type)
            notify.send(sender=sender, recipient=group,
                        verb=verb, type=notification_type, employee_id=sender.employee.employee_id)
