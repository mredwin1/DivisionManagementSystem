from django.urls import path
from main import views as main_views


urlpatterns = [
    path('', main_views.employee_info, name='main-home'),
    path('employee-info/', main_views.employee_info, name='main-employee-info'),
    path('export-phone-list/', main_views.export_phone_list, name='main-export-phone-list'),
    path('export-seniority-list/', main_views.export_seniority_list, name='main-export-seniority-list'),
    path('export-driver-list/', main_views.export_driver_list, name='main-export-driver-list'),
    path('export-custom-list/', main_views.export_custom_list, name='main-export-custom-list'),
    path('import-data/', main_views.import_data, name='main-import-data'),
    path('import-driver-data/', main_views.import_driver_data, name='main-import-driver-data'),
    path('import-attendance-data/', main_views.import_attendance_data, name='main-import-attendance-data'),
    path('import-safety-point-data/', main_views.import_safety_point_data, name='main-import-safety-point-data'),
]
