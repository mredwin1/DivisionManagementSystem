import datetime
import io
import requests

from PyPDF2 import PdfFileMerger, PdfFileReader
from django.contrib.auth import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone

from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill
from notifications.models import Notification
from phonenumber_field.modelfields import PhoneNumberField
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from titlecase import titlecase
from urllib.parse import urljoin

from .managers import EmployeeManager
from .validators import pdf_extension


class Company(models.Model):
    is_active = models.BooleanField(default=True)
    full_name = models.CharField(max_length=80, unique=True)
    display_name = models.CharField(max_length=15, unique=True)

    class Meta:
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'

    def __str__(self):
        return self.display_name


class Employee(AbstractBaseUser, PermissionsMixin):
    """A model representing an employee

    :param is_active: A boolean flag to represent if the Employee is active or not, defaults to 'False'
    :type is_active: bool
    :param is_superuser: A boolean flag to represent if the Employee is superuser or not, defaults to 'False'. If superuser then all permissions are granted.
    :type is_superuser: bool
    :param is_staff: A boolean flag to represent if the Employee is staff or not, defaults to 'False'. Grants access to admin panel.
    :type is_staff: bool
    :param is_part_time: A boolean flag to represent if the Employee is part time or not, defaults to 'False'
    :type is_part_time: bool
    :param is_pending_term: A boolean flag to represent if the Employee is pending term or not, defaults to 'False'
    :type is_pending_term: bool
    """
    POSITION_CHOICES = [
        ('', ''),
        ('driver', 'Driver'),
        ('mechanic', 'Mechanic'),
        ('utility', 'Utility'),
        ('dispatcher', 'Dispatcher'),
        ('dispatch_supervisor', 'Dispatch Supervisor'),
        ('driver_scheduler', 'Driver Scheduler'),
        ('hiring_supervisor', 'Hiring Supervisor'),
        ('road_supervisor', 'Road Supervisor'),
        ('operations_supervisor', 'Operations Supervisor'),
        ('clerk', 'Clerk'),
        ('drive_cam_manager', 'Drive Cam Manager'),
        ('safety_manager', 'Safety Manager'),
        ('operations_manager', 'Operations Manager'),
        ('maintenance_manager', 'Maintenance Manager'),
        ('it_manager', 'IT Manager'),
        ('agm', 'AGM'),
        ('gm', 'GM'),

    ]

    TERMINATION_CHOICES = [
        ('', ''),
        ('0', 'Voluntary'),
        ('1', 'Involuntary')
    ]

    is_active = models.BooleanField(default=True, verbose_name='Active')
    is_superuser = models.BooleanField(default=False, verbose_name='Superuser')
    is_staff = models.BooleanField(default=False, verbose_name='Staff')
    is_part_time = models.BooleanField(default=False, verbose_name='Part Time')
    is_neighbor_link = models.BooleanField(default=False, verbose_name='NeighborLink Driver')

    email_7attendance = models.BooleanField(default=True, verbose_name="7 Attendance Points",
                                            help_text='Receive an email when someone reaches 7 Attendance Points')
    email_10attendance = models.BooleanField(default=True, verbose_name="10 Attendance Points",
                                             help_text='Receive an email when someone reaches 10 Attendance Points')
    email_written = models.BooleanField(default=True, verbose_name='Written Warning',
                                        help_text='Receive an email when a written warning is issued')
    email_last_final = models.BooleanField(default=True, verbose_name='Last and Final',
                                           help_text='Receive an email when a last and final is issued')
    email_removal = models.BooleanField(default=True, verbose_name='Removal from Service',
                                        help_text='Receive an email when a removal from service is issued')
    email_safety_point = models.BooleanField(default=True, verbose_name='Safety Point',
                                             help_text='Receive an email when a Safety Point is issued')
    email_termination = models.BooleanField(default=True, verbose_name='Termination',
                                            help_text='Receive an email when an Employee is Terminated')
    email_add_hold = models.BooleanField(default=True, verbose_name='Placed on Hold',
                                         help_text='Receive an email when an Employee is placed on hold')
    email_rem_hold = models.BooleanField(default=True, verbose_name='Removed from Hold',
                                         help_text='Receive an email when a hold is removed from an Employee')
    email_add_settlement = models.BooleanField(default=True, verbose_name='Assign Settlement',
                                               help_text='Receive an email when a settlement is issued')
    email_new_time_off = models.BooleanField(default=True, verbose_name='New Time Off',
                                             help_text='Receive an email when time off is requested and the status is '
                                                       'pending')
    email_new_employee = models.BooleanField(default=True, verbose_name='New Employee',
                                             help_text='Receive an email when a new employee is added')
    email_attendance_doc_day5 = models.BooleanField(default=True, verbose_name='5 Days Past Due Attendance',
                                                    help_text='Receive an email when it has been 5 days since '
                                                              'an attendance point was given but not signed')
    email_attendance_doc_day7 = models.BooleanField(default=True, verbose_name='7 Days Past Due Attendance',
                                                    help_text='Receive an email when it has been 7 days since '
                                                              'an attendance point was given but not signed')
    email_attendance_doc_day10 = models.BooleanField(default=True, verbose_name='10 Days Past Due Attendance',
                                                     help_text='Receive an email when it has been 10 days since'
                                                               ' an attendance point was given but not signed')
    email_attendance_doc_day14 = models.BooleanField(default=True, verbose_name='3 Days Past Due Attendance',
                                                     help_text='Receive an email when it has been 14 or more days since'
                                                               ' an attendance point was given but not signed')
    email_safety_doc_day3 = models.BooleanField(default=True, verbose_name='3 Days Past Due Safety Point',
                                                help_text='Receive an email when it has been 3 days since '
                                                          'a safety point was given but a signed document '
                                                          'has not been uploaded')
    email_safety_doc_day5 = models.BooleanField(default=True, verbose_name='5 Days Past Due Safety Point',
                                                help_text='Receive an email when it has been 5 days since '
                                                          'a safety point was given but a signed document '
                                                          'has not been uploaded')
    email_safety_doc_day7 = models.BooleanField(default=True, verbose_name='7 Days Past Due Safety Point',
                                                help_text='Receive an email when it has been 7 days since '
                                                          'a safety point was given but a signed document '
                                                          'has not been uploaded')
    email_safety_doc_day10 = models.BooleanField(default=True, verbose_name='10 Days Past Due Safety Point',
                                                 help_text='Receive an email when it has been 10 or more days since '
                                                           'a safety point was given but a signed document '
                                                           'has not been uploaded')
    email_counseling_doc_day3 = models.BooleanField(default=True, verbose_name='3 Days Past Due Counseling',
                                                    help_text='Receive an email when it has been 3 days since '
                                                              'a counseling was given but a signed document '
                                                              'has not been uploaded')
    email_counseling_doc_day5 = models.BooleanField(default=True, verbose_name='5 Days Past Due Counseling',
                                                    help_text='Receive an email when it has been 5 days since '
                                                              'a counseling was given but a signed document '
                                                              'has not been uploaded')
    email_counseling_doc_day7 = models.BooleanField(default=True, verbose_name='7 Days Past Due Counseling',
                                                    help_text='Receive an email when it has been 7 days since '
                                                              'a counseling was given but a signed document '
                                                              'has not been uploaded')
    email_counseling_doc_day10 = models.BooleanField(default=True, verbose_name='10 Days Past Due Counseling',
                                                     help_text='Receive an email when it has been 10 or more days since'
                                                               ' a counseling was given but a signed document'
                                                               ' has not been uploaded')
    email_settlement_doc = models.BooleanField(default=True, verbose_name='Past Due Settlement',
                                               help_text='Receive an email when it has been 3 or more days since '
                                               'a settlement was created but a signed document '
                                               'has not been uploaded')

    employee_id = models.IntegerField(unique=True, null=True, verbose_name='Employee ID')
    primary_phone = PhoneNumberField(null=True, blank=True, verbose_name='Primary Phone Number')
    secondary_phone = PhoneNumberField(null=True, blank=True, verbose_name='Secondary Phone Number')
    paid_sick = models.IntegerField(default=0, verbose_name='Paid Sick')
    unpaid_sick = models.IntegerField(default=2, verbose_name='Unpaid Sick')
    floating_holiday = models.IntegerField(default=0, verbose_name='Floating Holiday')

    first_name = models.CharField(max_length=30, verbose_name='First Name')
    last_name = models.CharField(max_length=30, verbose_name='Last Name')
    username = models.CharField(max_length=30, unique=True, verbose_name='Username')
    position = models.CharField(max_length=30, choices=POSITION_CHOICES, verbose_name='Position')
    termination_type = models.CharField(max_length=30, choices=TERMINATION_CHOICES, null=True, blank=True,
                                        verbose_name='Termination Type')

    termination_comments = models.TextField(default='', verbose_name='Comments', blank=True)

    hire_date = models.DateField(null=True, verbose_name='Hire Date')
    application_date = models.DateField(null=True, verbose_name='Application Date')
    classroom_date = models.DateField(null=True, verbose_name='Classroom Date')
    removal_date = models.DateField(blank=True, null=True, verbose_name='Removal Date')
    termination_date = models.DateField(blank=True, null=True, verbose_name='Termination Date')

    email = models.EmailField(blank=True, null=True, verbose_name='Email')

    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, verbose_name='Company')

    profile_picture = ProcessedImageField(upload_to='profile_pictures',
                                          processors=[ResizeToFill(320, 320)],
                                          format='PNG',
                                          options={'quality': 60},
                                          blank=True)

    objects = EmployeeManager()

    USERNAME_FIELD = 'username'

    REQUIRED_FIELDS = ['first_name', 'last_name', 'employee_id']

    class Meta:
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'

        permissions = [

            # Employee's Views Permissions
            ('can_view_all_accounts', 'Can view all accounts'),
            ('can_edit_employee_info', 'Can edit employee information'),
            ('can_assign_attendance', 'Can assign attendance records'),
            ('can_delete_attendance', 'Can delete attendance records'),
            ('can_edit_attendance', 'Can edit attendance records'),
            ('can_download_attendance', 'Can download attendance records'),
            ('can_assign_counseling', 'Can assign counseling'),
            ('can_delete_counseling', 'Can delete counseling'),
            ('can_edit_counseling', 'Can edit counseling'),
            ('can_download_counseling', 'Can download counseling'),
            ('can_assign_safety_point', 'Can assign safety point'),
            ('can_delete_safety_point', 'Can delete safety point'),
            ('can_edit_safety_point', 'Can edit safety point'),
            ('can_download_safety_point', 'Can download safety point'),
            ('can_place_hold', 'Can place hold'),
            ('can_remove_hold', 'Can remove hold'),
            ('can_remove_employee', 'Can remove employee'),
            ('can_terminate_employee', 'Can remove employee'),
            ('can_export_profile', 'Can export profile'),
            ('can_export_attendance_history', 'Can export attendance history'),
            ('can_export_safety_history', 'Can export safety history'),
            ('can_export_counseling_history', 'Can export counseling history'),
            ('can_view_settlement', 'Can view settlement'),
            ('can_create_settlement', 'Can create settlement'),
            ('can_upload_profile_picture', 'Can upload profile picture'),
            ('can_view_all_details', 'Can view details in account'),
            ('can_view_attendance_details', 'Can view attendance details in account'),
            ('can_view_safety_details', 'Can view safety details in account'),
            ('can_view_counseling_details', 'Can view counseling details in account'),
            ('can_override_progressive_discipline_lock', 'Can override progressive discipline lock'),
            ('can_view_account_action_bar', 'Can view account action bar'),

            # Main's Views Permissions
            ('can_view_employee_info', 'Can view employee info'),
            ('can_export_safety_meeting_attendance', 'Can export safety meeting attendance list'),
            ('can_export_phone_list', 'Can export phone list'),
            ('can_export_seniority_list', 'Can export seniority list'),
            ('can_export_driver_list', 'Can export driver list'),
            ('can_export_main_custom_list', 'Can export main custom list'),
            ('can_view_import_data', 'Can view import data'),
            ('can_import_driver_data', 'Can import driver data'),
            ('can_import_attendance_data', 'Can import attendance data'),
            ('can_import_safety_point_data', 'Can import safety point data'),

            # Operation's Views Permissions
            ('can_view_operations_home', 'Can view operations home'),
            ('can_add_employee', 'Can add employee'),
            ('can_view_hold_list', 'Can view hold list'),
            ('can_view_attendance_reports', 'Can view attendance reports'),
            ('can_view_counseling_reports', 'Can view counseling reports'),
            ('can_add_time_off_request', 'Can add time off request'),
            ('can_delete_time_off_request', 'Can delete time off request'),
            ('can_view_time_off_reports', 'Can view time off reports'),
            ('can_view_termination_reports', 'Can view termination reports'),
        ]

    def get_last_warnings(self):
        """Returns the dates for the last written warning and removal from service"""
        counseling_history = Counseling.objects.filter(employee=self, is_active=True).exclude(attendance=None)

        written = None
        removal = None

        for counseling in counseling_history:
            try:
                written = counseling.issued_date if counseling.action_type == '2' and written is None else None
            except Counseling.DoesNotExist:
                pass

            try:
                removal = counseling.issued_date if counseling.action_type == '6' and removal is None else None
            except Counseling.DoesNotExist:
                pass

        return written, removal

    def get_attendance_history(self, incident_date):
        """Gets all the attendance records for a specific employee and returns a dictionary with the amounts of each
        record

        :param incident_date: Corresponds to the date of an incident to limit history
        :type datetime.datetime.date
        """

        attendance_records = Attendance.objects.filter(employee=self, is_active=True, incident_date__lte=incident_date)

        # This has been ordered to match the document
        history = {
            '0': 0,
            '6': 0,
            '7': 0,
            '2': 0,
            '4': 0,
            '5': 0,
            '3': 0,
        }

        # Goes through each of the past attendance points and adds +1 to the history ignoring '1'(Consecutive) and
        # treating '8'(Late Lunch) as '6'(< 15min). If it has any exception it won't count it
        for attendance_record in attendance_records:
            if not attendance_record.exemption:
                if attendance_record.reason != '1':
                    if attendance_record.reason == '8':
                        history['6'] += 1
                    else:
                        history[attendance_record.reason] += 1

        return history

    def get_full_name(self):
        """Returns Employees full name as 'first_name last_name'"""
        return f'{self.first_name} {self.last_name}'

    def get_position(self):
        """Returns pretty position"""
        pretty_position = self.position.replace('_', ' ')

        return pretty_position.title()

    def get_tenure(self):
        """Calculates the employees tenure in Years, Months, Weeks, Days and returns a string"""
        today = datetime.date.today()

        total_days = (today - self.hire_date).days
        years = int(total_days/365)
        months = int((total_days % 365) / 30.4167)
        weeks = int(((total_days % 365) % 30.4167) / 7)
        days = (total_days % 7)

        years_str = f'{years} Year' if years == 1 else f'{years} Years'
        months_str = f'{months} Month' if months == 1 else f'{months} Months'
        weeks_str = f'{weeks} Week' if weeks == 1 else f'{weeks} Weeks'
        days_str = f'{days} Day' if days == 1 else f'{days} Days'

        if years and months:
            tenure_str = f'{years_str} {months_str}'
        elif years:
            tenure_str = f'{years_str}'
        elif months and weeks:
            tenure_str = f'{months_str} {weeks_str}'
        elif months:
            tenure_str = f'{months_str}'
        elif weeks and days:
            tenure_str = f'{weeks_str} {days_str}'
        elif weeks:
            tenure_str = f'{weeks_str}'
        else:
            tenure_str = days_str

        return tenure_str

    def get_total_safety_points(self, exclude=None):
        """Gets all the Safety Point Objects for the employee and adds all the points then returns it. Optionally pass
        a Safety Point object to be excluded"""

        safety_points = SafetyPoint.objects.filter(employee=self, is_active=True)
        if exclude:
            safety_points = safety_points.exclude(pk=exclude.id)

        return sum([safety_point.points for safety_point in safety_points])

    def get_total_attendance_points(self, exclude=None):
        """Gets all the Attendance Objects for the employee and adds all the points then returns it. Optionally pass a
        Attendance object to be excluded"""
        attendance_records = Attendance.objects.filter(employee=self, is_active=True)

        if exclude:
            attendance_records.exclude(id=exclude.id)

        return sum([attendance_record.points for attendance_record in attendance_records])

    def get_introductory_status(self):
        """Checks if the Employee is still within their 90 days"""

        tenure = (datetime.date.today() - self.hire_date).days

        return False if tenure > 89 else True

    def has_attendance_in_6_months(self):
        attendance_records = Attendance.objects.filter(employee=self, incident_date__gte=timezone.now() - datetime.timedelta(days=180))

        if attendance_records:
            return True
        else:
            return False

    def safety_point_removal_required(self, instance):
        """Checks if the Employee needs to be removed from service based on SafetyPoint history and if so removes them

        Checks the total Safety Points of the Employee and sees if they have 6 or more total points or if they have 3
        separate SafetyPoint Objects. Depending on which one they satisfy it will create the Counseling required, if it
        creates the Counseling it will return True else return False
        """

        try:
            instance.counseling.delete()
        except Counseling.DoesNotExist:
            pass

        total_points = self.get_total_safety_points()
        introductory_status = self.get_introductory_status()
        if introductory_status:
            if total_points > 3:
                conduct = f'The driver has met/exceeded the number of allotted safety points within the' \
                          f' introductory period with a total of {total_points} points. According to the Employee' \
                          f' Handbook \"For introductory period employees: Receipt of four (4) or more points during' \
                          f' the introductory period will result in termination.\"'
                conversation = 'The driver has been explained the importance of making Safety their top priority,' \
                               ' driving with continuous unsafe behaviors is intolerable.'

                counseling = Counseling(
                    employee=self,
                    assigned_by=instance.assigned_by,
                    issued_date=datetime.date.today(),
                    action_type='6',
                    conduct=conduct,
                    conversation=conversation,
                    safety_point=instance
                )

                counseling.save()

                return True
            else:
                safety_points = SafetyPoint.objects.filter(is_active=True, employee=self)
                if len(safety_points) > 1:
                    conduct = f'The driver has met/exceeded the number of allotted safety point assessments within' \
                              f' the introductory period. According to the Employee Handbook \"... receipt of 2' \
                              f' separate safety point assessments during the introductory period will result in' \
                              f' termination, regardless of the employees\'s total point count.\"'
                    conversation = 'The driver has been explained the importance of making Safety their top priority,' \
                                   ' driving with continuous unsafe behaviors is intolerable.'

                    counseling = Counseling(
                        employee=self,
                        assigned_by=instance.assigned_by,
                        issued_date=datetime.date.today(),
                        action_type='6',
                        conduct=conduct,
                        conversation=conversation,
                        safety_point=instance
                    )

                    counseling.save()

                    return True
                else:
                    return False
        else:
            if total_points > 5:
                conduct = f'The driver has met/exceeded the number of allotted safety points within a rolling 18 month' \
                          f' period with a total of {total_points} points. According to the Employee Handbook \"For' \
                          f' non-introductory period employees: In any rolling 18 month period of employment, receipt of' \
                          f' six (6) or more points will result in termination.\" '
                conversation = 'The driver has been explained the importance of making Safety their top priority,' \
                               ' driving with continuous unsafe behaviors is intolerable.'

                counseling = Counseling(
                    employee=self,
                    assigned_by=instance.assigned_by,
                    issued_date=datetime.date.today(),
                    action_type='6',
                    conduct=conduct,
                    conversation=conversation,
                    safety_point=instance
                )

                counseling.save()

                return True
            else:
                safety_points = SafetyPoint.objects.filter(is_active=True, employee=self)
                if len(safety_points) > 2:
                    conduct = f'The driver has met/exceeded the number of allotted safety point assessments within a' \
                              f' rolling one year period. According to the Employee Handbook \"... receipt of 3 separate' \
                              f' safety point assessments in any rolling one year period will result in termination,' \
                              f' regardless of the employees\'s total point count.\"'
                    conversation = 'The driver has been explained the importance of making Safety their top priority,' \
                                   ' driving with continuous unsafe behaviors is intolerable.'

                    counseling = Counseling(
                        employee=self,
                        assigned_by=instance.assigned_by,
                        issued_date=datetime.date.today(),
                        action_type='6',
                        conduct=conduct,
                        conversation=conversation,
                        safety_point=instance
                    )

                    counseling.save()

                    return True
                else:
                    return False

    def attendance_counseling_required(self, reason, exemption, current_id=None):
        """A function to decide if counseling is required based on employees attendance history and the attendance
        they will receive now. It queries for all the Attendance objects that belong to the Employee ,if a current_id is
        passed it will exclude that Attendance object, sums all the points and see if they need counseling and which
        type of counseling.

        :param reason: A string representing the reason code of the current attendance they are receiving
        :type reason: str
        :param exemption: A string representing the exemption code of the current attendance they are receiving
        :type exemption: str
        :param current_id: An id for an Attendance object to exclude
        :type current_id: int, optional

        :return: A list containing the information for counseling. Index 0 is an int 0, 1, or 2 depending if no counseling, written, or removal from service respectively, index 1 is datetime object for any past counseling, index 2 is datetime object for counseling being issued
        :rtype: list
        """

        points = {
            '0': 1,
            '1': 0,
            '2': 1.5,
            '3': 4,
            '4': 1,
            '5': 1,
            '6': .5,
            '7': 1,
            '8': .5,
        }
        previous_counseling = {}

        for record in Counseling.objects.filter(employee=self, is_active=True):
            if record.attendance:
                previous_counseling[record.action_type] = record.issued_date

        point = points[reason] if exemption == '' else 0
        total_points = float(sum([record.points for record in
                                  Attendance.objects.filter(employee=self, is_active=True).exclude(
                                      id=current_id)])) + point

        # '2' Represents Written Warning
        if '2' in previous_counseling.keys() and total_points >= 10:
            counseling = [2, previous_counseling['2'], datetime.datetime.today()]
        elif '2' not in previous_counseling.keys() and total_points >= 7:
            counseling = [1, None, datetime.datetime.today()]
        elif '2' in previous_counseling.keys():
            counseling = [0, previous_counseling['2'], None]
        else:
            counseling = [0, None, None]

        return counseling

    def attendance_written(self, counseling, attendance, assigned_by):
        """Will create a Counseling for the Employee for a Written Warning"""

        conduct = 'You have reached the maximum allowable attendance points according to MV Transportation\'s' \
                  ' Employee Handbook which cause a Written Warning to be issued.'
        conversation = 'According to the Employee Handbook, Employee\'s are allowed a maximum of seven (7)' \
                       ' occurrences within a rolling 12 month period before a Written Warning is issued. If an' \
                       ' employee goes "occurrence free" for a consecutive six (6) month period, his/her' \
                       ' attendance record will be wiped clean and any prior points will not be considered as' \
                       ' a basis for disciplinary action. This documents is considered to be your Written' \
                       ' Warning Notice.'
        new_counseling = Counseling(
            employee=self,
            assigned_by=assigned_by,
            issued_date=counseling[2],
            action_type='2',
            hearing_datetime=None,
            conduct=conduct,
            conversation=conversation
        )

        new_counseling.attendance = attendance
        new_counseling.save()

    def attendance_removal(self, counseling, attendance, assigned_by):
        """Will create a Counseling for the Employee for a Removal from Service"""
        conduct = 'You have exceeded the maximum allowable attendance points according to MV Transportation\'s' \
                  ' Employee Handbook.'
        conversation = 'According to the Employee Handbook, Employee\'s are allowed a maximum of seven (7)' \
                       ' occurrences within a rolling 12 month period before a written warning is issued. If' \
                       ' an Employee reaches ten (10) occurrences within a rolling 12 month period, he/she' \
                       ' will be terminated. You have been removed from service pending possible termination' \
                       ' of employment. Management will contact you on a later date to attend a Fair &' \
                       ' Impartial Hearing.'

        new_counseling = Counseling(
            employee=self,
            assigned_by=assigned_by,
            issued_date=counseling[2],
            action_type='6',
            hearing_datetime=None,
            conduct=conduct,
            conversation=conversation
        )

        new_counseling.attendance = attendance
        new_counseling.save()

    def create_attendance_history_document(self):
        """Gets all the active Attendance Objects for the Employee and merges all documents into one and make a summary
        page for the beginning
        """
        attendance_history = Attendance.objects.filter(employee=self, is_active=True).order_by('-id')
        if attendance_history:
            buffer = io.BytesIO()

            merged_object = PdfFileMerger()
            cover_buffer = io.BytesIO()

            reasons = {
                '0': 'Unexcused',
                '1': 'Consecutive',
                '2': '< 1 HR',
                '3': 'NCNS',
                '4': 'FTC',
                '5': 'Missing Safety Meeting',
                '6': '< 15 MIN',
                '7': '> 15 MIN',
                '8': 'Late Lunch',
            }

            exemptions = {
                '0': 'FMLA',
                '1': 'Paid Sick',
                '2': 'Unpaid Sick',
                '3': 'Union Agreement',
                '4': 'Excused Absence',
            }

            p = canvas.Canvas(cover_buffer, pagesize=letter)

            p.setLineWidth(.75)

            # Title
            title = f"{self.get_full_name()}'s Attendance History"
            p.setFontSize(18)
            p.drawCentredString(4.25 * inch, 10 * inch, title)

            # Written Warning and Removal
            p.setFontSize(12)
            p.drawString(.5 * inch, 9.5 * inch, 'Written Warning Issued:')
            p.drawString(.5 * inch, 9.0 * inch, 'Removal From Service Issued:')

            p.line(2.4 * inch, 9.5 * inch, 3.95 * inch, 9.5 * inch)
            p.line(2.9 * inch, 9.0 * inch, 4.05 * inch, 9.0 * inch)

            written, removal = self.get_last_warnings()

            if written:
                p.drawString(2.42 * inch, 9.53 * inch, written.strftime('%m-%d-%Y'))
            if removal:
                p.drawString(2.92 * inch, 9.03 * inch, removal.strftime('%m-%d-%Y'))

            total_pages = int(len(attendance_history) / 30) + 1
            page_num = 1
            y = 8.25

            counter = 1

            # Adding attendance history to the cover page and setting the written warning removal dates
            for attendance in attendance_history:
                y = 9.75 if page_num > 1 else y
                p.setFont('Helvetica', 10)

                incident_date = attendance.incident_date.strftime('%m-%d-%Y') if attendance.incident_date else ''
                issued_date = attendance.issued_date.strftime('%m-%d-%Y') if attendance.issued_date else 'Not Issued'
                exemption = exemptions[attendance.exemption] if attendance.exemption else 'None'
                point = str(int(attendance.points)) if float(attendance.points).is_integer() else str(attendance.points)

                p.drawString(0.75 * inch, y * inch, incident_date)
                p.drawString(1.75 * inch, y * inch, issued_date)
                p.drawString(2.75 * inch, y * inch, reasons[attendance.reason])
                p.drawString(4.45 * inch, y * inch, point)
                p.drawString(5.15 * inch, y * inch, attendance.get_assignee().get_full_name())
                p.drawString(6.75 * inch, y * inch, exemption)
                p.line(0.65 * inch, (y - .1) * inch, 7.85 * inch, (y - .1) * inch)  # Bottom

                if y == 1 or len(attendance_history) == counter:
                    p.setFont('Helvetica-Bold', 10)

                    grid_bottom = y - .1
                    y = 10.00 if page_num > 1 else 8.5

                    # Heading
                    p.drawString(0.75 * inch, y * inch, 'Incident Date')
                    p.drawString(1.75 * inch, y * inch, 'Issued Date')
                    p.drawString(2.75 * inch, y * inch, 'Reason')
                    p.drawString(4.45 * inch, y * inch, 'Points')
                    p.drawString(5.15 * inch, y * inch, 'Assigned By')
                    p.drawString(6.75 * inch, y * inch, 'Exemption')

                    # Footer
                    p.drawString(1 * inch, .5 * inch, datetime.datetime.today().strftime('%A, %B %d, %Y'))
                    p.drawRightString(7.5 * inch, .5 * inch, f'Page {page_num} of {total_pages}')

                    # Grid
                    p.line(0.65 * inch, (y - .07) * inch, 7.85 * inch, (y - .07) * inch)  # Top
                    p.line(0.65 * inch, (y - .07) * inch, 0.65 * inch, grid_bottom * inch)  # Left
                    p.line(7.85 * inch, (y - .07) * inch, 7.85 * inch, grid_bottom * inch)  # Right
                    p.line(1.65 * inch, (y - .07) * inch, 1.65 * inch, grid_bottom * inch)  # Vertical 1
                    p.line(2.65 * inch, (y - .07) * inch, 2.65 * inch, grid_bottom * inch)  # Vertical 2
                    p.line(4.35 * inch, (y - .07) * inch, 4.35 * inch, grid_bottom * inch)  # Vertical 3
                    p.line(5.05 * inch, (y - .07) * inch, 5.05 * inch, grid_bottom * inch)  # Vertical 4
                    p.line(6.65 * inch, (y - .07) * inch, 6.65 * inch, grid_bottom * inch)  # Vertical 5

                    p.showPage()

                    page_num += 1

                counter += 1
                y -= .25

            p.save()

            merged_object.append(PdfFileReader(ContentFile(cover_buffer.getbuffer())))

            for attendance in attendance_history:
                remote_file = requests.get(attendance.document.url).content
                memory_file = io.BytesIO(remote_file)
                merged_object.append(PdfFileReader(memory_file))

            merged_object.write(buffer)

            return ContentFile(buffer.getbuffer())
        else:
            return None

    def create_counseling_history_document(self):
        """Gets all the active Counseling Objects for the Employee and merges all documents into one and make a summary
        page for the beginning
        """
        counseling_history = Counseling.objects.filter(employee=self, is_active=True).order_by('-id')
        if counseling_history:
            buffer = io.BytesIO()

            merged_object = PdfFileMerger()
            cover_buffer = io.BytesIO()

            action_types = {
                '0': 'Verbal Counseling',
                '1': 'Verbal Warning',
                '2': 'First Written Warning Notice',
                '3': 'Final Written Warning Notice & 3 Day Suspension',
                '4': 'Last & Final Warning',
                '5': 'Discharge for \"Just Cause\"',
                '6': 'Administrative Removal from Service',
            }

            p = canvas.Canvas(cover_buffer, pagesize=letter)

            p.setLineWidth(.75)

            # Title
            title = f"{self.get_full_name()}'s Counseling History"
            p.setFontSize(18)
            p.drawCentredString(4.25 * inch, 10 * inch, title)

            total_pages = int(len(counseling_history) / 30) + 1
            page_num = 1
            y = 9.25

            counter = 1

            # Adding counseling history to the cover page and setting the written warning removal dates
            for counseling in counseling_history:
                p.setFont('Helvetica', 10)

                p.drawString(1.50 * inch, y * inch, counseling.issued_date.strftime('%m-%d-%Y'))
                p.drawString(3.00 * inch, y * inch, action_types[counseling.action_type])
                p.drawString(5.40 * inch, y * inch, counseling.get_assignee().get_full_name())
                p.line(1.40 * inch, (y - .1) * inch, 7.10 * inch, (y - .1) * inch)  # Bottom

                if y == 1 or len(counseling_history) == counter:
                    p.setFont('Helvetica-Bold', 10)

                    grid_bottom = y - .1
                    y = 9.50

                    # Heading
                    p.drawString(1.50 * inch, y * inch, 'Issued Date')
                    p.drawString(3.00 * inch, y * inch, 'Action Type')
                    p.drawString(5.40 * inch, y * inch, 'Assigned By')

                    # Footer
                    p.drawString(1 * inch, .5 * inch, datetime.datetime.today().strftime('%A, %B %d, %Y'))
                    p.drawRightString(7.5 * inch, .5 * inch, f'Page {page_num} of {total_pages}')

                    # Grid
                    p.line(1.40 * inch, (y - .07) * inch, 7.10 * inch, (y - .07) * inch)  # Top
                    p.line(1.40 * inch, (y - .07) * inch, 1.40 * inch, grid_bottom * inch)  # Left
                    p.line(7.10 * inch, (y - .07) * inch, 7.10 * inch, grid_bottom * inch)  # Right
                    p.line(2.90 * inch, (y - .07) * inch, 2.90 * inch, grid_bottom * inch)  # Vertical 1
                    p.line(5.30 * inch, (y - .07) * inch, 5.30 * inch, grid_bottom * inch)  # Vertical 2

                    p.showPage()

                    page_num += 1

                counter += 1
                y -= .25

            p.save()

            merged_object.append(PdfFileReader(ContentFile(cover_buffer.getbuffer())))

            for counseling in counseling_history:
                remote_file = requests.get(counseling.document.url).content
                memory_file = io.BytesIO(remote_file)
                merged_object.append(PdfFileReader(memory_file))

            merged_object.write(buffer)

            return ContentFile(buffer.getbuffer())
        else:
            return None

    def create_safety_point_history_document(self):
        """Gets all the active Counseling Objects for the Employee and merges all documents into one and make a summary
        page for the beginning
        """
        safety_point_history = SafetyPoint.objects.filter(employee=self, is_active=True).order_by('-id')

        if safety_point_history:
            buffer = io.BytesIO()

            merged_object = PdfFileMerger()
            cover_buffer = io.BytesIO()

            reason_choices = {
                '0': 'Unsafe maneuver(s) or act',
                '1': 'Failure to cycle wheelchair lift',
                '2': 'Failure to do a proper vehicle inspection (DVI)',
                '3': 'Improper following distance',
                '4': 'Conviction of a minor traffic violation',
                '5': 'Backing Accident',
                '6': 'Minor Preventable incident',
                '7': 'Use of a non company-issued electronic device',
                '8': 'Major preventable incident',
                '9': 'Major preventable incident',
                '10': 'Any preventable roll-away incident',
                '11': 'Failure to properly secure/transport a mobility device',
                '12': 'Failure to immediately report a citation or incident',
                '13': 'Tampering with with Drive Cam or other monitoring equipment',
                '14': 'Conviction of a major traffic violation'
            }

            p = canvas.Canvas(cover_buffer, pagesize=letter)

            p.setLineWidth(.75)

            # Title
            title = f"{self.get_full_name()}'s Safety Point History"
            p.setFontSize(18)
            p.drawCentredString(4.25 * inch, 10 * inch, title)

            total_pages = int(len(safety_point_history) / 30) + 1
            page_num = 1
            y = 9.25

            counter = 1

            # Adding counseling history to the cover page and setting the written warning removal dates
            for safety_point in safety_point_history:
                p.setFont('Helvetica', 10)

                p.drawString(1.00 * inch, y * inch, safety_point.issued_date.strftime('%m-%d-%Y'))
                p.drawString(2.00 * inch, y * inch, reason_choices[safety_point.reason])
                p.drawString(6.00 * inch, y * inch, safety_point.get_assignee().get_full_name())
                p.line(0.90 * inch, (y - .1) * inch, 7.60 * inch, (y - .1) * inch)  # Bottom

                if y == 1 or len(safety_point_history) == counter:
                    p.setFont('Helvetica-Bold', 10)

                    grid_bottom = y - .1
                    y = 9.50

                    # Heading
                    p.drawString(1.00 * inch, y * inch, 'Issued Date')
                    p.drawString(2.00 * inch, y * inch, 'Action Type')
                    p.drawString(6.00 * inch, y * inch, 'Assigned By')

                    # Footer
                    p.drawString(1 * inch, .5 * inch, datetime.datetime.today().strftime('%A, %B %d, %Y'))
                    p.drawRightString(7.5 * inch, .5 * inch, f'Page {page_num} of {total_pages}')

                    # Grid
                    p.line(0.90 * inch, (y - .07) * inch, 7.60 * inch, (y - .07) * inch)  # Top
                    p.line(0.90 * inch, (y - .07) * inch, 0.90 * inch, grid_bottom * inch)  # Left
                    p.line(7.60 * inch, (y - .07) * inch, 7.60 * inch, grid_bottom * inch)  # Right
                    p.line(1.90 * inch, (y - .07) * inch, 1.90 * inch, grid_bottom * inch)  # Vertical 1
                    p.line(5.90 * inch, (y - .07) * inch, 5.90 * inch, grid_bottom * inch)  # Vertical 2

                    p.showPage()

                    page_num += 1

                counter += 1
                y -= .25

            p.save()

            merged_object.append(PdfFileReader(ContentFile(cover_buffer.getbuffer())))

            for safety_point in safety_point_history:
                remote_file = requests.get(safety_point.document.url).content
                memory_file = io.BytesIO(remote_file)
                merged_object.append(PdfFileReader(memory_file))

            merged_object.write(buffer)

            return ContentFile(buffer.getbuffer())
        else:
            return None

    def create_profile_history_document(self):
        buffer = io.BytesIO()

        merged_object = PdfFileMerger()
        cover_buffer = io.BytesIO()

        p = canvas.Canvas(cover_buffer, pagesize=letter)

        p.setLineWidth(.75)

        # Profile Picture
        if self.profile_picture:
            absolute_url = self.profile_picture.url
        else:
            profile_picture_url = 'main/blank-profile-picture.png'
            absolute_url = urljoin(settings.STATIC_URL, profile_picture_url)  # Removing the first /

        profile_picture = ImageReader(absolute_url)
        p.drawImage(profile_picture, 1 * inch, 8.5 * inch, 2 * inch, 2 * inch, mask='auto')

        # Name & ID
        title = f"{self.get_full_name()}"
        p.setFontSize(18)
        p.drawString(3.25 * inch, 10 * inch, title)

        p.setFontSize(12)
        p.setFillColor('gray')
        employee_id = str(self.employee_id)
        p.drawString(3.25 * inch, 9.85 * inch, employee_id)

        p.setFontSize(14)
        p.setFillColor('black')

        # General Information
        primary_phone = f'{self.primary_phone.as_e164[:-10]}({self.primary_phone.as_e164[-10:-7]}) {self.primary_phone.as_e164[-7:-4]}-{self.primary_phone.as_e164[-4:]}' if self.primary_phone else ''
        secondary_phone = f'{self.secondary_phone.as_e164[:-10]}({self.secondary_phone.as_e164[-10:-7]}) {self.secondary_phone.as_e164[-7:-4]}-{self.secondary_phone.as_e164[-4:]}' if self.secondary_phone else ''
        email = self.email
        hire_date = self.hire_date.strftime('%m-%d-%Y')
        company = self.company.display_name
        position = self.get_position()

        p.drawString(1 * inch, 7.0 * inch, f'Primary Phone Number: {primary_phone}')
        p.drawString(1 * inch, 6.5 * inch, f'Secondary Phone Number: {secondary_phone}')
        p.drawString(1 * inch, 6.0 * inch, f'Email: {email}')
        p.drawString(1 * inch, 5.5 * inch, f'Hire Date: {hire_date}')
        p.drawString(1 * inch, 5.0 * inch, f'Company: {company}')
        p.drawString(1 * inch, 4.5 * inch, f'Position: {position}')

        p.showPage()
        p.save()

        merged_object.append(PdfFileReader(ContentFile(cover_buffer.getbuffer())))
        attendance_history = self.create_attendance_history_document()
        counseling_history = self.create_counseling_history_document()
        safety_point_history = self.create_safety_point_history_document()

        if attendance_history:
            merged_object.append(PdfFileReader(attendance_history))
        if counseling_history:
            merged_object.append(PdfFileReader(counseling_history))
        if safety_point_history:
            merged_object.append(PdfFileReader(safety_point_history))

        merged_object.write(buffer)

        return ContentFile(buffer.getbuffer())

    def __str__(self):
        return f'{self.last_name}, {self.first_name}'


