import datetime
import io
import requests

from PyPDF2 import PdfFileMerger, PdfFileReader
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from .models import Counseling, Attendance


def combine_attendance_documents(attendance_ids):
    """
    This function accepts a list of Attendance Ids and gets the PDFs associated with each of those and combines them
    into one PDF and returns it. Also if there is any counseling it will also add those PDFs

    :param attendance_ids: List of Attendance Ids
    :return: bytes object
    """
    buffer = io.BytesIO()

    merged_object = PdfFileMerger()

    attendance_list = Attendance.objects.filter(id__in=attendance_ids)

    for attendance in attendance_list:
        remote_file = requests.get(attendance.document.url).content
        memory_file = io.BytesIO(remote_file)
        merged_object.append(PdfFileReader(memory_file))

        try:
            remote_file = requests.get(attendance.counseling.document.url).content
            memory_file = io.BytesIO(remote_file)
            merged_object.append(PdfFileReader(memory_file))
        except Counseling.DoesNotExist:
            pass

    merged_object.write(buffer)

    return buffer


def create_safety_meeting_attendance(employees):
    """This function takes a query set of employees and creates a PDF with all the names and their IDs and a spot to
    sign, meant to be used for safety meeting attendance.

    :param employees: QuerySet

    :return phone_list: ContentFile (The PDF)
    """
    buffer = io.BytesIO()

    p = canvas.Canvas(buffer, pagesize=letter)

    p.setLineWidth(.75)

    # Title
    title = 'Safety Meeting Attendance List'
    p.setFontSize(18)
    p.drawCentredString(4.25 * inch, 10.5 * inch, title)

    # Disclaimers
    p.setFontSize(10)
    p.drawString(.5 * inch, 10 * inch, 'On')
    p.line(.70 * inch, 10 * inch, 3.0 * inch, 10 * inch)

    p.drawString(3.10 * inch, 10 * inch, 'at')
    p.line(3.25 * inch, 10 * inch, 3.80 * inch, 10 * inch)

    p.drawString(3.85 * inch, 10 * inch, 'training was conducted on these topics:')
    p.line(6.35 * inch, 10 * inch, 8 * inch, 10 * inch)

    p.line(.5 * inch, 9.65 * inch, 8 * inch, 9.65 * inch)
    p.line(.5 * inch, 9.35 * inch, 8 * inch, 9.35 * inch)
    p.line(.5 * inch, 9.05 * inch, 8 * inch, 9.05 * inch)

    p.drawString(.5 * inch, 8.75 * inch, 'This training is in compliance with Federal, State, and local regulations, as well as MV company policy.')
    p.drawString(.5 * inch, 8.55 * inch, 'The following were in attendance:')

    total_pages = int(len(employees) / 18) + 1
    page_num = 1
    y = 7.5

    counter = 1
    p.setFontSize(12)
    for employee in employees:
        p.drawString(.625 * inch, y * inch, str(counter))
        p.drawString(1.0 * inch, y * inch, employee.get_full_name())
        p.drawString(2.75 * inch, y * inch, str(employee.employee_id))
        p.line(0.5 * inch, (y - .2) * inch, 8 * inch, (y - .2) * inch)  # Bottom

        if y <= 1 or len(employees) == counter:
            grid_bottom = y - .2
            y = 7.9 if page_num == 1 else 10.4
            # Heading
            p.drawString(1.00 * inch, y * inch, 'Name')
            p.drawString(2.75 * inch, y * inch, 'Employee #')
            p.drawString(4.00 * inch, y * inch, 'Time')
            p.drawString(5.50 * inch, y * inch, 'Signature')

            # Footer
            p.drawString(1 * inch, .5 * inch, datetime.datetime.today().strftime('%A, %B %d, %Y'))
            p.drawRightString(7.5 * inch, .5 * inch, f'Page {page_num} of {total_pages}')

            # Grid
            p.line(0.5 * inch, (y - .07) * inch, 8 * inch, (y - .07) * inch)  # Top
            p.line(3.9 * inch, (y - .07) * inch, 3.9 * inch, grid_bottom * inch)  # Vertical 1
            p.line(4.9 * inch, (y - .07) * inch, 4.9 * inch, grid_bottom * inch)  # Vertical 2

            p.showPage()

            page_num += 1

            y = 7.9 if page_num == 1 else 10.4

        counter += 1
        y -= .5

    p.save()

    return ContentFile(buffer.getbuffer())


