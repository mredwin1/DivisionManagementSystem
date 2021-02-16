import uuid
import os

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from django.db.models import CharField, Value as V
from django.db.models.functions import Concat
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse

from employees.helper_functions import create_phone_list, create_seniority_list, create_driver_list, create_custom_list
from employees.models import Employee
from .forms import DriverFilterForm, DriverImportForm, AttendanceImportForm, SafetyPointImportForm
from .tasks import import_drivers, import_attendance, import_safety_points


def home(request):
    return render(request, 'main/home.html')


def log_in(request):
    if request.method == 'GET':
        form = AuthenticationForm()

        return render(request, 'main/login.html', {'form': form})
    else:
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            login(request, user)
            if user.has_perm('employees.can_view_employee_info'):
                return redirect('main-employee-info')
            else:
                return redirect('employee-account', user.employee_id)
        else:
            return render(request, 'main/login.html', {'form': form})


@login_required
@permission_required('employees.can_view_employee_info', raise_exception=True)
def employee_info(request):
    company_name = request.GET.get('company')
    search = request.GET.get('search')
    sort_by = request.GET.get('sort_by')
    position = request.GET.get('position')

    f_form = DriverFilterForm(data={
        'sort_by': sort_by,
        'search': search,
        'company': company_name,
        'position': position
    })

    employees = Employee.objects.filter(is_active=True)
    if search:
        try:
            search = int(search)

            employees = employees.filter(employee_id__exact=search)

        except ValueError:
            employees = Employee.objects.annotate(
                full_name=Concat('first_name', V(' '), 'last_name', output_field=CharField())).filter(
                full_name__icontains=search, is_active=True)

    if company_name:
        employees = employees.filter(company__display_name__exact=company_name)

    if position:
        employees = employees.filter(position__exact=position)

    if sort_by:
        employees = employees.order_by(sort_by)

    page = request.GET.get('page')
    paginator = Paginator(employees, 25)
    page_obj = paginator.get_page(page)

    data = {
        'page_obj': page_obj,
        'f_form': f_form
    }

    return render(request, 'main/employee_info.html', data)


@login_required
@permission_required('employees.can_export_phone_list', raise_exception=True)
def export_phone_list(request):
    employees = Employee.objects.filter(is_active=True, position='driver').order_by('last_name')
    phone_list = create_phone_list(employees)

    filename = 'Division 12 - Phone List.pdf'

    response = HttpResponse(phone_list, content_type='application/force-download')
    response['Content-Disposition'] = f'attachment;filename="{filename}"'

    return response


@login_required
@permission_required('employees.can_export_seniority_list', raise_exception=True)
def export_seniority_list(request):
    employees = Employee.objects.filter(is_active=True, position='driver').order_by('hire_date', 'application_date')
    seniority_list = create_seniority_list(employees)

    filename = 'Division 12 - Seniority List.pdf'

    response = HttpResponse(seniority_list, content_type='application/force-download')
    response['Content-Disposition'] = f'attachment;filename="{filename}"'

    return response


@login_required
@permission_required('employees.can_export_driver_list', raise_exception=True)
def export_driver_list(request):
    employees = Employee.objects.filter(is_active=True, position='driver').order_by('last_name')
    driver_list = create_driver_list(employees)

    filename = 'Division 12 - Driver List.pdf'

    response = HttpResponse(driver_list, content_type='application/force-download')
    response['Content-Disposition'] = f'attachment;filename="{filename}"'

    return response


@login_required
@permission_required('employees.can_export_main_custom_list', raise_exception=True)
def export_custom_list(request):
    company_name = request.POST.get('company')
    search = request.POST.get('search')
    sort_by = request.POST.get('sort_by') if request.POST.get('sort_by') else 'last_name'
    position = request.POST.get('position')

    employees = Employee.objects.filter(is_active=True).order_by(sort_by)
    if search:
        try:
            search = int(search)

            employees = employees.filter(employee_id__exact=search)

        except ValueError:
            employees = Employee.objects.annotate(
                full_name=Concat('first_name', V(' '), 'last_name', output_field=CharField())).filter(
                full_name__icontains=search, is_active=True).order_by(sort_by)

    if company_name:
        employees = employees.filter(company__display_name__exact=company_name)

    if position:
        employees = employees.filter(position__exact=position)

    custom_list = create_custom_list(employees)

    filename = 'Division 12 - Custom List.pdf'

    response = HttpResponse(custom_list, content_type='application/force-download')
    response['Content-Disposition'] = f'attachment;filename="{filename}"'

    return response


@login_required
@permission_required('employees.can_view_import_data', raise_exception=True)
def import_data(request):
    d_form = DriverImportForm()
    a_form = AttendanceImportForm()
    s_form = SafetyPointImportForm()

    data = {
        'd_form': d_form,
        'a_form': a_form,
        's_form': s_form
    }

    return render(request, 'main/data_import.html', data)


@login_required
@permission_required('employees.can_import_driver_data', raise_exception=True)
def import_driver_data(request):
    d_form = DriverImportForm(request.POST, request.FILES)

    if d_form.is_valid():
        temp_file = open(f'shared_volume/{str(uuid.uuid4())}', 'wb')
        for chunk in request.FILES["driver_file_import"].chunks():
            temp_file.write(chunk)
        temp_file.close()

        import_drivers.delay(os.path.realpath(temp_file.name))

        messages.add_message(request, messages.SUCCESS, 'File uploaded successfully. '
                                                        'Driver data will import in the background')

        data = {'url': reverse('main-employee-info')}

        return JsonResponse(data, status=200)
    else:
        return JsonResponse(d_form.errors, status=400)


@login_required
@permission_required('employees.can_import_attendance_data', raise_exception=True)
def import_attendance_data(request):
    a_form = AttendanceImportForm(request.POST, request.FILES)

    if a_form.is_valid():
        temp_file = open(f'shared_volume/{str(uuid.uuid4())}', 'wb')
        for chunk in request.FILES["attendance_file_import"].chunks():
            temp_file.write(chunk)
        temp_file.close()

        import_attendance.delay(os.path.realpath(temp_file.name))

        messages.add_message(request, messages.SUCCESS, f'File uploaded successfully. '
                                                        f'Driver data will import in the background')

        data = {'url': reverse('main-home')}

        return JsonResponse(data, status=200)
    else:
        return JsonResponse(a_form.errors, status=400)


@login_required
@permission_required('employees.can_import_safety_point_data', raise_exception=True)
def import_safety_point_data(request):
    s_form = SafetyPointImportForm(request.POST, request.FILES)

    if s_form.is_valid():
        temp_file = open(f'shared_volume/{str(uuid.uuid4())}', 'wb')
        for chunk in request.FILES["safety_point_file_import"].chunks():
            temp_file.write(chunk)
        temp_file.close()

        import_safety_points.delay(os.path.realpath(temp_file.name))

        messages.add_message(request, messages.SUCCESS, f'File uploaded successfully. '
                                                        f'Driver data will import in the background')

        data = {'url': reverse('main-home')}

        return JsonResponse(data, status=200)
    else:
        return JsonResponse(s_form.errors, status=400)
