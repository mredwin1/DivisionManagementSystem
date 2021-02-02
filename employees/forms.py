import datetime

from django import forms
from phonenumber_field.formfields import PhoneNumberField
from pytz import timezone

from .models import Company, Attendance, Counseling, Hold, Employee, SafetyPoint, TimeOffRequest, Settlement, DayOff


class EditPhoneNumbers(forms.Form):
    primary_phone = PhoneNumberField(label='Primary Phone', required=True)
    secondary_phone = PhoneNumberField(label='Secondary Phone', required=False)

    def save(self, employee):
        employee.primary_phone = self.cleaned_data['primary_phone']
        employee.secondary_phone = self.cleaned_data['secondary_phone']

        employee.save()


class EditEmployeeInfo(forms.Form):
    COMPANY_CHOICES = []

    try:
        companies = Company.objects.all()

        for company in companies:
            company_name = (company.display_name, company.display_name)
            COMPANY_CHOICES.append(company_name)
    except:
        pass

    first_name = forms.CharField(label='First Name', required=True, max_length=30)
    last_name = forms.CharField(label='Last Name', required=True, max_length=30)

    employee_id = forms.IntegerField(label='Employee ID', required=True)

    primary_phone = PhoneNumberField(label='Primary Phone', required=True)
    secondary_phone = PhoneNumberField(label='Secondary Phone', required=False)

    hire_date = forms.DateField(label='Hire Date', widget=forms.TextInput(attrs={'type': 'date'}), required=True)
    application_date = forms.DateField(label='Application Date', widget=forms.TextInput(attrs={'type': 'date'}), required=True)
    classroom_date = forms.DateField(label='Classroom Date', widget=forms.TextInput(attrs={'type': 'date'}), required=True)

    company = forms.CharField(label='Company', widget=forms.Select(choices=COMPANY_CHOICES), required=True)

    is_part_time = forms.BooleanField(label='Part Time', required=False)
    is_neighbor_link = forms.BooleanField(label='Neighbor Link', required=False)

    def save(self, employee):
        company = Company.objects.get(display_name=self.cleaned_data['company'])

        employee.first_name = self.cleaned_data['first_name']
        employee.last_name = self.cleaned_data['last_name']
        employee.employee_id = self.cleaned_data['employee_id']
        employee.primary_phone = self.cleaned_data['primary_phone']
        employee.secondary_phone = self.cleaned_data['secondary_phone']
        employee.hire_date = self.cleaned_data['hire_date']
        employee.application_date = self.cleaned_data['application_date']
        employee.classroom_date = self.cleaned_data['classroom_date']
        employee.company = company
        employee.is_part_time = self.cleaned_data['is_part_time']
        employee.is_neighbor_link = self.cleaned_data['is_neighbor_link']

        employee.save()


class AssignAttendance(forms.Form):
    incident_date = forms.DateField(label='Incident Date', widget=forms.TextInput(attrs={'type': 'date'}),
                                    required=True)
    reason = forms.CharField(label='Reason', widget=forms.Select(choices=Attendance.REASON_CHOICES), required=True)
    exemption = forms.CharField(label='Exemption', widget=forms.Select(choices=Attendance.EXEMPTION_CHOICES), required=False)

    def __init__(self, *args, **kwargs):
        self.employee = kwargs.pop('employee', None)
        super(AssignAttendance, self).__init__(*args, **kwargs)

    def clean(self):
        super().clean()

        exception_field_name = 'exemption'
        exemption = self.cleaned_data[exception_field_name]

        if exemption == '1' and self.employee.paid_sick <= 0:
            self.add_error(exception_field_name, f'{self.employee.get_full_name()} does not have Paid Sick days '
                                                 f'available')
        elif exemption == '2' and self.employee.unpaid_sick <= 0:
            self.add_error(exception_field_name, f'{self.employee.get_full_name()} does not have Unpaid Sick days '
                                                 f'available')

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

        if self.cleaned_data['exemption']:
            point = 0
            if self.cleaned_data['exemption'] == '1':
                self.employee.paid_sick -= 1
            elif self.cleaned_data['exemption'] == '2':
                self.employee.unpaid_sick -= 1
        else:
            point = points[self.cleaned_data['reason']]

        attendance = Attendance(
            employee=self.employee,
            incident_date=self.cleaned_data['incident_date'],
            issued_date=datetime.date.today(),
            points=point,
            reason=self.cleaned_data['reason'],
            assigned_by=f'{request.user.first_name} {request.user.last_name}',
            exemption=self.cleaned_data['exemption'],
        )

        attendance.save()

        self.employee.save()