def wrap_text(string, font_name, font_size, wrapping_amount):
    words = string.split(' ')
    str_list = []
    current_words = []
    index = 0

    while index < len(words):
        current_words.append(words[index])
        wrapped_str = ' '.join(current_words)

        if stringWidth(wrapped_str, font_name, font_size) >= wrapping_amount and index != len(words):
            wrapped_str = ' '.join(current_words[:-1])
            current_words = []
            str_list.append(wrapped_str)
        elif stringWidth(wrapped_str, font_name, font_size) <= wrapping_amount and index == (len(words) - 1):
            str_list.append(wrapped_str)
            index += 1
        else:
            index += 1

    return str_list


class Attendance(models.Model):
    REASON_CHOICES = [
        ('', ''),
        ('0', 'Unexcused'),
        ('1', 'Consecutive'),
        ('2', '< 1 HR'),
        ('3', 'NCNS'),
        ('4', 'FTC'),
        ('5', 'Missing Safety Meeting'),
        ('6', '< 15 MIN'),
        ('7', '> 15 MIN'),
        ('8', 'Late Lunch'),
    ]

    EXEMPTION_CHOICES = [
        ('', ''),
        ('0', 'FMLA'),
        ('1', 'Paid Sick'),
        ('2', 'Unpaid Sick'),
        ('3', 'Union Agreement'),
        ('4', 'Excused Absence'),
        ('5', 'Attendance Incentive'),
    ]

    is_active = models.BooleanField(default=True)

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    incident_date = models.DateField()
    issued_date = models.DateField(null=True)
    points = models.DecimalField(max_digits=2, decimal_places=1)
    document = models.FileField(validators=[pdf_extension], upload_to='attendance_forms')
    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    assigned_by = models.CharField(max_length=50)
    exemption = models.CharField(max_length=30, choices=EXEMPTION_CHOICES, blank=True, null=True)
    edited_date = models.DateField(null=True, blank=True)
    edited_by = models.CharField(max_length=30, blank=True, default='')
    uploaded = models.BooleanField(default=False)

    def create_document(self):
        """Will create a PDF for the Attendance and assign it to the Attendance Object"""
        buffer = io.BytesIO()

        p = canvas.Canvas(buffer, pagesize=letter)

        p.setLineWidth(.75)

        history = self.employee.get_attendance_history(self.incident_date)
        counseling = self.employee.attendance_counseling_required(reason=self.reason, exemption=self.exemption,
                                                                  current_id=self.id)

        # Title
        title = 'Employee Attendance Report'
        p.setFontSize(18)
        p.drawCentredString(4.25 * inch, 10.5 * inch, title)

        # Name & Division
        p.setFontSize(12)
        p.drawString(.5 * inch, 10 * inch, 'Employee Name:')
        p.drawString(1.92 * inch, 10.03 * inch, self.employee.get_full_name())

        p.line(1.9 * inch, 10 * inch, 4 * inch, 10 * inch)

        p.drawString(6.8 * inch, 10 * inch, 'Division #: 12')

        # Date, Reason
        reasons = {
            '0': 'Unexcused',
            '1': 'Consecutive',
            '2': '< 1 HR',
            '3': 'NCNS',
            '4': 'FTC',
            '5': 'Missing Safety Meeting',
            '6': '< 15 MIN',
            '7': '> 15 MIN',
            '8': 'Late Lunch',
        }

        exemptions = {
            '0': 'FMLA',
            '1': 'Paid Sick',
            '2': 'Unpaid Sick',
            '3': 'Union Agreement',
            '4': 'Excused Absence',
            '5': 'Attendance Incentive',
        }

        p.setFontSize(12)
        p.drawString(.5 * inch, 9.5 * inch, 'Incident Date:')
        p.drawString(1.62 * inch, 9.53 * inch, self.incident_date.strftime('%m-%d-%Y'))

        p.line(1.6 * inch, 9.5 * inch, 2.75 * inch, 9.5 * inch)

        p.drawString(2.85 * inch, 9.5 * inch, 'Reason:')
        p.drawString(3.57 * inch, 9.53 * inch, reasons[self.reason])

        p.line(3.57 * inch, 9.5 * inch, 5.40 * inch, 9.5 * inch)

        p.drawString(5.50 * inch, 9.5 * inch, 'Exemption:')
        if self.exemption:
            p.drawString(6.42 * inch, 9.52 * inch, exemptions[self.exemption])

        p.line(6.42 * inch, 9.5 * inch, 8 * inch, 9.5 * inch)

        # Occurrences & Warnings
        points = {
            '0': 1,
            '1': 0,
            '2': 1.5,
            '3': 4,
            '4': 1,
            '5': 1,
            '6': .5,
            '7': 1,
            '8': .5,
        }
        if not self.exemption:
            p.drawString(.5 * inch, 8.75 * inch, 'Occurrences for this Violation: ' + str(points[self.reason]))
        else:
            p.drawString(.5 * inch, 8.75 * inch, 'Occurrences for this Violation: 0')

        if counseling[0] == 2:
            warning = 'Warning Issued on: ' + counseling[1].strftime('%m-%d-%Y')
            final = 'Final Warning Issued on: ' + counseling[2].strftime('%m-%d-%Y')
        elif counseling[0] == 1:
            warning = 'Warning Issued on: ' + counseling[2].strftime('%m-%d-%Y')
            final = 'Final Warning Issued on:'
        elif counseling[0] == 0:
            if counseling[1]:
                warning = 'Warning Issued on: ' + counseling[1].strftime('%m-%d-%Y')
            else:
                warning = 'Warning Issued on:'
            final = 'Final Warning Issued on:'
        else:
            warning = 'Warning Issued on:'
            final = 'Final Warning Issued on:'

        p.drawString(.5 * inch, 8.50 * inch, warning)
        p.drawString(.5 * inch, 8.25 * inch, final)

        # Reported By
        p.drawString(.5 * inch, 7.75 * inch, 'Reported By:')
        p.drawString(1.57 * inch, 7.78 * inch, self.get_assignee().get_full_name())

        p.line(1.55 * inch, 7.75 * inch, 3 * inch, 7.75 * inch)

        # Section 2 Start

        p.line(.5 * inch, 7.25 * inch, 8 * inch, 7.25 * inch)

        # History Grid
        p.setFontSize(8)
        p.drawRightString(2 * inch, 6.35 * inch, 'Unexcused Absence')
        p.drawRightString(2 * inch, 6.05 * inch, 'Tardy less than 15 min.')
        p.drawRightString(2 * inch, 5.75 * inch, 'Tardy more than 15 min.')
        p.drawRightString(2 * inch, 5.50 * inch, 'Called in less than 1 hr.')
        p.drawRightString(2 * inch, 5.40 * inch, 'prior to start of shift')
        p.drawRightString(2 * inch, 5.15 * inch, 'Failure to complete shift')
        p.drawRightString(2 * inch, 4.85 * inch, 'Missed required meeting')
        p.drawRightString(2 * inch, 4.55 * inch, 'No Call/No Show')
        p.drawCentredString(2.4 * inch, 6.75 * inch, 'Times')
        p.drawCentredString(2.4 * inch, 6.6 * inch, 'Occurred')

        # Left Box outer lines
        p.line(2.1 * inch, 6.55 * inch, 2.1 * inch, 4.45 * inch)  # Left Vertical
        p.line(2.7 * inch, 6.55 * inch, 2.7 * inch, 4.45 * inch)  # Right Vertical
        p.line(2.1 * inch, 6.55 * inch, 2.7 * inch, 6.55 * inch)  # Top Horizontal
        p.line(2.1 * inch, 4.45 * inch, 2.7 * inch, 4.45 * inch)  # Bottom Horizontal

        # Left Box Inner Horizontals Top to Bottom
        p.line(2.1 * inch, 6.25 * inch, 2.7 * inch, 6.25 * inch)
        p.line(2.1 * inch, 5.95 * inch, 2.7 * inch, 5.95 * inch)
        p.line(2.1 * inch, 5.65 * inch, 2.7 * inch, 5.65 * inch)
        p.line(2.1 * inch, 5.35 * inch, 2.7 * inch, 5.35 * inch)
        p.line(2.1 * inch, 5.05 * inch, 2.7 * inch, 5.05 * inch)
        p.line(2.1 * inch, 4.75 * inch, 2.7 * inch, 4.75 * inch)

        # Occurrences Grid
        p.setFontSize(8)
        p.drawString(5 * inch, 6.35 * inch, 'Each Unexcused absence equals 1 Occurrence')
        p.drawString(5 * inch, 6.05 * inch, 'Each Tardy less than 15 min equals 1/2 Occurrence')
        p.drawString(5 * inch, 5.75 * inch, 'Each Tardy more than 15 min equals 1 Occurrence')
        p.drawString(5 * inch, 5.45 * inch, 'Each violation equals 1 1/12 Occurrence')
        p.drawString(5 * inch, 5.15 * inch, 'Each Failure to Complete Shift equals 1 Occurrence')
        p.drawString(5 * inch, 4.85 * inch, 'Each violation equals 1 occurrence')
        p.drawString(5 * inch, 4.55 * inch, 'Each No Call/No Show equals 4 Occurrences')
        p.drawCentredString(4.4 * inch, 6.75 * inch, 'Total')
        p.drawCentredString(4.4 * inch, 6.6 * inch, 'Occurrences')
        p.drawString(5 * inch, 6.6 * inch, 'NOTES:')
        p.drawRightString(4 * inch, 4.25 * inch, 'TOTAL OCCURRENCES')

        # Right Box outer lines
        p.line(4.1 * inch, 6.55 * inch, 4.1 * inch, 4.15 * inch)  # Left Vertical
        p.line(4.7 * inch, 6.55 * inch, 4.7 * inch, 4.15 * inch)  # Right Vertical
        p.line(4.1 * inch, 6.55 * inch, 4.7 * inch, 6.55 * inch)  # Top Horizontal
        p.line(4.1 * inch, 4.15 * inch, 4.7 * inch, 4.15 * inch)  # Bottom Horizontal

        # Right Box Inner Horizontals Top to Bottom
        p.line(4.1 * inch, 6.25 * inch, 4.7 * inch, 6.25 * inch)
        p.line(4.1 * inch, 5.95 * inch, 4.7 * inch, 5.95 * inch)
        p.line(4.1 * inch, 5.65 * inch, 4.7 * inch, 5.65 * inch)
        p.line(4.1 * inch, 5.35 * inch, 4.7 * inch, 5.35 * inch)
        p.line(4.1 * inch, 5.05 * inch, 4.7 * inch, 5.05 * inch)
        p.line(4.1 * inch, 4.75 * inch, 4.7 * inch, 4.75 * inch)
        p.line(4.1 * inch, 4.45 * inch, 4.7 * inch, 4.45 * inch)

        # Left Box Contents
        p.setFontSize(12)
        y = 6.35
        for value in history.values():
            if value:
                p.drawCentredString(2.4 * inch, y * inch, str(value))
            y -= .3

        # Right Box Contents
        occurrences_amounts = {
            '0': 1,
            '6': .5,
            '7': 1,
            '2': 1.5,
            '4': 1,
            '5': 1,
            '3': 4,
        }
        p.setFontSize(12)
        y = 6.35
        total = 0
        for key, value in history.items():
            occurrence_total = value * occurrences_amounts[key]

            if float(occurrence_total).is_integer():
                p.drawCentredString(4.4 * inch, y * inch, str(int(occurrence_total)))
            else:
                p.drawCentredString(4.4 * inch, y * inch, str(occurrence_total))
            y -= .3
            total += occurrence_total

        if float(total).is_integer():
            p.drawCentredString(4.4 * inch, y * inch, str(int(total)))
        else:
            p.drawCentredString(4.4 * inch, y * inch, str(total))

        # Disclaimer
        disclaimer1 = 'The intent of this report is to advise you of your current attendance occurences per the MV Attendance Policy. You are allowed a maximum of seven'
        disclaimer2 = '"occurrences" within a floating 12 month period before a written warning is issued and disciplinary actions begin. Ten(10) occurrences will result'
        disclaimer3 = 'in termination. Six consecutive months of perfect attendance, meaning no occurences, will wipe your record clean and give you a fresh start.'
        disclaimer4 = 'Please see the Employee Handbook for more information.'

        p.setFontSize(8)
        p.drawString(.5 * inch, 3 * inch, disclaimer1)
        p.drawString(.5 * inch, 2.8 * inch, disclaimer2)
        p.drawString(.5 * inch, 2.6 * inch, disclaimer3)
        p.drawString(.5 * inch, 2.4 * inch, disclaimer4)

        # Comments
        p.setFontSize(12)
        p.drawString(.5 * inch, 2.1 * inch, 'Comments:')

        p.line(.5 * inch, 1.8 * inch, 8 * inch, 1.8 * inch)
        p.line(.5 * inch, 1.5 * inch, 8 * inch, 1.5 * inch)

        # Signatures & Date
        p.setFontSize(12)
        p.drawString(.5 * inch, 1 * inch, 'Employee Signature:')
        p.drawString(5.75 * inch, 1 * inch, 'Date:')
        p.drawString(.5 * inch, .5 * inch, 'Supervisor Signature:')
        p.drawString(5.75 * inch, .5 * inch, 'Date:')

        p.line(2.2 * inch, .5 * inch, 5.5 * inch, .5 * inch)
        p.line(2.2 * inch, 1 * inch, 5.5 * inch, 1 * inch)
        p.line(6.2 * inch, .5 * inch, 8 * inch, .5 * inch)
        p.line(6.2 * inch, 1 * inch, 8 * inch, 1 * inch)

        p.showPage()
        p.save()

        self.document.save(f'{self.employee.get_full_name()} Attendance Point.pdf', ContentFile(buffer.getbuffer()), save=False)
        self.save(update_fields=['document'])

    def get_assignee(self):
        """Will return the Employee Object of the assignee"""

        return Employee.objects.get(employee_id=self.assigned_by)

    def __str__(self):
        return f"{self.employee.get_full_name()}'s Attendance Point"


