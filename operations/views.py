import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import CharField, Value as V
from django.db.models.functions import Concat
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse

from employees.models import Employee, Attendance, Hold, Counseling, TimeOffRequest, DayOff
from .forms import EmployeeCreationForm, AttendanceFilterForm, CounselingFilterForm, BulkAssignAttendance, \
    MakeTimeOffRequest, TimeOffFilterForm, TerminationFilterForm


@login_required
def home(request, download=None):
    data = {
        'download': download
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

    employees = Employee.objects.filter(is_active=True).annotate(
                full_name=Concat('first_name', V(' '), 'last_name', output_field=CharField())).filter(
                full_name__icontains=search)

    employee_names = [f'{employee.last_name}, {employee.first_name} | {employee.employee_id}' for employee in employees]

    return JsonResponse(employee_names, safe=False)


@login_required
@permission_required('employees.can_view_attendance_reports', raise_exception=True)
def attendance_reports(request):
    if request.method == 'POST':
        sort_by = request.POST.get('sort_by')
        reasons = request.POST.get('reasons')
        company_name = request.POST.get('company')
        date_range = request.POST.get('date_range')
        search = request.POST.get('search')
    else:
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

    if search:
        try:
            search = int(search)
            attendance_records = attendance_records.filter(employee__employee_id=search)

        except ValueError:
            attendance_records = Attendance.objects.annotate(
                full_name=Concat('employee__first_name', V(' '), 'employee__last_name', output_field=CharField())).filter(
                full_name__icontains=search).order_by(sort_by)

    if sort_by:
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
    })

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
    if request.method == 'POST':
        sort_by = request.POST.get('sort_by')
        action_type = request.POST.get('action_type')
        company_name = request.POST.get('company')
        date_range = request.POST.get('date_range')
        search = request.POST.get('search')
    else:
        sort_by = request.GET.get('sort_by')
        action_type = request.GET.get('action_type')
        company_name = request.GET.get('company')
        date_range = request.GET.get('date_range')
        search = request.GET.get('search')

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
                filter(full_name__icontains=search, employee__is_active=True)

    if sort_by:
        counseling_records = counseling_records.order_by(sort_by)

    if action_type:
        counseling_records = counseling_records.filter(action_type__exact=action_type)

    if company_name:
        counseling_records = counseling_records.filter(employee__company__display_name=company_name)

    if start_date and end_date:
        counseling_records = counseling_records.filter(issued_date__gte=start_date, issued_date__lte=end_date)

    f_form = CounselingFilterForm(data={
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
    hold_list = Hold.objects.all()

    data = {
        'hold_list': hold_list
    }

    return render(request, 'operations/hold_list.html', data)


@login_required
@permission_required('employees.can_add_employee', raise_exception=True)
def add_employee(request):
    if request.method == 'POST':
        form = EmployeeCreationForm(request.POST)

        if form.is_valid():
            form.save()

            messages.add_message(request, messages.SUCCESS, 'Driver Successfully Added')

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

            data = {'url': reverse('operations-home')}

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
def time_off_reports(request):
    if request.method == 'POST':
        sort_by = request.POST.get('sort_by')
        status = request.POST.get('status')
        time_off_type = request.POST.get('time_off_type')
        company_name = request.POST.get('company')
        date_range = request.POST.get('date_range')
        search = request.POST.get('search')
    else:
        sort_by = request.GET.get('sort_by')
        status = request.GET.get('status')
        time_off_type = request.GET.get('time_off_type')
        company_name = request.GET.get('company')
        date_range = request.GET.get('date_range')
        search = request.GET.get('search')

    start_date = datetime.datetime.strptime(date_range[:10], '%m/%d/%Y') if date_range else \
        (datetime.datetime.today() - datetime.timedelta(days=30))
    end_date = datetime.datetime.strptime(date_range[13:], '%m/%d/%Y') if date_range else \
        (datetime.datetime.today() + datetime.timedelta(days=30))
    time_off_records = TimeOffRequest.objects.filter(is_active=True, employee__is_active=True)

    if search:
        try:
            search = int(search)
            time_off_records = time_off_records.filter(employee__employee_id=search)

        except ValueError:
            time_off_records = TimeOffRequest.objects.annotate(
                full_name=Concat('employee__first_name', V(' '), 'employee__last_name',
                                 output_field=CharField())).filter(
                full_name__icontains=search).order_by(sort_by)

    if time_off_type:
        time_off_records = time_off_records.filter(time_off_type__exact=time_off_type)

    if status:
        time_off_records = time_off_records.filter(status__exact=status)

    if company_name:
        time_off_records = time_off_records.filter(employee__company__display_name=company_name)

    if start_date and end_date:
        time_off_records = time_off_records.filter(request_date__gte=start_date, request_date__lte=end_date)

    if sort_by:
        time_off_records = time_off_records.order_by(sort_by)

    f_form = TimeOffFilterForm(data={
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
    if request.method == 'POST':
        company_name = request.POST.get('company')
        date_range = request.POST.get('date_range')
        search = request.POST.get('search')
    else:
        company_name = request.GET.get('company')
        date_range = request.GET.get('date_range')
        search = request.GET.get('search')

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
            termed_drivers = Employee.objects.filter(is_active=False).annotate(
                full_name=Concat('first_name', V(' '), 'last_name', output_field=CharField())).filter(
                full_name__icontains=search)

    if company_name:
        termed_drivers = termed_drivers.filter(company__display_name__exact=company_name)

    if start_date and end_date:
        termed_drivers = termed_drivers.filter(termination_date__gte=start_date, termination_date__lte=end_date)

    f_form = TerminationFilterForm(data={
        'company': company_name,
        'date_range': date_range,
        'search': search
    })

    page = request.GET.get('page')
    paginator = Paginator(termed_drivers.order_by('termination_date'), 25)
    page_obj = paginator.get_page(page)

    data = {
        'page_obj': page_obj,
        'f_form': f_form,
        'start_date': start_date.strftime('%m/%d/%Y'),
        'end_date': end_date.strftime('%m/%d/%Y'),
    }

    return render(request, 'operations/termination_reports.html', data)