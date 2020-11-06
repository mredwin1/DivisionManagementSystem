# DivisionManagementSystem
An application that helps organize and track employee, discipline, and time off data.


Initial Set up
    1. run pipenv install in your project directory
    2. create a config.json file
        a. 'SECRET_KEY' - This stores the Django SECRET_KEY
        b. 'EMAIL_HOST_USER' - Stores the username for the outlook email
        c. 'EMAIL_HOST_PASSWORD' - Stores the password for the outlook email
    3. run 'pipenv run makemigrations'
    4. run 'pipenv run migrate'
    5. run 'pipenv run createsuperuser'
    6. run 'pipenv run setup'
    7. run 'pipenv run collectstatic'
    8. run 'pipenv run start'