class SafetyPoint(models.Model):
    REASON_CHOICES = [
        ('0', 'Unsafe maneuver(s) or act'),
        ('1', 'Failure to cycle wheelchair lift'),
        ('2', 'Failure to do a proper vehicle inspection (DVI)'),
        ('3', 'Improper following distance'),
        ('4', 'Conviction of a minor traffic violation'),
        ('5', 'Backing Accident'),
        ('6', 'Minor Preventable incident'),
        ('7', 'Any use of a cell phone or non company-issued electronic device while operating a vehicle'),
        ('8', 'Major preventable incident that does not involve serious injury, death and/or property damage in excess of $25,000'),
        ('9', 'Major preventable incident with serious injury, death and/or property damage in excess of $25,000'),
        ('10', 'Any preventable roll-away incident'),
        ('11', 'Failure to properly secure/transport a mobility device'),
        ('12', 'Failure to immediately report a citation or incident in a company vehicle'),
        ('13', 'Tampering with, disabling, or otherwise interfering with Drive Cam or other monitoring equipment'),
        ('14', 'Conviction of a major traffic violation'),
    ]

    is_active = models.BooleanField(default=True)

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    incident_date = models.DateField()
    issued_date = models.DateField(null=True)
    points = models.IntegerField()
    document = models.FileField(validators=[pdf_extension], upload_to='safety_point_forms')
    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    unsafe_act = models.CharField(max_length=100, blank=True)
    details = models.TextField(default='')
    assigned_by = models.IntegerField()
    uploaded = models.BooleanField(default=False)

    def create_safety_point_document(self):
        """Will create a PDF for the Counseling and assign it to the Counseling Object"""
        subject = {
            '0': 'Unsafe maneuver(s) or act',
            '1': 'Failure to cycle wheelchair lift',
            '2': 'Failure to do a proper vehicle inspection (DVI)',
            '3': 'Improper following distance',
            '4': 'Conviction of a minor traffic violation',
            '5': 'Backing Accident',
            '6': 'Minor Preventable incident',
            '7': 'Any use of a cell phone or non company-issued electronic device while operating a vehicle',
            '8': 'Major preventable incident that does not involve serious injury, death and/or property damage in excess of $25,000',
            '9': 'Major preventable incident with serious injury, death and/or property damage in excess of $25,000',
            '10': 'Any preventable roll-away incident',
            '11': 'Failure to properly secure/transport a mobility device',
            '12': 'Failure to immediately report a citation or incident in a company vehicle',
            '13': 'Tampering with, disabling, or otherwise interfering with Drive Cam or other monitoring equipment',
            '14': 'Conviction of a major traffic violation',
        }

        paragraph1_return = {
            '0': 'committed an unsafe act while operating a company vehicle.',
            '1': 'failed to cycle a wheelchair lift.',
            '2': 'failed to do a proper vehicle inspection (DVI).',
            '3': 'failed to maintain a proper following distance of 4-5 seconds.',
            '4': 'was convicted of a minor traffic violation.',
            '5': 'was involved in a preventable backing accident.',
            '6': 'was involved in a minor preventable incident',
            '7': 'was using an unathorized electronic device while operating a company vehicle.',
            '8': 'was involved in a major preventable incident that does not involve serious injury, death and/or property damage in excess of $25,000.',
            '9': 'was involved in a major preventable incident with serious injury, death and/or property damage in excess of $25,000.',
            '10': 'was involved in a preventable roll-away incident.',
            '11': 'failed to properly secure/transport a mobility device.',
            '12': 'failed to immediately report a citation or incident in a company vehicle.',
            '13': 'was tampering with, disabling, or otherwise interfering with Drive Cam or other monitoring equipment.',
            '14': 'was convicted of a major traffic violation.',
        }

        points_str_return = {
            1: 'one',
            2: 'two',
            3: 'three',
            4: 'four',
            6: 'five',
        }

        buffer = io.BytesIO()

        p = canvas.Canvas(buffer, pagesize=letter)

        p.setLineWidth(.5)
        p.setFillColor('gray')
        p.setFont('Helvetica-Bold', 8)
        # Header
        header1 = '420 Executive Court North, Suite G'
        header2 = 'Fairfield, California 94585'
        header3 = '707 • 863 • 8980'
        header4 = '(Facsimile) 707 • 863 • 8 b944'
        header5 = 'www.mvtransit.com'
        p.drawRightString(7.75 * inch, 10.25 * inch, header1)
        p.drawRightString(7.75 * inch, 10.10 * inch, header2)
        p.drawRightString(7.75 * inch, 9.95 * inch, header3)
        p.drawRightString(7.75 * inch, 9.80 * inch, header4)
        p.drawRightString(7.75 * inch, 9.65 * inch, header5)

        # Logo
        logo_url = 'main/MV_Transportation_logo.png'
        absolute_url = urljoin(settings.STATIC_URL, logo_url)
        logo = ImageReader(absolute_url)
        p.drawImage(logo, 1 * inch, 9.5 * inch, 1.5 * inch, .75 * inch, mask='auto')

        # Title
        title = 'SAFETY POINT NOTICE'
        p.setFont('Times-BoldItalic', 18)
        p.setFillColor('black')
        p.drawString(1.5 * inch, 9.25 * inch, title)

        # To
        p.setFont('Helvetica-Bold', 13)
        p.drawString(1 * inch, 8.85 * inch, 'To:')
        p.drawString(1.6 * inch, 8.85 * inch, self.employee.get_full_name())

        # From
        p.drawString(1 * inch, 8.55 * inch, 'From:')
        p.drawString(1.6 * inch, 8.55 * inch, self.get_assignee().get_full_name())

        # Date
        p.drawString(1 * inch, 8.25 * inch, 'Date:')
        p.drawString(1.6 * inch, 8.25 * inch, self.issued_date.strftime('%m-%d-%Y'))

        # Subject
        p.drawString(1 * inch, 8.00 * inch, 'Subject:')
        subject_str = subject[self.reason] if self.reason != '0' else f'{subject[self.reason]}/{self.get_pretty_unsafe_act()}'

        y = 8.00
        if p.stringWidth(subject_str, 'Helvetica', 13) > 400:
            wrapped_text = wrap_text(subject_str, 'Helvetica', 13, 400)
            for line in wrapped_text:
                p.drawString(1.75 * inch, y * inch, line)
                y -= .20
        else:
            p.drawString(1.75 * inch, y * inch, subject_str)
            y -= .20

        # Paragraph 1
        paragraph1 = f"On {self.incident_date.strftime('%B %d, %Y')}, {self.employee.get_full_name()} {paragraph1_return[self.reason]}"
        if self.details:
            paragraph1 += ' '
            paragraph1 += self.details
            if self.details[-1] != '.':
                paragraph1 += '.'

        p.setFont('Times-Roman', 12)
        y -= .05
        if p.stringWidth(paragraph1, 'Times-Roman', 12) > 475:
            wrapped_text = wrap_text(paragraph1,'Times-Roman', 12, 475)
            for line in wrapped_text:
                p.drawString(1 * inch, (y + .02) * inch, line)
                y -= .20
        else:
            p.drawString(1 * inch, (y + .02) * inch, paragraph1)
            y -= .20

        reason = subject[self.reason] if self.reason != '0' else f'an {subject[self.reason]}'
        points = f'{points_str_return[self.points]} safety point ({self.points}).' if self.points == 1 else f'{points_str_return[self.points]} safety points ({self.points}).'

        points_line = f'According to company policy {reason} results in {points}'
        if p.stringWidth(points_line, 'Times-Roman', 12) > 475:
            wrapped_text = wrap_text(points_line, 'Times-Roman', 12, 475)
            for line in wrapped_text:
                p.drawString(1 * inch, y * inch, line)
                y -= .20
        else:
            p.drawString(1 * inch, (y + .02) * inch, points_line)
            y -= .20

        p.drawString(1 * inch, y * inch, 'Safety must always be the most important aspect of your job.')
        y -= .20

        # Safety Point Summary & Tenure
        p.setFont('Helvetica', 10)
        p.drawString(1 * inch, y * inch, 'The following is a summary of your Safety Points over the past eighteen (18) month period')
        y -= .3

        p.setFont('Times-Roman', 12)
        p.drawString(1.0 * inch, y * inch, 'Previous Point Total:')
        p.drawString(2.5 * inch, y * inch, str(self.employee.get_total_safety_points(exclude=self)))
        p.drawString(4.25 * inch, y * inch, 'Employee Hire Date:')
        p.drawString(5.75 * inch, y * inch, self.employee.hire_date.strftime('%m/%d/%Y'))
        y -= .2

        p.drawString(1.00 * inch, y * inch, 'New Points:')
        p.drawString(2.50 * inch, y * inch, str(self.points))
        p.drawString(4.25 * inch, y * inch, 'Tenure:')
        p.drawString(4.85 * inch, y * inch, self.employee.get_tenure())
        y -= .2

        p.drawString(1 * inch, y * inch, 'Total for 18-month period:')
        p.drawString(2.85 * inch, y * inch, str(self.employee.get_total_safety_points()))
        y -= .4

        # HR Paragraph
        paragraph2 = 'As an employee of MV Transportation you have the right to appeal the decision regarding this ' \
                     'accident. If you feel the preventable decision is inaccurate, then you must contact the HR ' \
                     'Director within 5 days of this notice. Once an appeal is received, we will have a panel review ' \
                     'your accident. For safety reasons this will not delay the retraining that must occur before ' \
                     'you can return to revenue service. '

        p.setFont('Helvetica', 10)
        wrapped_text = wrap_text(paragraph2, 'Helvetica', 10, 475)
        for line in wrapped_text:
            p.drawString(1 * inch, (y + .02) * inch, line)
            y -= .20

        p.setFont('Times-Roman', 12)
        # Signatures
        p.drawString(1 * inch, y * inch, 'Authorization')

        y -= .35

        p.line(1 * inch, y * inch, 3.75 * inch, y * inch)
        p.line(4.125 * inch, y * inch, 6.50 * inch, y * inch)

        y -= .2

        p.drawString(1 * inch, y * inch, 'Safety Manager')
        p.drawString(4.125 * inch, y * inch, 'Employee')

        y -= .4

        p.drawString(1 * inch, y * inch, 'Date:')
        p.line(1.5 * inch, y * inch, 3 * inch, y * inch)
        p.drawString(4.125 * inch, y * inch, 'Date:')
        p.line(4.625 * inch, y * inch, 6.125 * inch, y * inch)

        y -= .4

        p.drawString(1 * inch, y * inch, 'Witness:')
        p.line(1.75 * inch, y * inch, 3.75 * inch, y * inch)

        y -= .5

        # Union Things
        p.setLineWidth(1)
        p.setFont('Helvetica', 10)
        p.rect(1.625 * inch, y * inch, .1875 * inch, .1875 * inch)
        p.drawString(1.875 * inch, y * inch, 'By checking this box, you acknowledge that you do not want Union representation.')

        y -= .4

        paragraph3 = 'By checking this box, you acknowledge that you are requesting Union representation, and that ' \
                     'you have 10 business days to have the Union contact the Safety Manager about this point notice. ' \
                     'Failure to do so will result in the point(s) and related discipline being issued without ' \
                     'representation from the Union. '

        p.rect(1.625 * inch, y * inch, .1875 * inch, .1875 * inch)
        wrapped_text = wrap_text(paragraph3, 'Helvetica', 10, 450)
        line_num = 1
        x = 1.875
        for line in wrapped_text:
            if line_num == 2:
                x -= .25
            p.drawString(x * inch, y * inch, line)
            y -= .20
            line_num += 1

        y -= .2

        p.setFont('Helvetica-Bold', 12)
        p.drawString(3.125 * inch, y * inch, 'Your Initials:')
        p.line(4.1875 * inch, y * inch, 5.1875 * inch,y * inch)
        p.drawString(5.25 * inch, y * inch, 'Date:')
        p.line(5.6875 * inch, y * inch, 7 * inch, y * inch)

        p.setFillColor('gray')
        p.setFont('Times-Italic', 11)
        p.drawCentredString(4.25 * inch, .5 * inch, 'The Standard of Excellence Since 1976')

        p.showPage()
        p.save()

        self.document.save(f'{self.employee.get_full_name()} Safety Point.pdf', ContentFile(buffer.getbuffer()),
                           save=False)

        self.save(update_fields=['document'])

    def get_assignee(self):
        """Will return the Employee object of the assignee"""

        return Employee.objects.get(employee_id=self.assigned_by)

    def get_pretty_unsafe_act(self):
        return titlecase(self.unsafe_act)

    def __str__(self):
        return f"{self.employee.get_full_name()}'s Safety Point"


