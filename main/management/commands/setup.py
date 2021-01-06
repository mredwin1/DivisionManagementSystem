import logging

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'This command goes through all the set up steps for a new application.'

    def handle(self, *args, **options):
        # Setting up groups for each notification type
        notification_groups = ['email_7attendance', 'email_10attendance', 'email_written', 'email_last_final',
                               'email_removal', 'email_safety_point', 'email_termination', 'email_add_hold',
                               'email_rem_hold', 'email_add_settlement', 'email_new_time_off', 'email_new_employee',
                               'email_attendance_doc_day3', 'email_attendance_doc_day5', 'email_attendance_doc_day7',
                               'email_attendance_doc_day10']
        all_groups = [group.name for group in Group.objects.all()]

        for group_name in notification_groups:
            if group_name in all_groups:
                logging.info(f'Group "{group_name}" already exists, skipping.')
            else:
                new_group, created = Group.objects.get_or_create(name=group_name)

                if created:
                    success_message = f'Successfully created "{new_group}" group.'
                    logging.info(success_message)
                else:
                    fail_message = f'Could not create "{new_group}" group.'
                    logging.error(fail_message)
