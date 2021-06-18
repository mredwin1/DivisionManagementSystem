import datetime

from django.contrib.auth import settings
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.urls import reverse, NoReverseMatch
from django.utils import timezone
from django.utils.html import strip_tags
from notifications.models import Notification
from notifications.signals import notify
from urllib.parse import urljoin

from employees.models import Attendance, Counseling, SafetyPoint, Hold, Employee, Settlement, TimeOffRequest
from main.tasks import send_email, send_text


@receiver(post_delete, sender=Attendance)
def attendance_delete(sender, instance, **kwargs):
    if instance.exemption == '1':
        instance.employee.paid_sick += 1
    elif instance.exemption == '2':
        instance.employee.unpaid_sick += 1

    instance.employee.save()


@receiver(post_delete, sender=Counseling)
def counseling_delete(sender, instance, **kwargs):
    try:
        instance.employee.hold.delete()
    except Hold.DoesNotExist:
        pass


@receiver(post_delete, sender=SafetyPoint)
def safety_point_delete(sender, instance, **kwargs):
    try:
        instance.employee.hold.delete()
    except Hold.DoesNotExist:
        pass


@receiver(post_delete, sender=Hold)
def hold_delete(sender, instance, **kwargs):
    verb = f'{instance.employee.get_full_name()}\'s hold has been removed'
    notification_type = 'email_rem_hold'

    group = Employee.objects.filter(groups__name=notification_type).exclude(employee_id=instance.assigned_by)
    notify.send(sender=instance, recipient=group,
                verb=verb,
                type=notification_type, employee_id=instance.employee.employee_id)


@receiver(post_save, sender=Hold)
def hold_notification(sender, instance, created,**kwargs):
    if created:
        verb = f'{instance.employee.get_full_name()} has been placed on hold by {instance.get_assignee().get_full_name()}. Reason: {instance.reason}'
        notification_type = 'email_add_hold'

        group = Employee.objects.filter(groups__name=notification_type).exclude(employee_id=instance.assigned_by)
        notify.send(sender=instance, recipient=group,
                    verb=verb,
                    type=notification_type, employee_id=instance.employee.employee_id)


@receiver(post_save, sender=Notification)
def new_notification(sender, instance, created, **kwargs):
    try:
        if created:
            field_name = instance.data['type']
            if field_name == 'email_new_time_off':
                instance.data['url'] = f"{reverse('operations-time-off-reports', args=[instance.id])}?id={instance.data['sender_id']}"
            else:
                instance.data['url'] = reverse('employee-account', args=[instance.data['employee_id'], instance.id])

            instance.save()

            if getattr(instance.recipient, field_name):
                domain = Site.objects.get_current().domain
                data = {
                    'notification_message': instance.verb,
                    'notification_href': domain + instance.data['url'],
                    'preferences_href': domain + reverse('employee-notification-settings'),
                    'logo_url': urljoin(settings.STATIC_URL, 'main/MV_Transportation_logo.png')
                }
                subject = 'New Notification'
                html_message = render_to_string('main/notification_email.html', data)
                plain_message = strip_tags(html_message)
                to = instance.recipient.email

                send_email.delay(subject, plain_message, to, html_message)

                instance.emailed = True

                instance.save()
    except NoReverseMatch:
        pass


@receiver(post_save, sender=Counseling)
def post_save_counseling(sender, instance, created, update_fields, **kwargs):
    if not instance.document and instance.is_active:
        instance.create_counseling_document()

        if created:
            # This needs to be commented out until corporate gives us a Twilio API Key
            # if instance.employee.primary_phone and not instance.is_signed:
            #     body = f'Hello {instance.employee.get_full_name()}, please see operations next time you are at base.'
            #     send_text(str(instance.employee.primary_phone), body, instance.id, 'Counseling')
            # else:
            #     instance.status_update_date = timezone.now()
            #     instance.message_status = 'Unsent'
            #     instance.save()
            instance.status_update_date = timezone.now()
            instance.message_status = 'Unsent'

            if instance.action_type == '2':
                verb = f'{instance.employee.get_full_name()} has received a written warning' if instance.attendance is None else f'{instance.employee.get_full_name()} has received a written warning for reaching 7 Attendance Points'
                notification_type = 'email_written' if instance.attendance is None else 'email_7attendance'

                group = Employee.objects.filter(groups__name=notification_type).exclude(employee_id=instance.assigned_by)
                notify.send(sender=instance, recipient=group,
                            verb=verb,
                            type=notification_type, employee_id=instance.employee.employee_id)
            elif instance.action_type == '4':
                verb = f'{instance.employee.get_full_name()} has received a last and final'
                notification_type = 'email_last_final'

                group = Employee.objects.filter(groups__name=notification_type).exclude(employee_id=instance.assigned_by)
                notify.send(sender=instance, recipient=group,
                            verb=verb,
                            type=notification_type, employee_id=instance.employee.employee_id)

            elif instance.action_type == '6' or instance.action_type == '5':
                verb = f'{instance.employee.get_full_name()} has been Removed from Service'if instance.attendance is None else f'{instance.employee.get_full_name()} has been Removed from Service for reaching 10 Attendance Points'
                notification_type = 'email_removal' if instance.attendance is None else 'email_10attendance'

                group = Employee.objects.filter(groups__name=notification_type).exclude(employee_id=instance.assigned_by)
                notify.send(sender=instance, recipient=group,
                            verb=verb,
                            type=notification_type, employee_id=instance.employee.employee_id)

                if not instance.attendance:
                    try:
                        instance.employee.hold.delete()
                    except Hold.DoesNotExist:
                        pass

                    hold = Hold(
                        reason='Pending Termination',
                        hold_date=datetime.date.today(),
                        assigned_by=instance.assigned_by,
                        employee=instance.employee,
                    )
                    hold.save()

                instance.employee.save()


