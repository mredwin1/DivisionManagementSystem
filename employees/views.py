from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from notifications.models import Notification
from django.urls import reverse

from .forms import *
from .models import Employee, SafetyPoint, TimeOffRequest


@login_required
def account(request, employee_id, notification_id=None):
    if employee_id == request.user.employee_id or request.user.has_perm('employees.can_view_all_accounts'):
        employee = Employee.objects.get(employee_id=employee_id)
        attendance = Attendance.objects.filter(employee=employee, is_active=True).order_by('-incident_date')
        counseling = Counseling.objects.filter(employee=employee, is_active=True).order_by('-issued_date')
        safety_point = SafetyPoint.objects.filter(employee=employee, is_active=True).order_by('-incident_date')
        time_off = TimeOffRequest.objects.filter(employee=employee, is_active=True).order_by('-request_date')
        settlements = Settlement.objects.filter(employee=employee, is_active=True).order_by('-created_date')

        data = {
            'employee': employee,
            'attendance': attendance,
            'counseling': counseling,
            'safety_point': safety_point,
            'time_off': time_off,
            'settlements': settlements,
        }

        if notification_id:
            notification = Notification.objects.get(id=notification_id)
            notification.mark_as_read()

        return render(request, 'employees/account.html', data)
    else:
        raise PermissionDenied


@login_required
def edit_phonenumbers(request, employee_id):
    if employee_id == request.user.employee_id or request.user.has_perm('employees.can_view_all_accounts'):
        employee = Employee.objects.get(employee_id=employee_id)
        if request.method == 'GET':

            primary_phone = employee.primary_phone
            secondary_phone = employee.secondary_phone

            p_form = EditPhoneNumbers(initial={'primary_phone': primary_phone, 'secondary_phone': secondary_phone})

            data = {
                'p_form': p_form,
                'employee': employee
            }

            return render(request, 'employees/edit_phone.html', data)
        else:
            p_form = EditPhoneNumbers(request.POST)

            if p_form.is_valid():
                p_form.save(employee)

                messages.add_message(request, messages.SUCCESS, 'Phone Numbers Successfully Updated')

                data = {'url': reverse('employee-account', args=[employee_id])}

                return JsonResponse(data, status=200)
            else:
                return JsonResponse(p_form.errors, status=400)
    else:
        raise PermissionDenied


@login_required
@permission_required('employees.can_edit_employee_info', raise_exception=True)
def edit_employeeinfo(request, employee_id):
    employee = Employee.objects.get(employee_id=employee_id)
    if request.method == 'GET':

        initial = {
            'first_name': employee.first_name,
            'last_name': employee.last_name,
            'employee_id': employee.employee_id,
            'primary_phone': employee.primary_phone,
            'secondary_phone': employee.secondary_phone,
            'hire_date': employee.hire_date,
            'application_date': employee.application_date,
            'classroom_date': employee.classroom_date,
            'company': employee.company,
            'is_part_time': employee.is_part_time,
            'is_neighbor_link': employee.is_neighbor_link,
        }

        e_form = EditEmployeeInfo(initial=initial)

        data = {
            'e_form': e_form,
            'employee': employee
        }

        return render(request, 'employees/edit_info.html', data)
    else:
        e_form = EditEmployeeInfo(request.POST)

        if e_form.is_valid():
            e_form.save(employee)

            messages.add_message(request, messages.SUCCESS, 'Employee Information Updated Successfully')

            data = {'url': reverse('employee-account', args=[employee_id])}

            return JsonResponse(data, status=200)
        else:
            return JsonResponse(e_form.errors, status=400)


@login_required
@permission_required('employees.can_assign_attendance', raise_exception=True)
def assign_attendance(request, employee_id):
    employee = Employee.objects.get(employee_id=employee_id)
    if request.method == 'GET':

        form = AssignAttendance(employee=employee, request=request)

        data = {
            'form': form,
            'employee': employee,
            'domain': Site.objects.get_current().domain
        }

        return render(request, 'employees/attendance.html', data)
    else:
        form = AssignAttendance(data=request.POST, employee=employee, request=request)
        if form.is_valid():
            form.save()

            messages.add_message(request, messages.SUCCESS, 'Attendance Point Successfully Assigned')

            data = {'url': reverse('employee-account', args=[employee.employee_id])}

            return JsonResponse(data, status=200)
        else:

            return JsonResponse(form.errors, status=400)