class EditAttendance(forms.Form):
    incident_date = forms.DateField(label='Incident Date', widget=forms.TextInput(attrs={'type': 'date'}),
                                    required=True)
    reason = forms.CharField(label='Reason', widget=forms.Select(choices=Attendance.REASON_CHOICES), required=True)
    exemption = forms.CharField(label='Exemption', widget=forms.Select(choices=Attendance.EXEMPTION_CHOICES), required=False)
    issued_date = forms.DateField(label='Issued Date', widget=forms.TextInput(attrs={'type': 'date'}),
                                  required=False)
    document = forms.FileField(label='Document', required=False)

    def clean(self):
        super().clean()

        exception_field_name = 'exemption'
        exemption = self.cleaned_data[exception_field_name]

        if exemption == '1' and self.employee.paid_sick <= 0:
            self.add_error(exception_field_name, f'{self.employee.get_full_name()} does not have Paid Sick days '
                                                 f'available')
        elif exemption == '2' and self.employee.unpaid_sick <= 0:
            self.add_error(exception_field_name, f'{self.employee.get_full_name()} does not have Unpaid Sick days '
                                                 f'available')

    def save(self, employee, attendance, request):
        update_fields = ['incident_date', 'issued_date', 'reason', 'exemption', 'edited_date', 'edited_by', 'points']
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

        if self.cleaned_data['exemption']:
            attendance.points = 0
            if self.cleaned_data['exemption'] == '1' and attendance.exemption != '1':
                employee.paid_sick -= 1
            elif self.cleaned_data['exemption'] == '2' and attendance.exemption != '2':
                employee.unpaid_sick -= 1
        else:
            attendance.points = points[self.cleaned_data['reason']]

        if attendance.exemption == '1' and self.cleaned_data['exemption'] != '1':
            employee.paid_sick += 1
        elif attendance.exemption == '2' and self.cleaned_data['exemption'] != '2':
            employee.unpaid_sick += 1

        attendance.incident_date = self.cleaned_data['incident_date']
        attendance.issued_date = self.cleaned_data['issued_date']
        attendance.reason = self.cleaned_data['reason']
        attendance.exemption = self.cleaned_data['exemption']
        attendance.edited_date = datetime.datetime.today()
        attendance.edited_by = f'{request.user.first_name} {request.user.last_name}'

        try:
            attendance.document = request.FILES['document']
            attendance.uploaded = True
            update_fields.append('document')
        except KeyError:
            pass

        employee.save()
        attendance.save(update_fields=update_fields)

        try:
            attendance.counseling.delete()
        except Counseling.DoesNotExist:
            pass


