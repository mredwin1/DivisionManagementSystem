from io import BytesIO

from django import forms
from crispy_forms.helper import FormHelper
from openpyxl import load_workbook

from employees.models import Company
import os
from zipfile import ZipFile


class DriverFilterForm(forms.Form):
    COMPANY_CHOICES = [('','Filter by Company')]
    POSITION_CHOICES = [
        ('', 'Filter by Position'),
        ('driver', 'Driver'),
        ('driver_scheduler', 'Driver Scheduler'),
        ('hiring_supervisor', 'Hiring Supervisor'),
        ('clerk', 'Clerk'),
        ('assistant_manager', 'Assistant Manager'),
        ('general_manager', 'General Manager'),
        ('it_manager', 'IT Manager')
    ]
    SORT_CHOICES = [
        ('', 'Sort By'),
        ('last_name', 'Last Name'),
        ('first_name', 'First Name'),
        ('employee_id', 'Employee ID'),
        ('position', 'Position'),
        ('hire_date', 'Hire Date'),
    ]

    try:
        companies = Company.objects.all()

        for company in companies:
            company = (company, company)
            COMPANY_CHOICES.append(company)
    except:
        pass

    company = forms.CharField(initial='Filter by Company', widget=forms.Select(choices=COMPANY_CHOICES, attrs={'style':'font-size: 14px', 'onchange': 'form.submit();'}), required=False)
    position = forms.CharField(initial='Filter by Position', widget=forms.Select(choices=POSITION_CHOICES, attrs={'style':'font-size: 14px', 'onchange': 'form.submit();'}), required=False)
    sort_by = forms.CharField(initial='Sort By', widget=forms.Select(choices=SORT_CHOICES, attrs={'style':'font-size: 14px', 'onchange': 'form.submit();'}), required=False)
    search = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'placeholder': 'Search by Name or ID', 'style': 'font-size: 14px'}), required=False)

    def __init__(self, *args, **kwargs):
        super(DriverFilterForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False


class DriverImportForm(forms.Form):
    driver_file_import = forms.FileField(label='File', help_text='Ensure this is a .zip', required=True)

    def clean(self):
        super().clean()

        field_name = 'driver_file_import'
        file = self.files[field_name]
        file_name, file_extension = os.path.splitext(file.name)

        if file_extension != '.zip':
            self.add_error(field_name, f'File must be a zipped folder')
        else:
            with ZipFile(self.files['driver_file_import'], 'r') as zipfile:
                try:
                    driver_info = zipfile.read('drivers/drivers.xlsx')

                    wb = load_workbook(filename=BytesIO(driver_info))

                    try:
                        sheet = wb['data']

                        correct_headers = ['last_name', 'first_name', 'employee_id', 'position', 'hire_date',
                                           'application_date', 'classroom_date', 'company', 'is_partime',
                                           'primary_phone', 'secondary_phone', 'SS']
                        headers = []
                        for col in sheet.iter_cols():
                            headers.append(col[0].value)

                        if headers != correct_headers:
                            self.add_error(field_name, 'Headers are incorrect,'
                                                       ' look at documentation for more information')

                    except KeyError:
                        self.add_error(field_name, 'No sheet named "data"')
                except KeyError:
                    self.add_error(field_name, 'No excel file named "drivers.xlsx"')


class AttendanceImportForm(forms.Form):
    attendance_file_import = forms.FileField(label='File', help_text='Ensure this is a .xlsx', required=True)

    def clean(self):
        super().clean()

        field_name = 'attendance_file_import'
        file = self.cleaned_data[field_name]
        file_name, file_extension = os.path.splitext(file.name)

        if file_extension != '.xlsx':
            self.add_error(field_name, f'File must be a excel file')
        else:
            wb = load_workbook(filename=BytesIO(self.files['attendance_file_import'].read()))

            try:
                sheet = wb['data']

                correct_headers = ['employee_id', 'incident_date', 'reason', 'exemption', 'assigned_by']
                headers = []
                for col in sheet.iter_cols():
                    headers.append(col[0].value)

                if headers != correct_headers:
                    self.add_error(field_name, 'Headers are incorrect,'
                                               ' look at documentation for more information')

            except KeyError:
                self.add_error(field_name, 'No sheet named "data"')


class SafetyPointImportForm(forms.Form):
    safety_point_file_import = forms.FileField(label='File', help_text='Ensure this is a .xlsx', required=True)

    def clean(self):
        super().clean()

        field_name = 'safety_point_file_import'
        file = self.cleaned_data[field_name]
        file_name, file_extension = os.path.splitext(file.name)

        if file_extension != '.xlsx':
            self.add_error(field_name, f'File must be a excel file')
        else:
            wb = load_workbook(filename=BytesIO(self.files['safety_point_file_import'].read()))

            try:
                sheet = wb['data']

                correct_headers = ['employee_id', 'incident_date', 'issued_date', 'reason', 'assigned_by']
                headers = []
                for col in sheet.iter_cols():
                    headers.append(col[0].value)

                if headers != correct_headers:
                    self.add_error(field_name, 'Headers are incorrect,'
                                               ' look at documentation for more information')

            except KeyError:
                self.add_error(field_name, 'No sheet named "data"')
