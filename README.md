# DivisionManagementSystem
A django web application geared towards the transportation industry to help organize employee data, discipline, and time off. The application is containerized for easy deployment and can be set up in a matter of minutes.

## Features

#### Manage Employees
- Add, Edit, and Remove Employees
- Search for Any Employee with Smart Filtering
- Store Employee Information
    - Personal and Disciplinary
- Individual Employee Profiles
    - Immediately see all necessary information for any given employee

#### Perform and Automate Operation’s Tasks
- Place Employees on Hold
- Assign Attendance Points
    - Automatically create necessary documents
    - Automatically assign necessary counseling (Written warning and removal from service)
- Assign Counseling (Verbal, Written, Removal, etc.)
- Place Time Off Request
    - Track time off request for employees
- Terminate Employees
- Make Settlements for Employees Pending Termination
- Automatically Delete All Old/Invalid Attendance Records
    - Will delete any attendance older than one year by default or if employee has gone 6 months with no other attendance issues delete all attendance records by default.

#### Reporting for Operation’s Data with Smart Filtering
- Attendance Reports
    - See all employee’s attendance issues
    - Download any attendance form as PDF
- Counseling Reports
    - See all employee’s counseling issues
    - Download any counseling form as PDF
- Time Off Reports
    - See all time off requests and their status (Approved, Denied, Pending)

#### Permissions System
- Deny, Grant Access to Certain Pages or Actions
    - Set Groups to Easily Manage Employee permissions

#### Notification System
- Receive Notifications when Certain Events get Triggered
    - Employee placed on hold, employee removed from service, etc.
    - Toggle Emailing On/Off for Different Events

#### Export Data
- Phone List, Seniority List, Attendance Points, etc.

---
## Installation

1. Install docker & docker-compose. [Windows/Mac](https://www.docker.com/products/docker-desktop)
2. Create a docker network with the name "traefik_default"
2. Clone repo
3. Create a .env for all required environment variables
    - SECRET_KEY: The django secret key. [This](https://djecrety.ir/) can be used to generate a random secret key. More info on how this affects the project can be read [here](https://docs.djangoproject.com/en/3.1/ref/settings/#secret-key).
    - DEBUG: The django debug mode is used to display detailed error messages on the site. Here set it to either 1 or 0(True or False), it is reccommended to set it to 0 for production puposes. More info how this affects the application can be read [here](https://docs.djangoproject.com/en/3.1/ref/settings/#debug).
    - EMAIL_HOST: The host which emails will be sent from
    - EMAIL_PORT: The port to use to send emails
    - EMAIL_USE_TLS: Use TLS or not when sending emails (0 or 1)
    - EMAIL_HOST_USER: The email from which notifications will be sent.
    - EMAIL_HOST_PASSWORD: The password for the email provided.
    - SUPER_USERNAME: The username you want to set for the superuser that will be created.
    - SUPER_PASSWORD: The password for the superuser.
    - SQL_DATABASE: The name you want to use for the database where all the django tables will be saved.
    - SQL_PORT: The port for which the postgresql service in the docker container is exposed which is 5432 by defaul
    - SQL_HOST: The name of the postgresql service in the docker container which is 'db' by deafault. If you make changes to the docker-compose file then set this accordingly.
    - SQL_USER: The postgresql user that will have access to the created database.
    - SQL_PASSWORD: The password for the postgresql user
    - DOMAIN: The domain which incoming requests will be sent to the dms service.
    - ACME_EMAIL: The email in which you will register all the SSL with LetsEncrypt
    - TRAEFIK_LOG: The log level in which to run the traefik docker service
    - USE_S3: To either use S3 for all static and media files or use the filesystem on the local server. Set this to either 0 or 1.
    - AWS_ACCESS_KEY_ID: The access key ID for the AWS S3 bucket
    - AWS_SECRET_ACCESS_KEY: The access key for the AWS S3 bucket
    - AWS_STORAGE_BUCKET_NAME: The name set for the AWS S3 bucket
4. Run the command 'docker-compose up' inside the main project directory where the docker-compose.yaml file is. This will make the server available through the set DOMAIN, to log in simply use what was set for SUPER_USERNAME and SUPER_PASSWORD.