class AssignCounseling(forms.Form):
    issued_date = forms.DateField(label='Issued Date', widget=forms.TextInput(attrs={'type': 'date'}), required=True)
    action_type = forms.CharField(label='Action Type', widget=forms.Select(choices=Counseling.ACTION_CHOICES),
                                  required=True)
    hearing_date = forms.DateTimeField(label='Hearing Date', widget=forms.TextInput(attrs={'type': 'date'}),
                                       required=False)
    hearing_time = forms.TimeField(label='Hearing Time', widget=forms.TextInput(attrs={'type': 'time'}),
                                   initial=datetime.time(hour=10, minute=0), required=False)
    conduct = forms.CharField(label='Explanation of Employee Conduct', widget=forms.Textarea(), required=True)
    conversation = forms.CharField(label='Record of Conversation', widget=forms.Textarea(), required=True)
    pd_check_override = forms.BooleanField(label='Override Progressive Discipline Check', required=False)

    def __init__(self, *args, **kwargs):
        self.employee = kwargs.pop('employee', None)
        super(AssignCounseling, self).__init__(*args, **kwargs)

    def save(self, request):
        if self.cleaned_data['hearing_date']:
            hearing_date = datetime.datetime.combine(self.cleaned_data['hearing_date'],
                                                     self.cleaned_data['hearing_time'])
        else:
            hearing_date = None

        counseling = Counseling(
            employee=self.employee,
            assigned_by=f'{request.user.first_name} {request.user.last_name}',
            issued_date=datetime.datetime.today(),
            action_type=self.cleaned_data['action_type'],
            hearing_datetime=hearing_date,
            conduct=self.cleaned_data['conduct'],
            conversation=self.cleaned_data['conversation']
        )

        counseling.save()

    def clean(self):
        super().clean()
        counseling_records = Counseling.objects.filter(is_active=True, employee=self.employee).order_by('action_type')
        action_type_field = 'action_type'
        action_type = self.cleaned_data[action_type_field]

        if not self.cleaned_data['pd_check_override']:
            if action_type != '6' and action_type != '5':
                history = {
                    '0': False,
                    '1': False,
                    '2': False,
                    '3': False,
                    '4': False,
                }

                actions = {
                    '': '',
                    '0': 'Verbal Counseling',
                    '1': 'Verbal Warning',
                    '2': 'First Written Warning Notice',
                    '3': 'Final Written Warning Notice & 3 Day Suspension',
                    '4': 'Last % Final Warning',
                    '5': 'Discharge for \"Just Cause\"',
                    '6': 'Administrative Removal from Service',
                }

                for counseling_record in counseling_records:
                    if not counseling_record.attendance and counseling_record.action_type != '5' and counseling_record.action_type != '6':
                        history[counseling_record.action_type] = True

                history_total = sum(history.values())

                if history_total:
                    current = 0
                    del_counseling_count = 0
                    for key, value in history.items():
                        if history[key]:
                            current = int(key)
                    if current:
                        for x in range(current, -1, -1):
                            if not history[str(x)]:
                                del_counseling_count += 1
                        if del_counseling_count:
                            next_step = str(current - del_counseling_count + 1)
                        else:
                            next_step = str(current + 1)
                    else:
                        next_step = str(current + 1)
                else:
                    next_step = '0'

                if int(next_step) > 4:
                    next_step = '6'

                if action_type != next_step:
                    self.add_error(action_type_field, f'The next step in progressive discipline would be {actions[next_step]}.')


class EditCounseling(forms.Form):
    issued_date = forms.DateField(label='Issued Date', widget=forms.TextInput(attrs={'type': 'date'}), required=True)
    action_type = forms.CharField(label='Action Type', widget=forms.Select(choices=Counseling.ACTION_CHOICES), required=True)
    hearing_date = forms.DateTimeField(label='Hearing Date', widget=forms.TextInput(attrs={'type': 'date'}),
                                       required=False)
    hearing_time = forms.TimeField(label='Hearing Time', widget=forms.TextInput(attrs={'type': 'time'}),
                                   initial=datetime.time(hour=10, minute=0), required=False)
    conduct = forms.CharField(label='Explanation of Employee Conduct', widget=forms.Textarea(), required=True)
    conversation = forms.CharField(label='Record of Conversation', widget=forms.Textarea(), required=True)

    document = forms.FileField(label='Document', required=False)

    def save(self, counseling, request):
        update_fields = ['issued_date', 'action_type', 'conduct', 'hearing_datetime', 'conversation']
        try:
            counseling.document = request.FILES['document']
            counseling.uploaded = True
            update_fields.append('document')
        except KeyError:
            pass

        if self.cleaned_data['hearing_date']:
            hearing_datetime = datetime.datetime.combine(self.cleaned_data['hearing_date'], self.cleaned_data['hearing_time'], timezone('UTC'))
        else:
            hearing_datetime = None

        counseling.issued_date = self.cleaned_data['issued_date']
        counseling.action_type = self.cleaned_data['action_type']
        counseling.hearing_datetime = hearing_datetime
        counseling.conduct = self.cleaned_data['conduct']
        counseling.conversation = self.cleaned_data['conversation']

        counseling.save(update_fields=update_fields)


