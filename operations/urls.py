from django.urls import path
from . import views as operations_views

urlpatterns = [
    path('home/', operations_views.home, name='operations-home'),
    path('home/<str:attendance_ids>/', operations_views.home, name='operations-home'),
    path('add-employee/', operations_views.add_employee, name='operations-add-employee'),
    path('bulk-assign-attendance/', operations_views.bulk_assign_attendance, name='operations-bulk-assign-attendance'),
    path('bulk-assign-attendance/search-employees/', operations_views.search_employees, name='operations-search-employees'),
    path('attendance-reports/', operations_views.attendance_reports, name='operations-attendance-reports'),
    path('counseling-reports/', operations_views.counseling_reports, name='operations-counseling-reports'),
    path('time-off-reports/', operations_views.time_off_reports, name='operations-time-off-reports'),
    path('time-off-reports/<int:notification_id>/', operations_views.time_off_reports, name='operations-time-off-reports'),
    path('hold-list/', operations_views.view_hold_list, name='operations-hold-list'),
    path('make-time-off-request/', operations_views.make_time_off_request, name='operations-make-time-off-request'),
    path('make-time-off-request/search-employees/', operations_views.search_employees, name='operations-search-employees'),
    path('change-time-off-status/<int:time_off_id>/<str:status>/', operations_views.time_off_status, name='operations-change-time-off-status'),
    path('delete-time-off/<int:time_off_id>/', operations_views.remove_time_off, name='operations-remove-time-off'),
    path('termination-reports/', operations_views.termination_reports, name='operations-termination-reports'),

]
