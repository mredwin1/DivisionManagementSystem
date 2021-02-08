import datetime

from bootstrap_daterangepicker import widgets, fields
from crispy_forms.helper import FormHelper
from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import CharField, Value as V
from django.db.models.functions import Concat
from phonenumber_field.formfields import PhoneNumberField

from employees.models import Company, Employee, Attendance, TimeOffRequest, DayOff, Counseling


class EmployeeCreationForm(forms.Form):
    first_name = forms.CharField(label='First Name', required=True, max_length=30)
    last_name = forms.CharField(label='Last Name', required=True, max_length=30)
    position = forms.CharField(label='Position', widget=forms.Select(choices=Employee.POSITION_CHOICES,
                                                                     attrs={'onchange': 'email_change()'}),
                               required=True, max_length=30)

    employee_id = forms.IntegerField(label='Employee ID', required=True)
    last4_ss = forms.IntegerField(label='Last 4 of SS', required=True, help_text='This is only used for password '
                                                                                 'purposes and it is not stored.')
    primary_phone = PhoneNumberField(label='Primary Phone', required=True)
    secondary_phone = PhoneNumberField(label='Secondary Phone', required=False)

    hire_date = forms.DateField(label='Hire Date', widget=forms.TextInput(attrs={'type': 'date'}), required=True)
    application_date = forms.DateField(label='Application Date', widget=forms.TextInput(attrs={'type': 'date'}),
                                       required=True)
    classroom_date = forms.DateField(label='Classroom Date', widget=forms.TextInput(attrs={'type': 'date'}),
                                     required=True)
    email = forms.EmailField(label='Email', widget=forms.TextInput(attrs={'class': 'textinput textInput form-control',
                                                                          'required': ''}), required=False)

    company = forms.CharField(label='Company', required=True)

    is_part_time = forms.BooleanField(label='Part Time', initial=False, required=False)
    is_neighbor_link = forms.BooleanField(label='NeighborLink Driver', initial=False, required=False)

    def __init__(self, *args, **kwargs):
        super(EmployeeCreationForm, self).__init__(*args, **kwargs)
        company_choices = [(company.display_name, company.display_name) for company in Company.objects.all()]
        company_choices.insert(0, ('', ''))

        self.fields['company'].widget = forms.Select(choices=company_choices)

    def clean(self):
        employee_ids = [employee.employee_id for employee in Employee.objects.all()]

        employee_id_field = 'employee_id'
        employee_id = self.cleaned_data[employee_id_field]

        if employee_id in employee_ids:
            self.add_error(employee_id_field, 'This employee id already exists')

    def save(self):
        company = Company.objects.get(display_name=self.cleaned_data['company'])
        first_name = self.cleaned_data['first_name']
        last_name = self.cleaned_data['last_name']

        if self.cleaned_data['email']:
            username = f'{first_name.lower()}.{last_name.lower()}'
        else:
            username = self.cleaned_data['employee_id']

        new_employee = Employee(
            first_name=first_name,
            last_name=last_name,
            employee_id=self.cleaned_data['employee_id'],
            primary_phone=self.cleaned_data['primary_phone'],
            secondary_phone=self.cleaned_data['secondary_phone'],
            hire_date=self.cleaned_data['hire_date'],
            application_date=self.cleaned_data['application_date'],
            classroom_date=self.cleaned_data['classroom_date'],
            company=company,
            is_part_time=self.cleaned_data['is_part_time'],
            is_neighbor_link=self.cleaned_data['is_neighbor_link'],
            username=username,
            position=self.cleaned_data['position'],
            email=self.cleaned_data['email']
        )

        password = "{0}{1}{2}{3}".format(self.cleaned_data['company'].upper(),
                                         self.cleaned_data['first_name'][0].upper(),
                                         self.cleaned_data['last_name'][0].upper(), str(self.cleaned_data['last4_ss']))

        new_employee.set_password(password)

        new_employee.save()

        return new_employee