def create_phone_list(employees):
    """This function takes a query set of employees and creates a PDF with all the phone numbers (Primary and Secondary)
    of each of them.

    :param employees: QuerySet

    :return phone_list: ContentFile (The PDF)
    """

    buffer = io.BytesIO()

    p = canvas.Canvas(buffer, pagesize=letter)

    p.setLineWidth(.75)

    # Title
    title = 'Division 12 - Driver Phone List'
    p.setFontSize(18)
    p.drawCentredString(4.25 * inch, 10.5 * inch, title)

    total_pages = int(len(employees) / 38) + 1
    page_num = 1
    y = 10.00

    counter = 1

    for employee in employees:
        primary_phone = f'{employee.primary_phone.as_e164[:-10]}({employee.primary_phone.as_e164[-10:-7]}) {employee.primary_phone.as_e164[-7:-4]}-{employee.primary_phone.as_e164[-4:]}' if employee.primary_phone else ''
        secondary_phone = f'{employee.secondary_phone.as_e164[:-10]}({employee.secondary_phone.as_e164[-10:-7]}) {employee.secondary_phone.as_e164[-7:-4]}-{employee.secondary_phone.as_e164[-4:]}' if employee.secondary_phone else ''

        p.setFont('Helvetica', 10)

        p.drawString(1 * inch, y * inch, employee.last_name)
        p.drawString(2.5 * inch, y * inch, employee.first_name)
        p.drawString(3.5 * inch, y * inch, primary_phone)
        p.drawString(5.5 * inch, y * inch, secondary_phone)
        p.line(0.9 * inch, (y - .1) * inch, 7.6 * inch, (y - .1) * inch)  # Bottom

        if y == 1 or len(employees) == counter:
            p.setFont('Helvetica-Bold', 10)

            grid_bottom = y - .1
            y = 10.25

            # Heading
            p.drawString(1 * inch, y * inch, 'Last Name')
            p.drawString(2.5 * inch, y * inch, 'First Name')
            p.drawString(3.5 * inch, y * inch, 'Primary Phone Number')
            p.drawString(5.5 * inch, y * inch, 'Secondary Phone Number')

            # Footer
            p.drawString(1 * inch, .5 * inch, datetime.datetime.today().strftime('%A, %B %d, %Y'))
            p.drawRightString(7.5 * inch, .5 * inch, f'Page {page_num} of {total_pages}')

            # Grid
            p.line(0.9 * inch, (y - .07) * inch, 7.6 * inch, (y - .07) * inch)  # Top
            p.line(0.9 * inch, (y - .07) * inch, 0.9 * inch, grid_bottom * inch)  # Left
            p.line(7.6 * inch, (y - .07) * inch, 7.6 * inch, grid_bottom * inch)  # Right
            p.line(2.4 * inch, (y - .07) * inch, 2.4 * inch, grid_bottom * inch)  # Vertical 1
            p.line(3.4 * inch, (y - .07) * inch, 3.4 * inch, grid_bottom * inch)  # Vertical 2
            p.line(5.4 * inch, (y - .07) * inch, 5.4 * inch, grid_bottom * inch)  # Vertical 3

            p.showPage()

            page_num += 1

        counter += 1
        y -= .25

    p.save()

    return ContentFile(buffer.getbuffer())


