from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Company, Employee, Counseling, Attendance, SafetyPoint, TimeOffRequest, Settlement, Hold


class EmployeeAdmin(UserAdmin):
    model = Employee
    list_display = ('first_name', 'last_name', 'company', 'employee_id')
    list_filter = [
        ('is_active', admin.BooleanFieldListFilter),
        ('company', admin.RelatedOnlyFieldListFilter),
        ]
    search_fields = ['first_name', 'last_name']

    fieldsets = (
        ('General Information', {
            'fields': (
                ('is_active', 'is_superuser', 'is_staff'),
                ('username', 'password'),
                ('first_name', 'last_name', 'email'),
                ('employee_id', 'company', 'position'),
                ('primary_phone', 'secondary_phone'),
                ('paid_sick', 'unpaid_sick', 'floating_holiday'),
                'hire_date',
            )
        }),
        ('Groups and Permissions', {
            'classes': ('collapse',),
            'fields': (
                'groups',
                'user_permissions'
            )
        }),
        ('Other Infomation', {
            'classes': ('collapse',),
            'fields': (
                ('is_pending_term'),
                ('termination_date', 'termination_type'),
                ('termination_comments')
            )
        })
    )


admin.site.register(Company)
admin.site.register(Employee, EmployeeAdmin)
admin.site.register(Counseling)
admin.site.register(Attendance)
admin.site.register(SafetyPoint)
admin.site.register(TimeOffRequest)
admin.site.register(Settlement)
admin.site.register(Hold)