class Counseling(models.Model):
    ACTION_CHOICES = [
        ('0', 'Verbal Counseling'),
        ('1', 'Verbal Warning'),
        ('2', 'First Written Warning Notice'),
        ('3', 'Final Written Warning Notice & 3 Day Suspension'),
        ('4', 'Last & Final Warning'),
        ('5', 'Discharge for \"Just Cause\"'),
        ('6', 'Administrative Removal from Service'),
    ]

    is_active = models.BooleanField(default=True)

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    assigned_by = models.IntegerField()
    issued_date = models.DateField()
    action_type = models.CharField(max_length=40, choices=ACTION_CHOICES)
    document = models.FileField(validators=[pdf_extension], upload_to='counseling_forms')
    hearing_datetime = models.DateTimeField(null=True)
    conduct = models.TextField()
    conversation = models.TextField()
    attendance = models.OneToOneField(Attendance, on_delete=models.CASCADE, null=True, blank=True)
    safety_point = models.OneToOneField(SafetyPoint, on_delete=models.CASCADE, null=True, blank=True)
    uploaded = models.BooleanField(default=False)
    override_by = models.IntegerField(null=True)

    def get_hearing_datetime(self):
        """If there is a hearing datetime it will return the properly formatted string for it otherwise returns a
        later date """
        hearing_datetime_str = self.hearing_datetime.strftime('%m-%d-%Y %I:%M %p') if self.hearing_datetime else "a later date"
        return hearing_datetime_str

    def get_assignee(self):
        """Will return the Employee object of the assignee"""

        return Employee.objects.get(employee_id=self.assigned_by)

    def get_override_by(self):
        return Employee.objects.get(employee_id=self.override_by) if self.override_by else None

    def create_counseling_document(self):
        """Will create a PDF for the Counseling and assign it to the Counseling Object"""
        buffer = io.BytesIO()

        p = canvas.Canvas(buffer, pagesize=letter)

        p.setLineWidth(.75)

        # Title
        title = 'Employee Coaching and Counseling Form'
        p.setFontSize(18)
        p.drawCentredString(4.25 * inch, 10 * inch, title)

        # Date, Division, and Name
        p.setFontSize(11)

        p.drawString(.5 * inch, 9.5 * inch, 'Date: ' + datetime.datetime.today().strftime('%m-%d-%Y'))
        p.drawString(6.8 * inch, 9.5 * inch, 'Division #: 12')

        p.drawString(.5 * inch, 9.00 * inch, 'Employee Name:')
        p.drawString(1.92 * inch, 9.02 * inch, self.employee.get_full_name())

        p.line(1.9 * inch, 9.00 * inch, 4 * inch, 9.00 * inch)

        # Type of Action
        p.setFontSize(9)
        p.drawString(.5 * inch, 8.500 * inch, 'TYPE OF ACTION:')

        fill = {
            '0': 0,
            '1': 0,
            '2': 0,
            '3': 0,
            '4': 0,
            '5': 0,
            '6': 0,
        }

        fill[self.action_type] += 1

        p.rect(.875 * inch, 8.2425 * inch, .125 * inch, .125 * inch, fill=fill['0'])
        p.drawString(1.125 * inch, 8.2525 * inch, 'Verbal Counseling')

        p.rect(.875 * inch, 8.0425 * inch, .125 * inch, .125 * inch, fill=fill['1'])
        p.drawString(1.125 * inch, 8.0525 * inch, 'Verbal Warning')

        p.rect(.875 * inch, 7.8425 * inch, .125 * inch, .125 * inch, fill=fill['2'])
        p.drawString(1.125 * inch, 7.8525 * inch, 'First Written Warning Notice')

        p.rect(.875 * inch, 7.6425 * inch, .125 * inch, .125 * inch, fill=fill['3'])
        p.drawString(1.125 * inch, 7.6525 * inch, 'First Written Warning Notice & 3 Day Suspension')

        p.rect(.875 * inch, 7.4425 * inch, .125 * inch, .125 * inch, fill=fill['4'])
        p.drawString(1.125 * inch, 7.4525 * inch, 'Last & Final Warning')

        p.rect(.875 * inch, 7.2425 * inch, .125 * inch, .125 * inch, fill=fill['5'])
        p.drawString(1.125 * inch, 7.2525 * inch, 'Discharge for \"Just Cause\"')

        p.rect(.875 * inch, 6.9525 * inch, .125 * inch, .125 * inch, fill=fill['6'])
        p.drawString(1.125 * inch, 6.9625 * inch,
                     'Administrative Removal from Service Pending Investigation. A hearing is scheduled')
        p.drawString(1.125 * inch, 6.7625 * inch,
                     f'for {self.get_hearing_datetime()} at which time you may make any statement or produce')
        p.drawString(1.125 * inch, 6.5625 * inch, 'any evidence in regard to the facts of the matter.')

        p.setFont('Helvetica-Bold', 9)
        p.drawString(1.125 * inch, 6.3125 * inch,
                     'If you fail to appear at the scheduled hearing, the company will assume that you have')
        p.drawString(1.125 * inch, 6.125 * inch, 'resigned your employment.')

        p.setFont('Helvetica-Bold', 11)
        p.drawString(.5 * inch, 5.75 * inch, 'Explanation of Employee Conduct:')

        p.setFont('Helvetica', 9)

        # Conduct Paragraph Lines
        p.line(.5 * inch, 5.50 * inch, 8 * inch, 5.50 * inch)
        p.line(.5 * inch, 5.25 * inch, 8 * inch, 5.25 * inch)
        p.line(.5 * inch, 5.00 * inch, 8 * inch, 5.00 * inch)
        p.line(.5 * inch, 4.75 * inch, 8 * inch, 4.75 * inch)

        y = 5.50
        if p.stringWidth(self.conduct, 'Helvetica', 10) > 595:
            wrapped_text = wrap_text(self.conduct, 'Helvetica', 10, 595)
            for line in wrapped_text:
                p.drawString(.5625 * inch, (y + .02) * inch, line)
                y -= .25
        else:
            p.drawString(.5625 * inch, (y + .02) * inch, self.conduct)

        p.setFont('Helvetica-Bold', 11)
        p.drawString(.5 * inch, 4.50 * inch, 'Record of Conversation:')

        p.setFont('Helvetica', 9)

        # Conversation Paragraph Lines
        p.line(.5 * inch, 4.25 * inch, 8 * inch, 4.25 * inch)
        p.line(.5 * inch, 4.00 * inch, 8 * inch, 4.00 * inch)
        p.line(.5 * inch, 3.75 * inch, 8 * inch, 3.75 * inch)
        p.line(.5 * inch, 3.50 * inch, 8 * inch, 3.50 * inch)

        y = 4.25
        if p.stringWidth(self.conversation, 'Helvetica', 10) > 595:
            wrapped_text = wrap_text(self.conversation, 'Helvetica', 10, 595)
            for line in wrapped_text:
                p.drawString(.5625 * inch, (y + .02) * inch, line)
                y -= .25
        else:
            p.drawString(.5625 * inch, (y + .02) * inch, self.conversation)

        p.setFontSize(7)
        p.rect(.875 * inch, 3.245 * inch, .120 * inch, .120 * inch)
        p.drawString(1.0625 * inch, 3.270 * inch, 'Employee Waives the right to Union Representation:')
        p.line(3.70 * inch, 3.270 * inch, 4.0625 * inch, 3.270 * inch)

        p.drawString(4.25 * inch, 3.270 * inch, 'Witness:')
        p.line(4.75 * inch, 3.270 * inch, 7.00 * inch, 3.270 * inch)

        p.setFont('Helvetica-Bold', 7)
        p.drawString(.5 * inch, 3.000 * inch,
                     'Failure to correct this problem or to avoid future problems or offenses of this nature may result in')
        p.drawString(.5 * inch, 2.875 * inch, 'further disciplinary action up to and including termination.')

        p.setFont('Helvetica', 11)
        p.drawString(.5 * inch, 2.625 * inch, 'Employee Comments:')

        p.line(.5 * inch, 2.375 * inch, 8 * inch, 2.375 * inch)
        p.line(.5 * inch, 2.125 * inch, 8 * inch, 2.125 * inch)

        p.drawString(.5 * inch, 1.750 * inch, 'Employee Signature:')
        p.line(2.125 * inch, 1.750 * inch, 4.5 * inch, 1.750 * inch)

        p.drawString(5.5 * inch, 1.750 * inch, 'Date:')
        p.line(6 * inch, 1.750 * inch, 8 * inch, 1.750 * inch)

        p.setFontSize(7)

        p.drawString(.5 * inch, 1.625 * inch,
                     'Employee\'s signature does not indicate agreement or consent to discipline.')

        p.rect(.64 * inch, 1.4325 * inch, .1 * inch, .1 * inch)
        p.drawString(.8125 * inch, 1.44 * inch, 'Employee refused to sign')

        p.setFontSize(11)

        p.drawString(.5 * inch, 1 * inch, 'Supervisor Signature:')
        p.line(2.125 * inch, 1 * inch, 4.5 * inch, 1 * inch)

        p.drawString(5.5 * inch, 1 * inch, 'Date:')
        p.line(6 * inch, 1 * inch, 8 * inch, 1 * inch)

        p.showPage()
        p.save()

        self.document.save(f'{self.employee.get_full_name()} Counseling.pdf', ContentFile(buffer.getbuffer()), save=False)
        self.save(update_fields=['document'])

    def __str__(self):
        return f"{self.employee.get_full_name()}'s Counseling"