@login_required
@permission_required('employees.can_delete_attendance', raise_exception=True)
def delete_attendance(request, attendance_id):
    attendance = Attendance.objects.get(id=attendance_id)
    exemption = attendance.exemption
    employee = attendance.employee

    attendance.is_active = False

    try:
        attendance.counseling.is_active = False
        attendance.counseling.save(update_fields=['is_active'])
    except Counseling.DoesNotExist:
        pass

    attendance.save(update_fields=['is_active'])

    if exemption == '1':
        employee.paid_sick += 1
    elif exemption == '2':
        employee.unpaid_sick += 1

    employee.save()

    messages.add_message(request, messages.SUCCESS, 'Attendance Point Deleted Successfully')

    return redirect('employee-account', attendance.employee.employee_id)


@login_required
@permission_required('employees.can_edit_attendance', raise_exception=True)
def edit_attendance(request, attendance_id):
    attendance = Attendance.objects.get(id=attendance_id)
    employee = attendance.employee

    if request.method == 'POST':
        form = EditAttendance(data=request.POST, files=request.FILES, employee=employee,
                              attendance=attendance, request=request)

        if form.is_valid():
            form.save()

            data = {'url': reverse('employee-account', args=[employee.employee_id])}

            return JsonResponse(data, status=200)
        else:

            return JsonResponse(form.errors, status=400)
    else:
        initial = {
            'incident_date': attendance.incident_date,
            'reason': attendance.reason,
            'exemption': attendance.exemption,
            'issued_date': attendance.issued_date,
        }

        form = EditAttendance(initial=initial, employee=employee)

        data = {
            'employee': employee,
            'form': form,
            'attendance': attendance,
            'domain': Site.objects.get_current().domain
        }

        return render(request, 'employees/attendance.html', data)


@login_required
@permission_required('employees.can_assign_counseling', raise_exception=True)
def assign_counseling(request, employee_id):
    employee = Employee.objects.get(employee_id=employee_id)

    if request.method == 'POST':
        c_form = AssignCounseling(data=request.POST, employee=employee, request=request)

        if c_form.is_valid():
            counseling_id = c_form.save()

            messages.add_message(request, messages.SUCCESS, 'Counseling Successfully Added')

            data = {
                'url': reverse('employee-account', args=[employee_id, 'Counseling', counseling_id])
            }

            return JsonResponse(data, status=200)
        else:

            return JsonResponse(c_form.errors, status=400)
    else:
        c_form = AssignCounseling(employee=employee)

        data = {
            'employee': employee,
            'c_form': c_form
        }

        return render(request, 'employees/assign_counseling.html', data)


@login_required
@permission_required('employees.can_delete_attendance', raise_exception=True)
def delete_counseling(request, employee_id, counseling_id):
    counseling = Counseling.objects.get(id=counseling_id)

    counseling.is_active = False

    counseling.save(update_fields=['is_active', 'document'])

    messages.add_message(request, messages.SUCCESS, 'Counseling Successfully Deleted')

    return redirect('employee-account', employee_id)


@login_required
@permission_required('employees.can_edit_counseling', raise_exception=True)
def edit_counseling(request, employee_id, counseling_id):
    counseling = Counseling.objects.get(id=counseling_id)

    if request.method == 'POST':
        c_form = EditCounseling(data=request.POST, files=request.FILES, request=request, counseling=counseling)

        if c_form.is_valid():
            c_form.save()

            messages.add_message(request, messages.SUCCESS, 'Counseling Edited Successfully')

            data = {'url': reverse('employee-account', args=[employee_id, 'Counseling', counseling_id])}

            return JsonResponse(data, status=200)
        else:
            return JsonResponse(c_form.errors, status=400)
    else:
        initial = {
            'issued_date': counseling.issued_date,
            'action_type': counseling.action_type,
            'hearing_date': counseling.hearing_datetime.astimezone(timezone('UTC')).date() if counseling.hearing_datetime else None,
            'hearing_time': counseling.hearing_datetime.astimezone(timezone('UTC')).time() if counseling.hearing_datetime else datetime.time(hour=10),
            'conduct': counseling.conduct,
            'conversation': counseling.conversation
        }

        c_form = EditCounseling(initial=initial, counseling=counseling)

        data = {
            'counseling': counseling,
            'c_form': c_form,
        }

        return render(request, 'employees/edit_counseling.html', data)