class AssignSafetyPoint(forms.Form):
    incident_date = forms.DateField(label='Incident Date', widget=forms.TextInput(attrs={'type': 'date'}), required=True)
    issued_date = forms.DateField(label='Issued Date', widget=forms.TextInput(attrs={'type': 'date'}), required=True)
    reason = forms.CharField(label='Reason', required=True, widget=forms.Select(
        choices=SafetyPoint.REASON_CHOICES,attrs={'onchange': 'unsafe_act_change()'}))
    unsafe_act = forms.CharField(label='Type of Unsafe Act', widget=forms.TextInput(attrs={'class':'textinput textInput form-control', 'required':''}),required=False, help_text='Write the type of unsafe act')
    details = forms.CharField(label='Details', widget=forms.Textarea(attrs={'class': 'textarea form-control', 'required':''}), required=False)

    def save(self, employee, request):
        points = {
            '0': 1,
            '1': 1,
            '2': 1,
            '3': 2,
            '4': 2,
            '5': 2,
            '6': 2,
            '7': 3,
            '8': 4,
            '9': 6,
            '10': 6,
            '11': 6,
            '12': 6,
            '13': 6,
            '14': 6,
        }

        safety_point = SafetyPoint(
            employee=employee,
            incident_date=self.cleaned_data['incident_date'],
            issued_date=self.cleaned_data['issued_date'],
            points=points[self.cleaned_data['reason']],
            reason=self.cleaned_data['reason'],
            unsafe_act=self.cleaned_data['unsafe_act'],
            details=self.cleaned_data['details'],
            assigned_by=request.user.get_full_name(),
        )

        safety_point.save()


class EditSafetyPoint(forms.Form):
    incident_date = forms.DateField(label='Incident Date', widget=forms.TextInput(attrs={'type': 'date'}), required=True)
    issued_date = forms.DateField(label='Issued Date', widget=forms.TextInput(attrs={'type': 'date'}), required=True)
    reason = forms.CharField(label='Reason', required=True, widget=forms.Select(
        choices=SafetyPoint.REASON_CHOICES,attrs={'onchange': 'unsafe_act_change()'}))
    unsafe_act = forms.CharField(label='Type of Unsafe Act', widget=forms.TextInput(attrs={'class':'textinput textInput form-control', 'required':''}),required=False, help_text='Write the type of unsafe act')
    details = forms.CharField(label='Details', widget=forms.Textarea(attrs={'class': 'textarea form-control', 'required':''}), required=False)
    document = forms.FileField(label='Document', required=False)

    def save(self, safety_point, request):
        points = {
            '0': 1,
            '1': 1,
            '2': 1,
            '3': 2,
            '4': 2,
            '5': 2,
            '6': 2,
            '7': 3,
            '8': 4,
            '9': 6,
            '10': 6,
            '11': 6,
            '12': 6,
            '13': 6,
            '14': 6,
        }

        update_fields = ['incident_date', 'issued_date', 'points', 'reason', 'unsafe_act', 'details']
        try:
            safety_point.document = self.files['document']
            safety_point.uploaded = True
            update_fields.append('document')
        except KeyError:
            pass
        safety_point.incident_date = self.cleaned_data['incident_date']
        safety_point.issued_date = self.cleaned_data['issued_date']
        safety_point.points = points[self.cleaned_data['reason']]
        safety_point.reason = self.cleaned_data['reason']
        safety_point.unsafe_act = self.cleaned_data['unsafe_act']
        safety_point.details = self.cleaned_data['details']

        safety_point.save(update_fields=update_fields)