@receiver(post_save, sender=Attendance)
def post_save_attendance(sender, instance, created, **kwargs):
    if not instance.document and instance.is_active:
        instance.create_document()
        counseling = instance.employee.attendance_counseling_required(instance.reason, instance.exemption, instance.id)

        if counseling[0] == 2 and instance.points != 0:
            latest_attendance = Attendance.objects.filter(employee=instance.employee, points__gt=0, counseling=None).last()
            instance.employee.attendance_removal(counseling, latest_attendance, instance.assigned_by)
        elif counseling[0] == 1 and instance.points != 0:
            latest_attendance = Attendance.objects.filter(employee=instance.employee, points__gt=0, counseling=None).last()
            instance.employee.attendance_written(counseling, latest_attendance, instance.assigned_by)

        if created:
            # This needs to be commented out until corporate gives us a Twilio API Key
            # if instance.employee.primary_phone and not instance.is_signed:
            #     domain = Site.objects.get_current().domain
            #     body = f'Hello {instance.employee.get_full_name()}, you have received an attendance point. Please see a ' \
            #            f'manager to sign the document or go to the link below.\n' \
            #            f'https://{domain}{reverse("employee-sign-document", args=["Self Service", instance.id, "Attendance"])}'
            #     send_text(str(instance.employee.primary_phone), body, instance.id, 'Attendance')
            # else:
            #     instance.status_update_date = timezone.now()
            #     instance.message_status = 'Unsent'
            #     instance.save()
            instance.status_update_date = timezone.now()
            instance.message_status = 'Unsent'
            instance.save()
    else:
        total_points = instance.employee.get_total_attendance_points()
        if total_points < 7:
            attendance_objects = Attendance.objects.filter(employee=instance.employee)
            for attendance_object in attendance_objects:
                try:
                    if attendance_object.counseling.action_type == '2':
                        attendance_object.counseling.delete()
                except Counseling.DoesNotExist:
                    pass
        if total_points < 10:
            attendance_objects = Attendance.objects.filter(employee=instance.employee)
            for attendance_object in attendance_objects:
                try:
                    if attendance_object.counseling.action_type == '6':
                        attendance_object.counseling.delete()
                except Counseling.DoesNotExist:
                    pass


@receiver(post_save, sender=SafetyPoint)
def post_save_safety_point(sender, instance, created, **kwargs):
    if not instance.document and instance.is_active:
        instance.create_safety_point_document()

        if created:
            # This needs to be commented out until corporate gives us a Twilio API Key
            # if instance.employee.primary_phone and not instance.is_signed:
            #     body = f'Hello {instance.employee.get_full_name()}, please see safety next time you are at base.'
            #     send_text(str(instance.employee.primary_phone), body, instance.id, 'SafetyPoint')
            # else:
            #     instance.status_update_date = timezone.now()
            #     instance.message_status = 'Unsent'
            #     instance.save()
            instance.status_update_date = timezone.now()
            instance.message_status = 'Unsent'
            instance.save()
            removal = instance.employee.safety_point_removal_required(instance)

            verb = f'{instance.employee.get_full_name()} has received a Safety Point' if not removal else f'{instance.employee.get_full_name()} has received a Safety Point and been removed from service'
            group = Employee.objects.filter(groups__name='email_safety_point').exclude(employee_id=instance.assigned_by)
            notify.send(sender=instance, recipient=group,
                        verb=verb,
                        type='email_safety_point', employee_id=instance.employee.employee_id)


@receiver(post_save, sender=Settlement)
def add_settlement_document(sender, instance, created, update_fields, **kwargs):
    try:
        if created or 'document' not in update_fields:
            instance.create_settlement_document()

            if created:
                verb = f'New Settlement Created for {instance.employee.get_full_name()}'

                group = Employee.objects.filter(groups__name='email_add_settlement').exclude(employee_id=instance.assigned_by)
                notify.send(sender=instance, recipient=group,
                            verb=verb,
                            type='email_add_settlement', employee_id=instance.employee.employee_id)
    except TypeError:
        pass


@receiver(post_save, sender=TimeOffRequest)
def check_floating_holiday(sender, instance, created, update_fields, **kwargs):
    if instance.time_off_type == '7':
        if update_fields:
            if 'is_active' in update_fields:
                instance.employee.floating_holiday += 1
        elif instance.status != '2':
            instance.employee.floating_holiday -= 1
        elif instance.status == '2':
            instance.employee.floating_holiday += 1
    if created and instance.status == '0':
        verb = f'{instance.employee.get_full_name()} has requested time off'
        notification_type = 'email_new_time_off'

        group = Employee.objects.filter(groups__name=notification_type)
        notify.send(sender=instance, recipient=group,
                    verb=verb, sender_id=instance.id,
                    type=notification_type, employee_id=instance.employee.employee_id)

    instance.employee.save()


@receiver(post_save, sender=Employee)
def add_new_employee(sender, instance, created, update_fields, **kwargs):
    if created:
        verb = f'New Employee added: {instance.get_full_name()}'
        notification_type = 'email_new_employee'
        
        group = Employee.objects.filter(groups__name=notification_type)
        notify.send(sender=instance, recipient=group,
                    verb=verb, type=notification_type, employee_id=instance.employee_id)

        if instance.position == 'dispatcher':
            dispatcher_group = Group.objects.get(name='Dispatchers')
            dispatcher_group.user_set.add(instance)