def create_seniority_list(employees):
    """
        This function takes a query set of employees ordered by hire_date then creates a PDF with their employee numbers
        along with the hire dates and names.

        :param employees: QuerySet

        :return phone_list: ContentFile (The PDF)
        """

    buffer = io.BytesIO()

    p = canvas.Canvas(buffer, pagesize=letter)

    p.setLineWidth(.75)

    # Title
    title = 'Division 12 - Driver Seniority List'
    p.setFontSize(18)
    p.drawCentredString(4.25 * inch, 10.5 * inch, title)

    total_pages = int(len(employees) / 38) + 1
    page_num = 1
    y = 10.00

    counter = 1

    for employee in employees:
        p.setFont('Helvetica', 10)

        p.drawString(1.00 * inch, y * inch, str(counter))
        p.drawString(1.50 * inch, y * inch, employee.last_name)
        p.drawString(3.00 * inch, y * inch, employee.first_name)
        p.drawString(4.00 * inch, y * inch, employee.hire_date.strftime('%m-%d-%Y'))
        p.drawString(5.00 * inch, y * inch, employee.application_date.strftime('%m-%d-%Y'))
        p.drawString(6.25 * inch, y * inch, str(employee.employee_id))
        p.line(0.9 * inch, (y - .1) * inch, 7.6 * inch, (y - .1) * inch)  # Bottom

        if y == 1 or len(employees) == counter:
            p.setFont('Helvetica-Bold', 10)

            grid_bottom = y - .1
            y = 10.25

            # Heading
            p.drawString(1.50 * inch, y * inch, 'Last Name')
            p.drawString(3.00 * inch, y * inch, 'First Name')
            p.drawString(4.00 * inch, y * inch, 'Hire Date')
            p.drawString(5.00 * inch, y * inch, 'Application Date')
            p.drawString(6.25 * inch, y * inch, 'Employee Number')

            # Footer
            p.drawString(1 * inch, .5 * inch, datetime.datetime.today().strftime('%A, %B %d, %Y'))
            p.drawRightString(7.5 * inch, .5 * inch, f'Page {page_num} of {total_pages}')

            # Grid
            p.line(0.90 * inch, (y - .07) * inch, 7.60 * inch, (y - .07) * inch)  # Top
            p.line(0.90 * inch, (y - .07) * inch, 0.90 * inch, grid_bottom * inch)  # Left
            p.line(7.60 * inch, (y - .07) * inch, 7.60 * inch, grid_bottom * inch)  # Right
            p.line(1.40 * inch, (y - .07) * inch, 1.40 * inch, grid_bottom * inch)  # Vertical 1
            p.line(2.90 * inch, (y - .07) * inch, 2.90 * inch, grid_bottom * inch)  # Vertical 2
            p.line(3.90 * inch, (y - .07) * inch, 3.90 * inch, grid_bottom * inch)  # Vertical 3
            p.line(4.90 * inch, (y - .07) * inch, 4.90 * inch, grid_bottom * inch)  # Vertical 4
            p.line(6.15 * inch, (y - .07) * inch, 6.15 * inch, grid_bottom * inch)  # Vertical 5

            p.showPage()

            page_num += 1

        counter += 1
        y -= .25

    p.save()

    return ContentFile(buffer.getbuffer())


def create_driver_list(employees):
    """
        This function takes a query set of employees ordered by hire_date then creates a PDF with their employee numbers
        along with the hire dates and names.

        :param employees: QuerySet

        :return phone_list: ContentFile (The PDF)
        """

    buffer = io.BytesIO()

    p = canvas.Canvas(buffer, pagesize=letter)

    p.setLineWidth(.75)

    # Title
    title = 'Division 12 - Driver List'
    p.setFontSize(18)
    p.drawCentredString(4.25 * inch, 10.5 * inch, title)

    total_pages = int(len(employees) / 38) + 1
    page_num = 1
    y = 10.00

    counter = 1

    for employee in employees:
        p.setFont('Helvetica', 10)

        p.drawString(1.00 * inch, y * inch, str(counter))
        p.drawString(1.50 * inch, y * inch, employee.last_name)
        p.drawString(3.25 * inch, y * inch, employee.first_name)
        p.drawString(5.00 * inch, y * inch, employee.hire_date.strftime('%m-%d-%Y'))
        p.drawString(6.25 * inch, y * inch, str(employee.employee_id))
        p.line(0.9 * inch, (y - .1) * inch, 7.6 * inch, (y - .1) * inch)  # Bottom

        if y == 1 or len(employees) == counter:
            p.setFont('Helvetica-Bold', 10)

            grid_bottom = y - .1
            y = 10.25

            # Heading
            p.drawString(1.50 * inch, y * inch, 'Last Name')
            p.drawString(3.25 * inch, y * inch, 'First Name')
            p.drawString(5.00 * inch, y * inch, 'Hire Date')
            p.drawString(6.25 * inch, y * inch, 'Employee Number')

            # Footer
            p.drawString(1 * inch, .5 * inch, datetime.datetime.today().strftime('%A, %B %d, %Y'))
            p.drawRightString(7.5 * inch, .5 * inch, f'Page {page_num} of {total_pages}')

            # Grid
            p.line(0.90 * inch, (y - .07) * inch, 7.60 * inch, (y - .07) * inch)  # Top
            p.line(0.90 * inch, (y - .07) * inch, 0.90 * inch, grid_bottom * inch)  # Left
            p.line(7.60 * inch, (y - .07) * inch, 7.60 * inch, grid_bottom * inch)  # Right
            p.line(1.40 * inch, (y - .07) * inch, 1.40 * inch, grid_bottom * inch)  # Vertical 1
            p.line(3.15 * inch, (y - .07) * inch, 3.15 * inch, grid_bottom * inch)  # Vertical 2
            p.line(4.90 * inch, (y - .07) * inch, 4.90 * inch, grid_bottom * inch)  # Vertical 3
            p.line(6.15 * inch, (y - .07) * inch, 6.15 * inch, grid_bottom * inch)  # Vertical 5

            p.showPage()

            page_num += 1

        counter += 1
        y -= .25

    p.save()

    return ContentFile(buffer.getbuffer())


