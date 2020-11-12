import socket
import time
import sys
import os

from django.core.management.base import BaseCommand
from django.core.management import call_command


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
                print("Database is ready.")
                break
            except socket.error:
                attempts_left -= 1
                print("Not ready yet, retrying.")
                time.sleep(0.5)
        else:
            print("Database could not be found, exiting.")
            sys.exit(1)

        print('Running migrations')
        call_command("migrate")
        print('Running setup')
        call_command("setup")
        print('Running collectstatic')
        call_command("collectstatic", interactive=False, clear=True)
        print('Starting server')
        os.system("gunicorn --preload -b 0.0.0.0:8001 DivisionManagementSystem.wsgi:application --threads 8 -w 4")
        exit()