class PlaceHold(forms.Form):
    incident_date = forms.DateField(label='Incident Date', help_text='If incident, date of the incident',
                                    widget=forms.TextInput(attrs={'type': 'date'}), required=False)
    training_date = forms.DateField(label='Training Date', help_text='If training, date of the training',
                                    widget=forms.TextInput(attrs={'type': 'date'}), required=False)
    training_time = forms.TimeField(label='Training Time', help_text='If training, time of the training',
                                    widget=forms.TextInput(attrs={'type': 'time'}), required=False)
    release_date = forms.DateField(label='Release Date', help_text='If date of release known put it above',
                                   widget=forms.TextInput(attrs={'type': 'date'}), required=False)
    reason = forms.CharField(label='Reason', help_text='Type the reason for being placed on hold')

    def save(self, employee, request):
        if self.cleaned_data['training_date']:
            training_datetime = datetime.datetime.combine(self.cleaned_data['training_date'], self.cleaned_data['training_time'])
        else:
            training_datetime = None

        assigned_by = f'{request.user.first_name} {request.user.last_name}'

        hold = Hold(
            employee=employee,
            incident_date=self.cleaned_data['incident_date'],
            training_datetime=training_datetime,
            release_date=self.cleaned_data['release_date'],
            reason=self.cleaned_data['reason'],
            assigned_by=assigned_by,
            hold_date=datetime.datetime.today()
        )

        hold.save()


class TimeOffRequestForm(forms.Form):
    requested_dates = forms.CharField(label='Dates Requested Off', widget=forms.TextInput())
    time_off_type = forms.CharField(label='Type of Time Off',
                                    widget=forms.Select(choices=TimeOffRequest.TIME_OFF_CHOICES), required=True)
    reason = forms.CharField(label='Reason for Time Off', widget=forms.Textarea(), required=False)
    comments = forms.CharField(label='Comments/Special Instructions', widget=forms.Textarea(), required=False)

    def __init__(self, *args, **kwargs):
        self.employee = kwargs.pop('employee', None)
        super(TimeOffRequestForm, self).__init__(*args, **kwargs)

    def save(self, employee):
        time_off_request = TimeOffRequest(
            employee=employee,
            request_date=datetime.datetime.today(),
            time_off_type=self.cleaned_data['time_off_type'],
            status='0',
            reason=self.cleaned_data['reason'],
            comments=self.cleaned_data['comments']
        )

        time_off_request.save()

        for date in self.cleaned_data['requested_dates'].split(','):
            day_off = DayOff(
                requested_date=datetime.datetime.strptime(date, '%m/%d/%Y'),
                time_off_request=time_off_request,
            )

            day_off.save()

    def clean(self):
        super().clean()

        # Ensure dates selected are in the future and not already requested

        date_field = 'requested_dates'
        requested_dates_str = self.cleaned_data[date_field]
        requested_dates = [datetime.datetime.strptime(date, '%m/%d/%Y') for date in requested_dates_str.split(',')]
        employee_days_off = [str(day) for day in DayOff.objects.filter(is_active=True, time_off_request__employee=self.employee)]
        today = datetime.datetime.today()
        duplicate_dates = []

        for date in requested_dates:
            if date < today:
                self.add_error(date_field, f'The dates selected must be in the future')
                break
            if date.strftime('%m-%d-%Y') in employee_days_off and date not in duplicate_dates:
                duplicate_dates.append(date.strftime('%m-%d-%Y'))

        if duplicate_dates:
            duplicates_str = ','.join(duplicate_dates)
            self.add_error(date_field, f"The following days have already been requested off: {duplicates_str}")

        # Check if employees have floating holidays

        type_field = 'time_off_type'
        time_off_type = self.cleaned_data[type_field]

        if time_off_type == '7' and self.employee.floating_holiday < 1:
            self.add_error(type_field, f'No more floating holidays')

        # Checking how many days off have been requested and if it exceeds the allotted maximums

        days_totals = {}
        requested_dates.sort()
        days_off = DayOff.objects.filter(is_active=True, requested_date__gte=requested_dates[0],
                                         requested_date__lte=requested_dates[-1],
                                         time_off_request__employee__is_neighbor_link=self.employee.is_neighbor_link)

        # Days of the week where 0 is Sunday and 6 is Saturday
        maximums = {
            '0': 4,
            '1': 10,
            '2': 10,
            '3': 10,
            '4': 10,
            '5': 10,
            '6': 4,
        }

        for day in days_off:
            if str(day) in days_totals.keys():
                days_totals[str(day)] += 1
            else:
                days_totals[str(day)] = 1

        if self.employee.is_neighbor_link:
            error_str = []
            for date in requested_dates:
                try:
                    if days_totals[date.strftime('%m-%d-%Y')] >= 2:
                        error_str.append(date.strftime('%m-%d-%Y'))
                except KeyError:
                    pass
            if error_str:
                self.add_error(date_field, f"The following dates have reached their request limit: {', '.join(error_str)}."
                                           f" Please see a Manager with any questions")
        else:
            error_str = []
            for date in requested_dates:
                try:
                    if days_totals[date.strftime('%m-%d-%Y')] >= maximums[str(date.weekday())]:
                        error_str.append(date.strftime('%m-%d-%Y'))
                except KeyError:
                    pass
            if error_str:
                self.add_error(date_field,
                               f"The following dates have reached their request limit: {', '.join(error_str)}."
                               f" Please see a Manager with any questions")