@login_required
@permission_required('employees.can_assign_safety_point', raise_exception=True)
def assign_safety_point(request, employee_id):
    employee = Employee.objects.get(employee_id=employee_id)

    if request.method == 'POST':
        s_form = AssignSafetyPoint(request.POST, employee=employee, request=request)

        if s_form.is_valid():
            safety_point_id = s_form.save()

            messages.add_message(request, messages.SUCCESS, 'Safety Point Successfully Assigned')

            data = {'url': reverse('employee-account', args=[employee_id, 'Safety Point', safety_point_id])}

            return JsonResponse(data, status=200)
        else:

            return JsonResponse(s_form.errors, status=400)

    else:
        s_form = AssignSafetyPoint(initial={'issued_date': datetime.date.today()})

        data = {
            'employee': employee,
            's_form': s_form
        }

        return render(request, 'employees/assign_safety_point.html', data)


@login_required
@permission_required('employees.can_delete_attendance', raise_exception=True)
def delete_safety_point(request, employee_id, safety_point_id):
    safety_point = SafetyPoint.objects.get(id=safety_point_id)

    safety_point.is_active = False

    try:
        safety_point.counseling.is_active = False
        safety_point.counseling.save(update_fields=['document', 'is_active'])
    except Counseling.DoesNotExist:
        pass

    safety_point.save(update_fields=['is_active', 'document'])

    messages.add_message(request, messages.SUCCESS, 'Safety Point Successfully Deleted')

    return redirect('employee-account', employee_id)


@login_required
@permission_required('employees.can_edit_safety_point', raise_exception=True)
def edit_safety_point(request, employee_id, safety_point_id):
    safety_point = SafetyPoint.objects.get(id=safety_point_id)
    employee = Employee.objects.get(employee_id=employee_id)

    if request.method == 'POST':
        s_form = EditSafetyPoint(data=request.POST, files=request.FILES)

        if s_form.is_valid():
            s_form.save(safety_point, request)

            messages.add_message(request, messages.SUCCESS, 'Safety Point Edited Successfully')

            data = {'url': reverse('employee-account', args=[employee_id, 'Safety Point', safety_point_id])}

            return JsonResponse(data, status=200)

        else:
            return JsonResponse(s_form.errors, status=400)
    else:
        initial = {
            'incident_date': safety_point.incident_date,
            'issued_date': safety_point.issued_date,
            'reason': safety_point.reason,
            'unsafe_act': safety_point.unsafe_act,
            'details': safety_point.details
        }

        s_form = EditSafetyPoint(initial=initial)

        data = {
            'employee': employee,
            's_form': s_form,
        }

        return render(request, 'employees/edit_safety_point.html', data)


@login_required
@permission_required('employees.can_place_hold', raise_exception=True)
def place_hold(request, employee_id):
    employee = Employee.objects.get(employee_id=employee_id)

    if request.method == 'POST':
        h_form = PlaceHold(request, employee=employee, data=request.POST)

        if h_form.is_valid():
            h_form.save()

            data = {'url': reverse('employee-account', args=[employee_id])}

            return JsonResponse(data, status=200)
        else:
            return JsonResponse(h_form.errors, status=400)
    else:
        h_form = PlaceHold(request, employee=employee)

        data = {
            'employee': employee,
            'h_form': h_form
        }

        return render(request, 'employees/place_hold.html', data)


@permission_required('employees.can_place_hold', raise_exception=True)
def edit_hold(request, hold_id):
    hold = Hold.objects.get(id=hold_id)
    h_form = EditHold(request, hold, data=request.POST)

    if h_form.is_valid():
        h_form.save()
        return JsonResponse({}, status=200)
    else:
        return JsonResponse(h_form.errors, status=400)


@login_required
@permission_required('employees.can_remove_hold', raise_exception=True)
def remove_hold(request, employee_id, hold_id):
    hold = Hold.objects.get(id=hold_id)

    if hold.reason == 'Pending Termination':
        hold.employee.removal_date = None

        hold.employee.save()

    hold.delete()

    return redirect('employee-account', employee_id)