class Hold(models.Model):
    hold_date = models.DateField()
    incident_date = models.DateField(null=True, blank=True)
    training_datetime = models.DateTimeField(null=True, blank=True)
    release_date = models.DateTimeField(null=True, blank=True)
    reason = models.CharField(max_length=30)
    assigned_by = models.IntegerField()
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE)

    def get_assignee(self):
        """Will return the Employee object of the assignee"""

        return Employee.objects.get(employee_id=self.assigned_by)

    def __str__(self):
        return f'{self.employee.get_full_name()}\'s Hold'


class TimeOffRequest(models.Model):
    TIME_OFF_CHOICES = [
        ('', ''),
        ('0', 'Day(s) Off (Unpaid)'),
        ('1', 'Vacation (Paid)'),
        ('2', 'Leave of Absence'),
        ('3', 'Jury Duty / Subpoena'),
        ('4', 'Military Leave'),
        ('5', 'Extended Medical Leave'),
        ('6', 'Family Medical Leave'),
        ('7', 'Floating Holiday'),
        ('8', 'Personal'),
        ('9', 'Doctor Appointment'),
        ('10', 'Other'),
    ]

    STATUS_CHOICES = [
        ('0', 'Pending'),
        ('1', 'Approved'),
        ('2', 'Denied'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    request_date = models.DateField()
    time_off_type = models.CharField(max_length=50, choices=TIME_OFF_CHOICES)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='0')
    status_change_by = models.CharField(max_length=50, blank=True)
    reason = models.TextField(blank=True)
    comments = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    date_removed = models.DateField(null=True)

    def __str__(self):
        return f"{self.employee.get_full_name()}'s Time Off Request"


class DayOff(models.Model):
    requested_date = models.DateField()
    time_off_request = models.ForeignKey(TimeOffRequest, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.requested_date.strftime('%m-%d-%Y')


class Settlement(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True)
    details = models.TextField(default='', blank=False)
    created_date = models.DateField(null=True)
    assigned_by = models.IntegerField()
    document = models.FileField(validators=[pdf_extension], upload_to='settlement_forms', null=True)
    is_active = models.BooleanField(default=True)
    uploaded = models.BooleanField(default=False)

    def create_settlement_document(self):
        """Will create a PDF for the Counseling and assign it to the Counseling Object"""
        buffer = io.BytesIO()

        p = canvas.Canvas(buffer, pagesize=letter)

        p.setLineWidth(.75)

        # Logo
        logo_url = 'main/MV_Transportation_logo.png'
        absolute_url = urljoin(settings.STATIC_URL, logo_url)
        logo = ImageReader(absolute_url)
        p.drawImage(logo, 3.5 * inch, 10 * inch, 1.5 * inch, .75 * inch, mask='auto')

        # Title
        p.drawCentredString(4.25 * inch, 9.3875 * inch, "SETTLEMENT AGREEMENT")
        p.drawCentredString(4.25 * inch, 9.1875 * inch, "BETWEEN")
        p.drawCentredString(4.25 * inch, 8.9875 * inch, "MV TRANSPORTATION AND TEAMSTERS LOCAL 385")

        p.setFont('Times-Roman', 12)
        # Intro
        intro = f'MV Transportation and Teamster Local 385 have agreed to the following regarding' \
                f' {self.employee.get_full_name()}.'
        y = 8.5

        if p.stringWidth(intro, 'Times-Roman', 12) > 455.0:
            wrapped_text = wrap_text(intro, 'Times-Roman', 12, 455)
            for line in wrapped_text:
                p.drawString(1.125 * inch, y * inch, line)
                y -= .20
        else:
            p.drawString(1.125 * inch, y * inch, intro)
            y -= .20

        y -= .3
        # Details
        for paragraph in self.details.replace('\r', '').split('\n'):
            if p.stringWidth(paragraph, 'Times-Roman', 12) > 455.0:
                wrapped_text = wrap_text(paragraph, 'Times-Roman', 12, 455)
                for line in wrapped_text:
                    p.drawString(1.125 * inch, y * inch, line)
                    y -= .20
            else:
                p.drawString(1.125 * inch, y * inch, paragraph)
                y -= .20

        y -= .3

        p.drawString(1.125 * inch, y * inch, 'Any hours that may have been missed during this process will be unpaid.')

        y -= .3

        # Outro
        outro = 'The parties agree that the terms of this agreement may not used or referenced in any grievance or' \
                ' open ULP activity related proceeding and the resolution of this matter shall not result in the' \
                ' establishment of any past practice or precedent with regard to the interpretation of the' \
                ' company\'s work rules, polices, and/or the applicable collective bargaining agreement.'

        wrapped_text = wrap_text(outro, 'Times-Roman', 12, 455)
        for line in wrapped_text:
            p.drawString(1.125 * inch, y * inch, line)
            y -= .20

        y -= .5

        p.setFont('Helvetica', 10)
        # Signatures
        p.line(1.125 * inch, y * inch, 3.75 * inch, y * inch)  # Top Left
        p.line(4.75 * inch, y * inch, 7.375 * inch, y * inch)  # Top Right

        y -= .2
        p.drawString(1.125 * inch, y * inch, 'MV Transportation')
        p.drawRightString(3.75 * inch, y * inch, 'Date')

        p.drawString(4.75 * inch, y * inch, 'MV Transportation')
        p.drawRightString(7.375 * inch, y * inch, 'Date')

        y -= .75

        p.line(1.125 * inch, y * inch, 3.75 * inch, y * inch)  # Bottom Left
        p.line(4.75 * inch, y * inch, 7.375 * inch, y * inch)  # Bottom Right

        y -= .2
        p.drawString(1.125 * inch, y * inch, 'Employee')
        p.drawRightString(3.75 * inch, y * inch, 'Date')

        p.drawString(4.75 * inch, y * inch, 'Teamster Local 385')
        p.drawRightString(7.375 * inch, y * inch, 'Date')

        # Footer
        footer = '4950 LB McLeod Rd | Orlando FL 32811 | P 407-851-8201'
        p.setFont('Helvetica-Bold', 10)
        p.setFillColor('gray')

        p.drawCentredString(4.25 * inch, .25 * inch, footer)

        p.showPage()
        p.save()

        self.document.save(f'{self.employee.get_full_name()} Settlement.pdf', ContentFile(buffer.getbuffer()),
                           save=False)
        self.save(update_fields=['document'])

    def get_assignee(self):
        """Will return the Employee object of the assignee"""

        return Employee.objects.get(employee_id=self.assigned_by)

    def __str__(self):
        return f'{self.employee.get_full_name()}\'s Settlement'