class TerminateEmployee(forms.Form):
    termination_type = forms.CharField(max_length=50, label='Termination Type',
                                       widget=forms.Select(choices=Employee.TERMINATION_CHOICES), required=True)
    termination_comments = forms.CharField(label='Comments', widget=forms.Textarea())

    def save(self, employee):
        employee.termination_type = self.cleaned_data['termination_type']
        employee.termination_comments = self.cleaned_data['termination_comments']
        employee.termination_date = datetime.date.today()
        employee.is_active = False

        employee.save()


class NotificationSettings(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['email_7attendance', 'email_10attendance', 'email_written', 'email_last_final', 'email_removal',
                  'email_safety_point', 'email_termination', 'email_add_hold', 'email_rem_hold', 'email_add_settlement',
                  'email_new_time_off', 'email_new_employee', 'email_attendance_doc_day3', 'email_attendance_doc_day5',
                  'email_attendance_doc_day7', 'email_attendance_doc_day10', 'email_safety_doc_day3',
                  'email_safety_doc_day5', 'email_safety_doc_day7', 'email_safety_doc_day10',
                  'email_counseling_doc_day3', 'email_counseling_doc_day5', 'email_counseling_doc_day7',
                  'email_counseling_doc_day10', 'email_settlement_doc']


class UploadProfilePicture(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['profile_picture']


class AssignSettlement(forms.Form):
    details = forms.CharField(label='Settlement Details', widget=forms.Textarea(), required=True)

    def save(self, request, employee):
        settlement = Settlement(
            employee=employee,
            details=self.cleaned_data['details'],
            created_date=datetime.date.today(),
            assigned_by=request.user.get_full_name(),
        )

        if employee.hold:
            employee.hold.delete()

        settlement.save()


class ViewSettlement(forms.ModelForm):
    class Meta:
        model = Settlement
        fields = ['details', 'document']
        widgets = {
            'created_date': forms.TextInput(attrs={'type': 'date'})
        }
