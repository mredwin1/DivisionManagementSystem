import logging
import os
import socket
import sys
import time

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db.utils import OperationalError

from employees.models import Employee


class Command(BaseCommand):
    help = 'An alternative to runserver which will run migrate and collectstatic beforehand'

    def handle(self, *args, **options):
        # Attempt to connect to the database socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        attempts_left = 10
        while attempts_left:
            try:
                # Ignore 'incomplete startup packet'
                s.connect((os.environ['SQL_HOST'], int(os.environ['SQL_PORT'])))
                s.shutdown(socket.SHUT_RDWR)
                logging.info('Database is ready.')
                break
            except socket.error:
                attempts_left -= 1
                logging.warning('Database not ready yet, retrying.')
                time.sleep(0.5)
        else:
            logging.error('Database could not be found, exiting.')
            sys.exit('Database not found')

        attempts_left = 5
        while attempts_left:
            try:
                logging.info('Trying to run migrations...')
                call_command("migrate")
                logging.info('Migrations complete')
                break
            except OperationalError as error:
                if error.args[0] == 'FATAL:  the database system is starting up\n':
                    attempts_left -= 1
                    logging.warning('Cannot run migrations because the database system is starting up, retrying.')
                    time.sleep(0.5)
                else:
                    sys.exit(f'Migrations unsuccessful. Error: {error.args}')
        else:
            logging.error('Migrations could not be run, exiting.')
            sys.exit('Migrations unsuccessful')

        if not Employee.objects.filter(username=os.environ['SUPER_USERNAME']).exists():
            Employee.objects.create_superuser(
                username=os.environ['SUPER_USERNAME'],
                password=os.environ['SUPER_PASSWORD'],
                employee_id=0,
                first_name='admin'
            )
            logging.info('Superuser created.')
        else:
            logging.info('Superuser already created, skipping that step.')

        logging.info('Running setup...')
        call_command("setup")
        logging.info('Running collectstatic...')
        call_command("collectstatic", interactive=False, clear=True)

        logging.info('Starting server...')
        os.system("gunicorn --preload -b 0.0.0.0:80 DivisionManagementSystem.wsgi:application --threads 8 -w 4")
        exit()
