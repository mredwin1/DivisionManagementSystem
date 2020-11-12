import logging

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'This command goes through all the set up steps for a new application.'

    def handle(self, *args, **options):
        # Setting up groups for each notification type
        group_names = ['email_7attendance', 'email_10attendance', 'email_written', 'email_removal',
                       'email_safety_point', 'email_termination', 'email_add_hold', 'email_rem_hold',
                       'email_add_settlement']

        for group_name in group_names:
            new_group, created = Group.objects.get_or_create(name=group_name)

            if created:
                success_message = f'Successfully created {new_group}'
                logging.info(success_message)
            else:
                fail_message = f'Could not create {new_group}'
                logging.warning(fail_message)