def create_custom_list(employees):
    """
        This function takes a query set of employees ordered by the filter and returns a PDF

        :param employees: QuerySet

        :return phone_list: ContentFile (The PDF)
        """

    buffer = io.BytesIO()

    p = canvas.Canvas(buffer, pagesize=letter)

    p.setLineWidth(.75)

    # Title
    title = 'Division 12 - Custom List'
    p.setFontSize(18)
    p.drawCentredString(4.25 * inch, 10.5 * inch, title)

    total_pages = int(len(employees) / 38) + 1
    page_num = 1
    y = 10.00

    counter = 1

    for employee in employees:
        primary_phone = f'{employee.primary_phone.as_e164[:-10]}({employee.primary_phone.as_e164[-10:-7]}) {employee.primary_phone.as_e164[-7:-4]}-{employee.primary_phone.as_e164[-4:]}' if employee.primary_phone else ''
        secondary_phone = f'{employee.secondary_phone.as_e164[:-10]}({employee.secondary_phone.as_e164[-10:-7]}) {employee.secondary_phone.as_e164[-7:-4]}-{employee.secondary_phone.as_e164[-4:]}' if employee.secondary_phone else ''

        p.setFont('Helvetica', 10)

        p.drawString(0.50 * inch, y * inch, f'{employee.last_name}, {employee.first_name}')
        p.drawString(2.20 * inch, y * inch, str(employee.employee_id))
        p.drawString(2.95 * inch, y * inch, employee.company.display_name if employee.company else '')
        p.drawString(3.40 * inch, y * inch, employee.hire_date.strftime('%m-%d-%Y') if employee.hire_date else '')
        p.drawString(4.35 * inch, y * inch, employee.get_position_display())
        p.drawString(5.70 * inch, y * inch, primary_phone)
        p.drawString(6.95 * inch, y * inch, secondary_phone)
        p.line(0.40 * inch, (y - .1) * inch, 8.10 * inch, (y - .1) * inch)  # Bottom

        if y == 1 or len(employees) == counter:
            p.setFont('Helvetica-Bold', 10)

            grid_bottom = y - .1
            y = 10.25

            # Heading
            p.drawString(0.50 * inch, y * inch, 'Employee Name')
            p.drawString(2.20 * inch, y * inch, 'ID')
            p.drawString(2.95 * inch, y * inch, 'Co.')
            p.drawString(3.40 * inch, y * inch, 'Hire Date')
            p.drawString(4.35 * inch, y * inch, 'Position')
            p.drawString(5.70 * inch, y * inch, 'Primary Phone')
            p.drawString(6.95 * inch, y * inch, 'Secondary Phone')

            # Footer
            p.drawString(1 * inch, .5 * inch, datetime.datetime.today().strftime('%A, %B %d, %Y'))
            p.drawRightString(7.5 * inch, .5 * inch, f'Page {page_num} of {total_pages}')

            # Grid
            p.line(0.40 * inch, (y - .07) * inch, 8.10 * inch, (y - .07) * inch)  # Top
            p.line(0.40 * inch, (y - .07) * inch, 0.40 * inch, grid_bottom * inch)  # Left
            p.line(8.10 * inch, (y - .07) * inch, 8.10 * inch, grid_bottom * inch)  # Right
            p.line(2.15 * inch, (y - .07) * inch, 2.15 * inch, grid_bottom * inch)  # Vertical 1
            p.line(2.85 * inch, (y - .07) * inch, 2.85 * inch, grid_bottom * inch)  # Vertical 2
            p.line(3.35 * inch, (y - .07) * inch, 3.35 * inch, grid_bottom * inch)  # Vertical 2
            p.line(4.30 * inch, (y - .07) * inch, 4.30 * inch, grid_bottom * inch)  # Vertical 2
            p.line(5.65 * inch, (y - .07) * inch, 5.65 * inch, grid_bottom * inch)  # Vertical 3
            p.line(6.90 * inch, (y - .07) * inch, 6.90 * inch, grid_bottom * inch)  # Vertical 5

            p.showPage()

            page_num += 1

        counter += 1
        y -= .25

    p.save()

    return ContentFile(buffer.getbuffer())