import boto3
import datetime
import os
import uuid

from django.contrib import messages
from django.contrib.auth import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import Sum, Q, OuterRef, Subquery, CharField, Value as V
from django.db.models.functions import Concat
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from notifications.models import Notification

from employees.helper_functions import combine_attendance_documents
from employees.models import Employee, Attendance, Hold, Counseling, TimeOffRequest, DayOff, Settlement
from .forms import EmployeeCreationForm, AttendanceFilterForm, CounselingFilterForm, BulkAssignAttendance, \
    MakeTimeOffRequest, TimeOffFilterForm, FilterForm


@login_required
@permission_required('employees.can_view_operations_home', raise_exception=True)
def home(request, attendance_ids=None):
    download_urls = []
    if attendance_ids:
        attendance_ids_list = attendance_ids.split(',')
        attendance_ids_list = [int(attendance_id) for attendance_id in attendance_ids_list]
        if attendance_ids_list and len(attendance_ids_list) > 1:
            attendance_document = combine_attendance_documents(attendance_ids_list)
            s3 = boto3.client('s3',
                              aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
                              aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'])

            object_name = f'tmp/bulk_attendance_{str(uuid.uuid4())}.pdf'
            object_url = f'https://{settings.AWS_S3_CUSTOM_DOMAIN}/{object_name}'
            attendance_document.seek(0)

            s3.put_object(Body=attendance_document.read(), Bucket=os.environ['AWS_STORAGE_BUCKET_NAME'], Key=object_name,
                          ContentType='application/pdf')

            download_urls.append(object_url)
        elif attendance_ids_list and len(attendance_ids_list) == 1:
            attendance_object = Attendance.objects.get(id=attendance_ids_list[0])
            download_urls.append(request.build_absolute_uri(attendance_object.document.url))
            try:
                download_urls.append(request.build_absolute_uri(attendance_object.counseling.document.url))
            except Counseling.DoesNotExist:
                pass

    all_employees = Employee.objects.filter(is_active=True).order_by('last_name')
    at_10_attendance = [employee for employee in all_employees if employee.get_total_attendance_points() >= 10]
    all_settlements = Settlement.objects.filter(is_active=True).order_by('-created_date')[:10]
    last_final = all_employees.filter(counseling__action_type='4')
    no_sick_days = [employee for employee in all_employees if (employee.unpaid_sick + employee.paid_sick) <= 0]
    recent_terms = Employee.objects.filter(is_active=False).order_by('-termination_date')[:5]
    no_attendance_6_months = [employee for employee in all_employees if not employee.has_attendance_in_6_months()]
    recent_hires = all_employees.filter(hire_date__gte=timezone.now() - datetime.timedelta(days=30))

    data = {
        'download_urls': download_urls,
        'at_10_attendance': at_10_attendance,
        'all_settlements': all_settlements,
        'last_final': last_final,
        'no_sick_days': no_sick_days,
        'recent_terms': recent_terms,
        'no_attendance_6_months': no_attendance_6_months,
        'recent_hires': recent_hires,
    }

    return render(request, 'operations/home.html', data)


@login_required
@permission_required('employees.can_assign_attendance', raise_exception=True)
def bulk_assign_attendance(request):
    if request.method == 'POST':
        form = BulkAssignAttendance(request.POST)

        if form.is_valid():
            attendance_ids = form.save(request)

            messages.add_message(request, messages.SUCCESS, 'Successfully added all attendance points')

            data = {'url': reverse('operations-home', args=[attendance_ids])}

            return JsonResponse(data, status=200)
        else:
            return JsonResponse(form.errors, status=400)

    else:
        form = BulkAssignAttendance()

        data = {
            'form': form
        }

        return render(request, 'operations/bulk_assign_attendance.html', data)


@login_required
def search_employees(request):
    search = request.GET.get('q')

    employees = Employee.objects.annotate(
                full_name=Concat('first_name', V(' '), 'last_name', output_field=CharField())).filter(
                full_name__icontains=search, is_active=True)

    employee_names = [f'{employee.last_name}, {employee.first_name} | {employee.employee_id}' for employee in employees]

    return JsonResponse(employee_names, safe=False)


@login_required
@permission_required('employees.can_view_attendance_reports', raise_exception=True)
def attendance_reports(request):
    sort_by = request.GET.get('sort_by')
    reasons = request.GET.get('reasons')
    company_name = request.GET.get('company')
    date_range = request.GET.get('date_range')
    search = request.GET.get('search')

    start_date = datetime.datetime.strptime(date_range[:10], '%m/%d/%Y') if date_range else\
        (datetime.datetime.today() - datetime.timedelta(days=365))
    end_date = datetime.datetime.strptime(date_range[13:], '%m/%d/%Y') if date_range else\
        datetime.datetime.today()
    attendance_records = Attendance.objects.filter(is_active=True, employee__is_active=True)

    sort_choices = [
        ('', 'Sort By'),
        ('employee__last_name', 'Last Name'),
        ('-incident_date', 'Incident Date'),
        ('employee__first_name', 'First Name'),
        ('employee_id', 'Employee ID'),
        ('-points', 'Points'),
        ('-total_points', 'Total Points'),
    ]

    if search:
        try:
            search = int(search)
            attendance_records = attendance_records.filter(employee__employee_id=search)

        except ValueError:
            attendance_records = Attendance.objects.annotate(
                full_name=Concat('employee__first_name', V(' '), 'employee__last_name', output_field=CharField())).filter(
                full_name__icontains=search, is_active=True, employee__is_active=True)

    if sort_by == '-total_points':
        records = attendance_records.annotate(full_name=Concat('employee__first_name', V(' '), 'employee__last_name', output_field=CharField())).values('full_name').annotate(total_points=Sum('points'))

        attendance_records = attendance_records.annotate(total_points=Subquery(records.filter(Q(full_name__icontains=OuterRef('employee__first_name')) & Q(full_name__icontains=OuterRef('employee__last_name'))).values('total_points')[:1]))

        attendance_records = attendance_records.order_by('-total_points')
    elif sort_by:
        attendance_records = attendance_records.order_by(sort_by)

    if reasons:
        attendance_records = attendance_records.filter(reason__exact=reasons)

    if company_name:
        attendance_records = attendance_records.filter(employee__company__display_name=company_name)

    if start_date and end_date:
        attendance_records = attendance_records.filter(incident_date__gte=start_date, incident_date__lte=end_date)

    f_form = AttendanceFilterForm(data={
        'sort_by': sort_by,
        'reasons': reasons,
        'company': company_name,
        'date_range': date_range,
        'search': search
    }, sort_choices=sort_choices)

    page = request.GET.get('page')
    paginator = Paginator(attendance_records, 25)
    page_obj = paginator.get_page(page)

    data = {
        'page_obj': page_obj,
        'f_form': f_form,
        'start_date': start_date.strftime('%m/%d/%Y'),
        'end_date': end_date.strftime('%m/%d/%Y'),
    }

    return render(request, 'operations/attendance_reports.html', data)


@login_required
@permission_required('employees.can_view_counseling_reports', raise_exception=True)
def counseling_reports(request):
    sort_by = request.GET.get('sort_by')
    action_type = request.GET.get('action_type')
    company_name = request.GET.get('company')
    date_range = request.GET.get('date_range')
    search = request.GET.get('search')

    sort_choices = [
        ('', 'Sort By'),
        ('employee__last_name', 'Last Name'),
        ('-issued_date', 'Issued Date'),
        ('employee__first_name', 'First Name'),
        ('employee_id', 'Employee ID'),
    ]

    start_date = datetime.datetime.strptime(date_range[:10], '%m/%d/%Y') if date_range else\
        (datetime.datetime.today() - datetime.timedelta(days=30))
    end_date = datetime.datetime.strptime(date_range[13:], '%m/%d/%Y') if date_range else\
        datetime.datetime.today()
    counseling_records = Counseling.objects.filter(is_active=True, employee__is_active=True)

    if search:
        try:
            search = int(search)
            counseling_records = counseling_records.filter(employee__employee_id=search)

        except ValueError:
            counseling_records = Counseling.objects.annotate(
                full_name=Concat('employee__first_name', V(' '), 'employee__last_name', output_field=CharField())).\
                filter(full_name__icontains=search, employee__is_active=True, is_active=True)

    if sort_by:
        counseling_records = counseling_records.order_by(sort_by)

    if action_type:
        counseling_records = counseling_records.filter(action_type__exact=action_type)

    if company_name:
        counseling_records = counseling_records.filter(employee__company__display_name=company_name)

    if start_date and end_date:
        counseling_records = counseling_records.filter(issued_date__gte=start_date, issued_date__lte=end_date)

    f_form = CounselingFilterForm(sort_choices=sort_choices, data={
        'sort_by': sort_by,
        'action_type': action_type,
        'company': company_name,
        'date_range': date_range,
        'search': search
    })

    page = request.GET.get('page')
    paginator = Paginator(counseling_records, 25)
    page_obj = paginator.get_page(page)

    data = {
        'page_obj': page_obj,
        'f_form': f_form,
        'start_date': start_date.strftime('%m/%d/%Y'),
        'end_date': end_date.strftime('%m/%d/%Y'),
    }

    return render(request, 'operations/counseling_reports.html', data)


@login_required
@permission_required('employees.can_view_hold_list', raise_exception=True)
def view_hold_list(request):
    company = request.GET.get('company')
    search = request.GET.get('search')
    sort_by = request.GET.get('sort_by')

    sort_choices = [
        ('', 'Sort By'),
        ('employee__last_name', 'Last Name'),
        ('employee__first_name', 'First Name'),
        ('employee__employee_id', 'Employee ID'),
        ('employee__position', 'Position'),
        ('employee__hire_date', 'Hire Date'),
        ('-hold_date', 'Hold Date'),
        ('reason', 'Reason'),
    ]

    employee_holds = Hold.objects.filter(employee__is_active=True).order_by('-id')
    if search:
        try:
            search = int(search)

            employee_holds = employee_holds.filter(employee_id__exact=search)

        except ValueError:
            employee_holds = Hold.objects.annotate(
                full_name=Concat('employee__first_name', V(' '), 'employee__last_name', output_field=CharField())).filter(
                full_name__icontains=search)

    if company:
        employee_holds = employee_holds.filter(employee__company__display_name__exact=company)
    if sort_by:
        employee_holds = employee_holds.order_by(sort_by)

    f_form = FilterForm(sort_choices=sort_choices, data={
        'company': company,
        'search': search,
        'sort_by': sort_by
    })

    page = request.GET.get('page')
    paginator = Paginator(employee_holds, 25)
    page_obj = paginator.get_page(page)

    data = {
        'page_obj': page_obj,
        'f_form': f_form,
    }
    return render(request, 'operations/hold_list.html', data)


@login_required
@permission_required('employees.can_add_employee', raise_exception=True)
def add_employee(request):
    if request.method == 'POST':
        form = EmployeeCreationForm(request.POST)

        if form.is_valid():
            new_employee = form.save()

            messages.add_message(request, messages.SUCCESS, f'{new_employee.get_position()} Successfully Added')

            data = {'url': reverse('main-home')}

            return JsonResponse(data, status=200)
        else:
            return JsonResponse(form.errors, status=400)

    else:
        form = EmployeeCreationForm()

        return render(request, 'operations/add_employee.html', {'form': form})


@login_required
@permission_required('employees.can_add_time_off_request', raise_exception=True)
def make_time_off_request(request):
    if request.method == 'POST':
        form = MakeTimeOffRequest(request.POST)

        if form.is_valid():
            form.save(request)

            messages.add_message(request, messages.SUCCESS, 'Successfully Added Time Off Request')

            data = {'url': reverse('operations-make-time-off-request')}

            return JsonResponse(data, status=200)
        else:
            return JsonResponse(form.errors, status=400)
    else:
        form = MakeTimeOffRequest()

        data = {
            'form': form,
        }

        return render(request, 'operations/make_time_off_request.html', data)


@login_required
@permission_required('employees.can_view_time_off_reports', raise_exception=True)
def time_off_reports(request, notification_id=None):
    sort_by = request.GET.get('sort_by')
    status = request.GET.get('status')
    time_off_type = request.GET.get('time_off_type')
    company_name = request.GET.get('company')
    date_range = request.GET.get('date_range')
    search = request.GET.get('search')
    pk = request.GET.get('pk')

    sort_choices = [
        ('', 'Sort By'),
        ('employee__last_name', 'Last Name'),
        ('-request_date', 'Request Date'),
        ('employee__first_name', 'First Name'),
        ('employee_id', 'Employee ID'),
    ]

    start_date = datetime.datetime.strptime(date_range[:10], '%m/%d/%Y') if date_range else \
        (datetime.datetime.today() - datetime.timedelta(days=30))
    end_date = datetime.datetime.strptime(date_range[13:], '%m/%d/%Y') if date_range else \
        (datetime.datetime.today() + datetime.timedelta(days=30))

    if notification_id:
        notification = Notification.objects.get(id=notification_id)
        notification.mark_as_read()
    if pk:
        time_off_records = TimeOffRequest.objects.filter(pk=pk)
    else:
        time_off_records = TimeOffRequest.objects.filter(is_active=True, employee__is_active=True)

        if search:
            try:
                search = int(search)
                time_off_records = time_off_records.filter(employee__employee_id=search)

            except ValueError:
                time_off_records = TimeOffRequest.objects.annotate(
                    full_name=Concat('employee__first_name', V(' '), 'employee__last_name',
                                     output_field=CharField())).filter(full_name__icontains=search, is_active=True,
                                                                       employee__is_active=True)

        if time_off_type:
            time_off_records = time_off_records.filter(time_off_type__exact=time_off_type)

        if status:
            time_off_records = time_off_records.filter(status__exact=status)

        if company_name:
            time_off_records = time_off_records.filter(employee__company__display_name=company_name)

        if start_date and end_date:
            time_off_records = time_off_records.filter(dayoff__requested_date__gte=start_date, dayoff__requested_date__lte=end_date)

        if sort_by:
            time_off_records = time_off_records.order_by(sort_by)

    f_form = TimeOffFilterForm(sort_choices=sort_choices, data={
        'sort_by': sort_by,
        'status': status,
        'time_off_type': time_off_type,
        'company': company_name,
        'date_range': date_range,
        'search': search
    })

    page = request.GET.get('page')
    paginator = Paginator(time_off_records, 25)
    page_obj = paginator.get_page(page)

    data = {
        'page_obj': page_obj,
        'f_form': f_form,
        'start_date': start_date.strftime('%m/%d/%Y'),
        'end_date': end_date.strftime('%m/%d/%Y'),
    }

    return render(request, 'operations/time_off_reports.html', data)


@login_required
@permission_required('employees.can_view_time_off_reports', raise_exception=True)
def time_off_status(request, time_off_id, status):
    time_off = TimeOffRequest.objects.get(id=time_off_id)

    time_off.status = status
    time_off.status_change_by = request.user.get_full_name()
    time_off.save()

    return redirect('operations-time-off-reports')


@login_required
@permission_required('employees.can_remove_time_off', raise_exception=True)
def remove_time_off(request, time_off_id):
    time_off_request = TimeOffRequest.objects.get(id=time_off_id)

    if time_off_request.status == '0':
        time_off_request.is_active = False
        time_off_request.date_removed = datetime.datetime.today()

        time_off_request.save(update_fields=['is_active'])

        for day in DayOff.objects.filter(time_off_request=time_off_request):
            day.is_active = False
            day.save()

    else:
        messages.add_message(request, messages.ERROR, 'Time off Request has been approved/denied already.'
                                                      'Please contact a manager to remove this time off request')

    return redirect('employee-account', time_off_request.employee.employee_id)


@login_required
@permission_required('employees.can_view_termination_reports', raise_exception=True)
def termination_reports(request):
    company = request.GET.get('company')
    date_range = request.GET.get('date_range')
    search = request.GET.get('search')
    sort_by = request.GET.get('sort_by')

    sort_choices = [
        ('', 'Sort By'),
        ('last_name', 'Last Name'),
        ('first_name', 'First Name'),
        ('employee_id', 'Employee ID'),
        ('position', 'Position'),
        ('hire_date', 'Hire Date'),
        ('-termination_date', 'Termination Date'),
    ]

    start_date = datetime.datetime.strptime(date_range[:10], '%m/%d/%Y') if date_range else \
        (datetime.datetime.today() - datetime.timedelta(days=365))
    end_date = datetime.datetime.strptime(date_range[13:], '%m/%d/%Y') if date_range else \
        datetime.datetime.today()

    termed_drivers = Employee.objects.filter(is_active=False)
    if search:
        try:
            search = int(search)

            termed_drivers = termed_drivers.filter(employee_id__exact=search)

        except ValueError:
            termed_drivers = Employee.objects.annotate(
                full_name=Concat('first_name', V(' '), 'last_name', output_field=CharField())).filter(
                full_name__icontains=search, is_active=False)

    if company:
        termed_drivers = termed_drivers.filter(company__display_name__exact=company)
    if start_date and end_date:
        termed_drivers = termed_drivers.filter(termination_date__gte=start_date, termination_date__lte=end_date)
    if sort_by:
        termed_drivers = termed_drivers.order_by(sort_by)

    f_form = FilterForm(sort_choices=sort_choices, data={
        'company': company,
        'date_range': date_range,
        'search': search,
        'sort_by': sort_by
    })

    page = request.GET.get('page')
    paginator = Paginator(termed_drivers, 25)
    page_obj = paginator.get_page(page)

    data = {
        'page_obj': page_obj,
        'f_form': f_form,
        'start_date': start_date.strftime('%m/%d/%Y'),
        'end_date': end_date.strftime('%m/%d/%Y'),
    }

    return render(request, 'operations/termination_reports.html', data)