class BulkAssignAttendance(forms.Form):
    employee_name1 = forms.CharField(required=True, widget=forms.TextInput(
        attrs={'class': 'form-control basicAutoComplete', 'data-url': 'search-employees/',
               'autocomplete': 'off', 'oninput': 'addRow(this);'}))
    incident_date1 = forms.DateField(widget=forms.TextInput(attrs={'type': 'date', 'onchange': 'addRow(this);'}),
                                     required=True)
    reason1 = forms.CharField(
        widget=forms.Select(choices=Attendance.REASON_CHOICES, attrs={'onchange': 'addRow(this);'}), required=True)
    exemption1 = forms.CharField(widget=forms.Select(choices=Attendance.EXEMPTION_CHOICES), required=False)

    def get_all_fields(self):
        counter = 0
        field_list = []
        temp_list = []
        for field_name in self.fields:
            temp_list.append(self[field_name])
            counter += 1
            if counter == 4:
                field_list.append(temp_list)
                temp_list = []
                counter = 0

        return field_list

    def __init__(self, data=None, *args, **kwargs):
        super(BulkAssignAttendance, self).__init__(data, *args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False

        if data:
            for key, value in data.items():
                if key[:-1] == 'employee_name':
                    if value:
                        self.fields[key] = forms.CharField(required=True, widget=forms.TextInput(
                            attrs={'class': 'form-control basicAutoComplete', 'data-url': 'search-employees/',
                                   'autocomplete': 'off', 'oninput': 'addRow(this);'}))
                        self.initial[key] = value
                    else:
                        self.fields[key] = forms.CharField(required=False, widget=forms.TextInput(
                            attrs={'class': 'form-control basicAutoComplete', 'data-url': 'search-employees/',
                                   'autocomplete': 'off', 'oninput': 'addRow(this);'}))
                elif key[:-1] == 'incident_date':
                    if value:
                        self.fields[key] = forms.DateField(widget=forms.TextInput(
                            attrs={'type': 'date', 'onchange': 'addRow(this);'}),
                            required=True)
                        self.initial[key] = value
                    else:
                        self.fields[key] = forms.DateField(widget=forms.TextInput(
                            attrs={'type': 'date', 'onchange': 'addRow(this);'}),
                            required=False)
                elif key[:-1] == 'reason':
                    if value:
                        self.fields[key] = forms.CharField(widget=forms.Select(
                            choices=Attendance.REASON_CHOICES, attrs={'onchange': 'addRow(this);'}), required=True)
                        self.initial[key] = value
                    else:
                        self.fields[key] = forms.CharField(widget=forms.Select(
                            choices=Attendance.REASON_CHOICES, attrs={'onchange': 'addRow(this);'}), required=False)
                elif key[:-1] == 'exemption':
                    self.fields[key] = forms.CharField(widget=forms.Select(choices=Attendance.EXEMPTION_CHOICES),
                                                       required=False)
                    self.initial[key] = value

    def clean(self):
        super().clean()

        employees = Employee.objects.filter(is_active=True).annotate(
            full_name=Concat('first_name', V(' '), 'last_name', output_field=CharField()))

        employee_names = [f'{employee.last_name}, {employee.first_name} | {employee.employee_id}' for employee in
                          employees]

        i = 1
        field_name = f'employee_name{i}'

        while self.cleaned_data.get(field_name):
            employee_name = self.cleaned_data[field_name]

            if employee_name not in employee_names:
                self.add_error(field_name, f'Employee \"{employee_name}\" not in database')

            i += 1
            field_name = f'employee_name{i}'

    def save(self, request):
        points = {
            '0': 1,
            '1': 0,
            '2': 1.5,
            '3': 4,
            '4': 1,
            '5': 1,
            '6': .5,
            '7': 1,
            '8': .5,
        }

        attendance_ids = []
        temp_list = []
        field_sets = []
        i = 0

        # Populates field_sets with a list containing 4 fields
        for field_name in self.cleaned_data.keys():
            if field_name[:-1] == 'employee_name' and self.cleaned_data[field_name] == '':
                pass
            else:
                temp_list.append(field_name)
                i += 1
                if i == 4:
                    field_sets.append(temp_list)
                    temp_list = []
                    i = 0

        for field_set in field_sets:
            employee_name = self.cleaned_data[field_set[0]]
            index = employee_name.find('|')
            employee_id = employee_name[index + 2:]
            employee = Employee.objects.get(employee_id=employee_id)
            incident_date = self.cleaned_data[field_set[1]]
            reason = self.cleaned_data[field_set[2]]
            exemption = self.cleaned_data[field_set[3]]
            point = 0 if exemption else points[reason]
            reported_by = request.user.employee_id

            attendance = Attendance(
                employee=employee,
                incident_date=incident_date,
                issued_date=datetime.date.today(),
                points=point,
                reason=reason,
                assigned_by=reported_by,
                exemption=exemption,
            )

            attendance.save()

            attendance_ids.append(str(attendance.id))

        return ','.join(attendance_ids)


class MakeTimeOffRequest(forms.Form):
    employee_name = forms.CharField(label='Employee Name', required=True, widget=forms.TextInput(
        attrs={'class': 'form-control basicAutoComplete', 'data-url': 'search-employees/',
               'autocomplete': 'off'}))
    request_date = forms.DateField(label='Request Date', help_text='Date time off request form was submitted',
                                   widget=forms.TextInput(attrs={'type': 'date'}), required=True)
    requested_dates = forms.CharField(label='Dates Requested Off', widget=forms.TextInput())
    time_off_type = forms.CharField(label='Type of Time Off',
                                    widget=forms.Select(choices=TimeOffRequest.TIME_OFF_CHOICES), required=True)
    status = forms.CharField(label='Status', widget=forms.Select(choices=TimeOffRequest.STATUS_CHOICES), required=True)
    reason = forms.CharField(label='Reason for Time Off', widget=forms.Textarea(), required=False)
    comments = forms.CharField(label='Comments/Special Instructions', widget=forms.Textarea(), required=False)

    def clean(self):
        super().clean()

        employees = Employee.objects.filter(is_active=True).annotate(
            full_name=Concat('first_name', V(' '), 'last_name', output_field=CharField()))

        employee_names = [f'{employee.last_name}, {employee.first_name} | {employee.employee_id}' for employee in
                          employees]

        employee_field = 'employee_name'
        employee_name = self.cleaned_data[employee_field]

        if employee_name not in employee_names:
            self.add_error(employee_field, f'Employee \"{employee_name}\" not in database')

        try:
            divider_index = employee_name.find('|')
            employee_id = int(employee_name[divider_index + 1:])
            employee = employees.get(employee_id=employee_id)

            # Ensure dates selected are in the future and not already requested

            date_field = 'requested_dates'
            requested_dates_str = self.cleaned_data[date_field]
            requested_dates = [datetime.datetime.strptime(date, '%m/%d/%Y') for date in
                               requested_dates_str.split(',')]
            employee_days_off = [str(day) for day in
                                 DayOff.objects.filter(is_active=True, time_off_request__employee=employee)]
            duplicate_dates = []

            for date in requested_dates:
                if date.strftime('%m-%d-%Y') in employee_days_off and date not in duplicate_dates:
                    duplicate_dates.append(date.strftime('%m-%d-%Y'))

            if duplicate_dates:
                duplicates_str = ','.join(duplicate_dates)
                self.add_error(date_field, f"The following days have already been requested off: {duplicates_str}")

            # Check if employees have floating holidays

            type_field = 'time_off_type'
            time_off_type = self.cleaned_data[type_field]

            if time_off_type == '7' and employee.floating_holiday < 1:
                self.add_error(type_field, f'Employee \"{employee_name}\" has no more floating holidays')

        except ObjectDoesNotExist or ValueError:
            pass

    def save(self, request):
        employee_name = self.cleaned_data['employee_name']
        index = employee_name.find('|')
        employee_id = employee_name[index + 1:]
        employee = Employee.objects.get(employee_id=employee_id)

        time_off_request = TimeOffRequest(
            employee=employee,
            request_date=datetime.datetime.today(),
            time_off_type=self.cleaned_data['time_off_type'],
            status='0',
            reason=self.cleaned_data['reason'],
            comments=self.cleaned_data['comments'],
            status_change_by=request.user.get_full_name()
        )

        time_off_request.save()

        for date in self.cleaned_data['requested_dates'].split(','):
            day_off = DayOff(
                requested_date=datetime.datetime.strptime(date, '%m/%d/%Y'),
                time_off_request=time_off_request,
            )

            day_off.save()


class FilterForm(forms.Form):
    company = forms.CharField(initial='Filter by Company', required=False)
    date_range = fields.DateRangeField(input_formats=['%m/%d/%Y'],
                                       widget=widgets.DateRangeWidget(format='%m/%d/%Y',
                                                                      attrs={'style': 'font-size: 14px'}),
                                       required=False)
    search = forms.CharField(max_length=30, widget=forms.TextInput(
        attrs={'placeholder': 'Search by Name or ID', 'style': 'font-size: 14px'}), required=False)

    sort_by = forms.CharField(required=False)

    def __init__(self, sort_choices, *args, **kwargs):
        super(FilterForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_show_labels = False

        company_choices = [(company.display_name, company.display_name) for company in Company.objects.all()]
        company_choices.insert(0, ('', 'Filter by Company'))

        self.fields['company'].widget = forms.Select(choices=company_choices, attrs={'style': 'font-size: 14px',
                                                                                     'onchange': 'form.submit();'})
        self.fields['sort_by'].widget = forms.Select(choices=sort_choices,
                                                     attrs={'style': 'font-size: 14px', 'onchange': 'form.submit();'})


class AttendanceFilterForm(FilterForm):
    reasons = forms.CharField(required=False)

    def __init__(self, sort_choices, *args, **kwargs):
        super(AttendanceFilterForm, self).__init__(sort_choices, *args, **kwargs)
        reason_choices = Attendance.REASON_CHOICES
        reason_choices[0] = ('', 'Filter by Reason')
        self.fields['reasons'].widget = forms.Select(choices=reason_choices,
                                                     attrs={'style': 'font-size: 14px', 'onchange': 'form.submit();'})


class CounselingFilterForm(FilterForm):
    action_type = forms.CharField(initial='Filter by Action Type', required=False)

    def __init__(self, sort_choices, *args, **kwargs):
        super(CounselingFilterForm, self).__init__(sort_choices, *args, **kwargs)
        action_choices = Counseling.ACTION_CHOICES
        action_choices[0] = ('', 'Filter by Action Type')
        self.fields['action_type'].widget = forms.Select(choices=action_choices,
                                                         attrs={'style': 'font-size: 14px',
                                                                'onchange': 'form.submit();'})


class TimeOffFilterForm(FilterForm):
    status = forms.CharField(initial='Filter by Status', required=False)
    time_off_type = forms.CharField(initial='Filter by Action Type', required=False)

    def __init__(self, sort_choices, *args, **kwargs):
        super(TimeOffFilterForm, self).__init__(sort_choices, *args, **kwargs)
        status_choices = TimeOffRequest.STATUS_CHOICES
        status_choices[0] = ('', 'Filter by Status')
        time_off_choices = TimeOffRequest.TIME_OFF_CHOICES
        time_off_choices[0] = ('', 'Filter by Time off type')
        self.fields['status'].widget = forms.Select(choices=status_choices,
                                                    attrs={'style': 'font-size: 14px',
                                                           'onchange': 'form.submit();'})
        self.fields['time_off_type'].widget = forms.Select(choices=time_off_choices,
                                                           attrs={'style': 'font-size: 14px',
                                                                  'onchange': 'form.submit();'})
