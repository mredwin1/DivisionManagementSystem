from django.core.management.base import BaseCommand
from employees.models import Settlement, Employee
import datetime
import logging
from notifications.signals import notify


class Command(BaseCommand):
    help = 'This command goes through all the Settlement Records and checks if there are any signed documents that' \
           'have not been uploaded. Dependant on the amount of days it has been since the creation of the record it' \
           'will send a notification.'

    def handle(self, *args, **options):
        logging.info('Running settlement notification...')
        settlement_records = Settlement.objects.filter(is_active=True).order_by('created_date')

        today = datetime.datetime.today().date()

        for settlement_record in settlement_records:
            if not settlement_record.uploaded:
                days_passed = (today - settlement_record.created_date).days
                verb = f'A settlement was created for {settlement_record.employee.get_full_name()} {days_passed}' \
                       f' days ago and no signed document has been uploaded yet.'
                notification_types = []

                if days_passed >= 3:
                    notification_types = ['email_settlement_doc']
                    logging.info(f'days passed: {days_passed}')

                if notification_types:
                    self.send_notification(settlement_record, notification_types, verb)

        success_message = 'Attendance settlement successfully ran'
        logging.info(success_message)

    @staticmethod
    def send_notification(sender, notification_types, verb):
        for notification_type in notification_types:
            group = Employee.objects.filter(groups__name=notification_type)
            notify.send(sender=sender, recipient=group,
                        verb=verb, type=notification_type, employee_id=sender.employee_id)
            logging.info(f'Notification Sent')