@login_required
@permission_required('employees.can_terminate_employee', raise_exception=True)
def employee_settlement_terminate(request, employee_id):
    employee = Employee.objects.get(employee_id=employee_id)

    t_form = TerminateEmployee()
    s_form = AssignSettlement()

    data = {
        'employee': employee,
        't_form': t_form,
        's_form': s_form
    }

    return render(request, 'employees/terminate_employee.html', data)


@login_required
@permission_required('employees.can_terminate_employee', raise_exception=True)
def terminate_employee(request, employee_id):
    employee = Employee.objects.get(employee_id=employee_id)
    t_form = TerminateEmployee(request.POST)
    if t_form.is_valid():
        t_form.save(employee)

        messages.add_message(request, messages.SUCCESS, 'Driver successfully terminated')

        data = {'url': reverse('main-home')}

        return JsonResponse(data, status=200)
    else:
        return JsonResponse(t_form.errors, status=400)


@login_required
@permission_required('employees.can_create_settlement', raise_exception=True)
def create_settlement(request, employee_id):
    employee = Employee.objects.get(employee_id=employee_id)
    s_form = AssignSettlement(request.POST)
    if s_form.is_valid():
        s_form.save(request, employee)

        messages.add_message(request, messages.SUCCESS, 'Settlement successfully created')

        data = {'url': reverse('employee-account', args=[employee_id])}

        return JsonResponse(data, status=200)
    else:

        return JsonResponse(s_form.errors, status=400)


@login_required
@permission_required('employees.can_view_settlement', raise_exception=True)
def view_settlement(request, settlement_id):
    settlement = Settlement.objects.get(id=settlement_id)
    if request.method == 'POST':
        s_form = ViewSettlement(instance=settlement, data=request.POST, files=request.FILES)
        if s_form.is_valid():
            update_fields = ['details', 'assigned_by', 'created_date']
            settlement_object = s_form.save(commit=False)

            if request.FILES:
                update_fields.append('document')
                settlement.uploaded = True
                settlement.save()

            settlement_object.save(update_fields=update_fields)

            data = {'url': reverse('employee-account', args=[settlement.employee.employee_id])}

            return JsonResponse(data, status=200)
        else:
            return JsonResponse(s_form.errors, status=400)
    else:
        s_form = ViewSettlement(instance=settlement)
        data = {
            'employee': settlement.employee,
            's_form': s_form
        }

        return render(request, 'employees/view_settlement.html', data)


@login_required
@permission_required('employees.can_create_settlement', raise_exception=True)
def delete_settlement(request, settlement_id):
    settlement = Settlement.objects.get(id=settlement_id)

    settlement.is_active = False
    settlement.save(update_fields=['is_active', 'document'])

    return redirect('employee-account', settlement.employee.employee_id)


@login_required
def time_off_request(request, employee_id):
    if employee_id == request.user.employee_id or request.user.has_perm('employees.can_add_time_off_request'):
        employee = Employee.objects.get(employee_id=employee_id)
        if request.method == 'POST':
            form = TimeOffRequestForm(data=request.POST, employee=employee)
            if form.is_valid():
                form.save(employee)

                data = {'url': reverse('employee-account', args=[employee_id])}

                return JsonResponse(data, status=200)
            else:

                return JsonResponse(form.errors, status=400)
        else:
            data = {
                'employee': employee,
                'form': TimeOffRequestForm(),
            }

            return render(request, 'employees/time_off_request.html', data)
    else:
        raise PermissionDenied


@login_required
def notification_settings(request):
    if request.method == 'POST':
        form = NotificationSettings(data=request.POST, instance=request.user)
        if form.is_valid():
            form.save()

            data = {'url': reverse('main-home')}

            return JsonResponse(data, status=200)
    else:
        form = NotificationSettings(instance=request.user)

        return render(request, 'employees/notification_settings.html', {'form': form})


@login_required
@permission_required('employees.can_export_attendance_history', raise_exception=True)
def export_attendance_history(request, employee_id):
    employee = Employee.objects.get(employee_id=employee_id)

    try:
        filename = f'{employee.first_name} {employee.last_name} Attendance History.pdf'

        response = HttpResponse(employee.create_attendance_history_document(), content_type='application/force-download')
        response['Content-Disposition'] = f'attachment;filename="{filename}"'

        return response
    except:
        messages.add_message(request, messages.ERROR, 'No File to Download')

        return redirect('employee-account', employee_id)


