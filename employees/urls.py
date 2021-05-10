from django.urls import path
from . import views as employee_views

urlpatterns = [
    path('account/<int:employee_id>/', employee_views.account, name='employee-account'),
    path('account/<int:employee_id>/<int:notification_id>/', employee_views.account, name='employee-account'),
    path('edit-phonenumbers/<int:employee_id>/', employee_views.edit_phonenumbers, name='employee-edit-phonenumbers'),
    path('edit-info/<int:employee_id>/', employee_views.edit_employeeinfo, name='employee-edit-info'),
    path('assign-attendance-point/<int:employee_id>/', employee_views.assign_attendance, name='employee-assign-attendance'),
    path('delete-attendance-point/<int:attendance_id>/', employee_views.delete_attendance, name='employee-remove-attendance'),
    path('edit-attendance-point/<int:attendance_id>/', employee_views.edit_attendance, name='employee-edit-attendance'),
    path('counsel-driver/<int:employee_id>/', employee_views.assign_counseling, name='employee-assign-counseling'),
    path('delete-counseling/<int:employee_id>/<int:counseling_id>/', employee_views.delete_counseling, name='employee-remove-counseling'),
    path('edit-counseling/<int:employee_id>/<int:counseling_id>/', employee_views.edit_counseling, name='employee-edit-counseling'),
    path('assign-safety-point/<int:employee_id>/', employee_views.assign_safety_point, name='employee-assign-safety-point'),
    path('delete-safety-point/<int:employee_id>/<int:safety_point_id>/', employee_views.delete_safety_point, name='employee-remove-safety-point'),
    path('edit-safety-point/<int:employee_id>/<int:safety_point_id>/', employee_views.edit_safety_point, name='employee-edit-safety-point'),
    path('place-hold/<int:employee_id>/', employee_views.place_hold, name='employee-place-hold'),
    path('edit-hold/<int:hold_id>/', employee_views.edit_hold, name='employee-edit-hold'),
    path('remove-hold/<int:employee_id>/<int:hold_id>/', employee_views.remove_hold, name='employee-remove-hold'),
    path('termination-settlement/<int:employee_id>/', employee_views.employee_settlement_terminate, name='employee-terminate-settlement'),
    path('terminate-employee/<int:employee_id>/', employee_views.terminate_employee, name='employee-terminate'),
    path('employee-settlement/<int:employee_id>/', employee_views.create_settlement, name='employee-create-settlement'),
    path('delete-settlement/<int:settlement_id>/', employee_views.delete_settlement, name='employee-delete-settlement'),
    path('view-employee-settlement/<int:settlement_id>/', employee_views.view_settlement, name='employee-view-settlement'),
    path('request-time-off/<int:employee_id>/', employee_views.time_off_request, name='employee-time-off-request'),
    path('notification-settings/', employee_views.notification_settings, name='employee-notification-settings'),
    path('export-attendance-history/<int:employee_id>/', employee_views.export_attendance_history, name='employee-export-attendance-history'),
    path('export-counseling-history/<int:employee_id>/', employee_views.export_counseling_history, name='employee-export-counseling-history'),
    path('export-safety-point-history/<int:employee_id>/', employee_views.export_safety_point_history, name='employee-export-safety-point-history'),
    path('export-profile/<int:employee_id>/', employee_views.export_profile, name='employee-export-profile'),
    path('upload-profile-picture/<int:employee_id>/', employee_views.upload_profile_picture, name='employee-upload-profile-picture'),
    path('get-signature/', employee_views.get_signature, name='employee-get-signature'),
    path('sign-document/', employee_views.sign_document, name='employee-sign-document'),
]
