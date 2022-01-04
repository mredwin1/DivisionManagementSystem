import datetime

from django import template
from django.contrib.auth import settings
from django.contrib.sites.models import Site
from employees.models import DayOff, SafetyPoint
from pytz import utc

register = template.Library()


@register.filter
def pretty_phone(value):
    if value:
        value = f'{value.as_e164[:-10]}({value.as_e164[-10:-7]}) {value.as_e164[-7:-4]}-{value.as_e164[-4:]}'
    else:
        value = 'None'

    return value


@register.filter()
def pretty_position(value):
    value = value.replace('_', ' ')

    return value.upper()


@register.filter()
def pretty_date(value):
    if value:
        value = value.strftime('%m-%d-%Y')

    return value


# Inputs a query set with a field named points and adds them all up
@register.filter()
def total_points(query_set):
    total = 0

    for item in query_set:
        total += item.points

    return total


# Inputs a value that corresponds to an attendance reason
@register.filter()
def attendance_reason_return(value):
    reasons = {
        '0': 'Unexcused',
        '1': 'Consecutive',
        '2': '< 1 HR',
        '3': 'NCNS',
        '4': 'FTC',
        '5': 'Missing Safety Meeting',
        '6': '< 15 MIN',
        '7': '> 15 MIN',
        '8': 'Late Lunch',
    }

    value = reasons[value]

    return value


# Inputs a value that corresponds to an safety point reason
@register.filter()
def safety_point_reason_return(value):
    reasons = {}

    for key, value in SafetyPoint.REASON_CHOICES:
        reasons[key] = value

    value = reasons[value]

    return value


# Inputs a value that corresponds to a reason
@register.filter()
def points_return(value):

    value = int(value) if float(value).is_integer() else value

    return value


# Inputs a value that corresponds to a exemption
@register.filter()
def exemption_return(value):
    exemptions = {
        '': 'None',
        '0': 'FMLA',
        '1': 'Paid Sick',
        '2': 'Unpaid Sick',
        '3': 'Union Agreement',
        '4': 'Excused Absence',
        '5': 'Attendance Incentive',
    }

    if value:
        value = exemptions[value]
    else:
        value = 'None'

    return value


@register.filter()
def action_type_return(value):
    actions = {
        '': '',
        '0': 'Verbal Counseling',
        '1': 'Verbal Warning',
        '2': 'First Written Warning Notice',
        '3': 'Final Written Warning Notice & 3 Day Suspension',
        '4': 'Last & Final Warning',
        '5': 'Discharge for \"Just Cause\"',
        '6': 'Administrative Removal from Service',
    }

    if value:
        value = actions[value]
    else:
        value = 'None'

    return value


@register.filter()
def pretty_datetime(value):
    if value:
        value = value.strftime('%m-%d-%Y @ %I:%M %p')
    else:
        value = 'None'

    return value


@register.filter()
def full_name(value):
    if value:
        value = f'{value.last_name}, {value.first_name}'

    return value


@register.simple_tag(takes_context=True)
def param_replace(context, **kwargs):
    """
    Return encoded URL parameters that are the same as the current
    request's parameters, only with the specified GET parameters added or changed.

    It also removes any empty parameters to keep things neat,
    so you can remove a parm by setting it to ``""``.

    For example, if you're on the page ``/things/?with_frosting=true&page=5``,
    then

    <a href="/things/?{% param_replace page=3 %}">Page 3</a>

    would expand to

    <a href="/things/?with_frosting=true&page=3">Page 3</a>

    Based on
    https://stackoverflow.com/questions/22734695/next-and-before-links-for-a-django-paginated-query/22735278#22735278
    """

    d = context['request'].GET.copy()
    for k, v in kwargs.items():
        d[k] = v
    for k in [k for k, v in d.items() if not v]:
        del d[k]
    return d.urlencode()


@register.filter()
def to_list(value):
    """
    Takes a List that has been turned into a string and returns a list (', ' is the delimiter) and removes '[]'

    :param value: string
    :return: list
    """

    if value:
        value = value.replace('[', '')
        value = value.replace(']', '')

        new_value = value.split(', ')
    else:
        new_value = None

    return new_value


@register.filter()
def status_return(value):
    """
    Takes a status code and returns readable status

    :param value: str
    :return: str of status
    """

    status = {
        '0': 'Pending',
        '1': 'Approved',
        '2': 'Denied'
    }

    return status[value]


@register.filter()
def time_off_return(value):
    """
    Takes a time off code and returns readable time off reason

    :param value: str
    :return: str of reason
    """

    time_off = {
        '0': 'Day(s) Off (Unpaid)',
        '1': 'Vacation (Paid)',
        '2': 'Leave of Absence',
        '3': 'Jury Duty / Subpoena',
        '4': 'Military Leave',
        '5': 'Extended Medical Leave',
        '6': 'Family Medical Leave',
        '7': 'Floating Holiday',
        '8': 'Personal',
        '9': 'Doctor Appointment',
        '10': 'Other',
    }

    return time_off[value]


@register.filter
def requested_dates_return(value):
    """Takes a TimeOff Object and returns a list of strings with all the dates requested off"""
    if value:
        dates = [pretty_date(day_off.requested_date) for day_off in DayOff.objects.filter(time_off_request=value)]
    else:
        dates = []

    return dates


@register.filter
def pretty_requested_dates(value):

    return ' | '.join(requested_dates_return(value))


@register.filter
def termination_type_return(value):
    if value == '0':
        return 'Voluntary'
    elif value == '1':
        return 'Involuntary'
    else:
        return None


@register.filter
def assignee_return(value):
    return value.get_assignee().get_full_name()


@register.filter
def override_by_return(value):
    return value.get_override_by().get_full_name() if value.get_override_by() else None


@register.filter
def release_date_color_return(value):
    if value:
        elapsed_days = (value - datetime.datetime.today().astimezone(utc)).days
        if elapsed_days == 0:
            necessary_class = 'text-warning'
        elif elapsed_days < 0:
            necessary_class = 'text-danger'
        else:
            necessary_class = ''

        return necessary_class


@register.filter
def document_full_url_return(value):
    """Returns a models full document url including domain and protocol"""
    if settings.USE_S3:
        return value.document.url
    else:
        domain = Site.objects.get_current().domain
        return f'https://{domain}{value.document.url}'