@login_required
@permission_required('employees.can_export_counseling_history', raise_exception=True)
def export_counseling_history(request, employee_id):
    employee = Employee.objects.get(employee_id=employee_id)

    try:
        filename = f'{employee.first_name} {employee.last_name} Counseling History.pdf'

        counseling_history = employee.create_counseling_history_document()

        response = HttpResponse(counseling_history, content_type='application/force-download')
        response['Content-Disposition'] = f'attachment;filename="{filename}"'

        return response
    except:
        messages.add_message(request, messages.ERROR, 'No File to Download')

        return redirect('employee-account', employee_id)


@login_required
@permission_required('employees.can_export_safety_point_history', raise_exception=True)
def export_safety_point_history(request, employee_id):
    employee = Employee.objects.get(employee_id=employee_id)

    try:
        filename = f'{employee.first_name} {employee.last_name} Safety Point History.pdf'

        safety_point_history = employee.create_safety_point_history_document()

        response = HttpResponse(safety_point_history, content_type='application/force-download')
        response['Content-Disposition'] = f'attachment;filename="{filename}"'

        return response
    except:
        messages.add_message(request, messages.ERROR, 'No File to Download')

        return redirect('employee-account', employee_id)


@login_required
@permission_required('employees.can_export_profile', raise_exception=True)
def export_profile(request, employee_id):
    employee = Employee.objects.get(employee_id=employee_id)

    filename = f'{employee.first_name} {employee.last_name} Profile History.pdf'

    response = HttpResponse(employee.create_profile_history_document(), content_type='application/force-download')
    response['Content-Disposition'] = f'attachment;filename="{filename}"'

    return response
    # except:
    #     messages.add_message(request, messages.ERROR, 'No File to Download')
    #
    #     return redirect('employee-account', employee_id)


@login_required
@permission_required('employees.can_upload_profile_picture', raise_exception=True)
def upload_profile_picture(request, employee_id):
    employee = Employee.objects.get(employee_id=employee_id)
    if request.method == "POST":
        p_form = UploadProfilePicture(instance=employee, files=request.FILES)
        if p_form.is_valid():
            p_form.save()

            data = {'url': reverse('employee-account', args=[employee_id])}

            return JsonResponse(data, status=200)
        else:
            return JsonResponse(p_form.errors, status=400)

    else:
        p_form = UploadProfilePicture(instance=employee)

        data = {
            'employee': employee,
            'p_form': p_form
        }

        return render(request, 'employees/upload_profile_picture.html', data)


@login_required
def get_signature(request, employee_id=None):
    employee = Employee.objects.get(employee_id=employee_id) if employee_id else request.user

    data = {
        'signature': employee.signature
    }
    return JsonResponse(data, status=200)


def clear_signature(request, employee_id):
    employee = Employee.objects.get(employee_id=employee_id)
    employee.set_signature('')

    return JsonResponse('Success', status=200)


def sign_document(request, signature_method, record_id, document_type=None):
    if signature_method == 'QR':
        employee = Employee.objects.get(id=record_id)

        if request.method == 'GET':
            data = {
                'signature_method': signature_method,
                'record': employee,
                'document_type': None
            }

            return render(request, 'employees/sign_document.html', data)
        else:
            signature = request.POST.get('other_signature')
            employee.set_signature(signature)

            data = {
                'url': reverse('main-home')
            }

            return JsonResponse(data, status=200)
    else:
        if document_type == 'Attendance':
            record = Attendance.objects.get(id=record_id)
        else:
            record = Employee.objects.get(id=record_id)

        if request.method == 'GET':
            data = {
                'document_type': document_type,
                'signature_method': signature_method,
                'record': record
            }

            return render(request, 'employees/sign_document.html', data)
        else:
            signature = request.POST.get('other_signature')
            record.signature = signature
            record.signature_method = signature_method
            record.document.delete()

            data = {
                'url': reverse('employee-account', args=[record.employee.employee_id])
            }

            return JsonResponse(data, status=200)
