import socket
import time
import sys
import os
import logging

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db.utils import OperationalError


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
                logging.warning('Not ready yet, retrying.')
                time.sleep(0.5)
        else:
            logging.error('Database could not be found, exiting.')
            sys.exit(1)

        attempts_left = 5
        while attempts_left:
            try:
                logging.info('Trying to run migrations')
                call_command("migrate")
                logging.info('Migrations ran')
                break
            except OperationalError:
                attempts_left -= 1
                logging.warning('Cannot run migrations, retrying.')
                time.sleep(0.5)
        else:
            logging.error('Migrations could not be run, exiting.')
            sys.exit(1)

        logging.info('Running setup')
        call_command("setup")
        logging.info('Running collectstatic')
        call_command("collectstatic", interactive=False, clear=True)
        logging.info('Starting server')
        os.system("gunicorn --preload -b 0.0.0.0:8001 DivisionManagementSystem.wsgi:application --threads 8 -w 4")
        exit()
