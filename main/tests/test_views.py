from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from employees.models import Employee


class TestEmployeeInfoView(TestCase):
    def setUp(self) -> None:
        """Create an authorized Django user for testing purposes"""
        self.user = Employee.objects.create_user(
            username='test.user',
            password='test',
            first_name='Test',
            last_name='User',
            employee_id=000000
        )

    def test_redirect_when_logged_out(self):
        """Test that the user is redirected to the log in page when not logged in"""
        url = reverse('main-employee-info')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

    def test_get_when_logged_in_no_permissions(self):
        """Test that the view returns a HTTP 403 when the user is logged in but does not have can_view_employee_info
         permissions"""
        url = reverse('main-employee-info')
        self.client.force_login(self.user)
        resp = self.client.get(url)
        self.client.logout()

        self.assertEqual(resp.status_code, 403)

    def test_get_when_logged_in_with_permissions(self):
        """Test that the view returns a HTTP 200 when the user is logged in and has can_view_employee_info
         permissions"""
        url = reverse('main-employee-info')
        permission = Permission.objects.get(codename='can_view_employee_info')

        self.user.user_permissions.add(permission)
        self.client.force_login(self.user)
        resp = self.client.get(url)
        self.client.logout()

        self.assertEqual(resp.status_code, 200)


class TestExportPhoneList(TestCase):
    def setUp(self):
        """Create an authorized Django user for testing purposes"""
        self.user = Employee.objects.create_user(
            username='test.user',
            password='test',
            first_name='Test',
            last_name='User',
            employee_id=000000
        )

    def test_redirect_when_logged_out(self):
        """Test that the user is redirected to the log in page when not logged in"""
        url = reverse('main-export-phone-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

    def test_get_when_logged_in_no_permissions(self):
        """Test that the view returns a HTTP 403 when the user is logged in but does not have can_export_phone_list
         permissions"""
        url = reverse('main-export-phone-list')
        self.client.force_login(self.user)
        resp = self.client.get(url)
        self.client.logout()

        self.assertEqual(resp.status_code, 403)

    def test_get_when_logged_in_with_permissions(self):
        """Test that the view returns a HTTP 200 and that content-disposition is correct when the user is logged in and
         has can_export_phone_list permissions"""
        url = reverse('main-export-phone-list')
        permission = Permission.objects.get(codename='can_export_phone_list')

        self.user.user_permissions.add(permission)
        self.client.force_login(self.user)
        resp = self.client.get(url)
        self.client.logout()

        self.assertEqual(resp.get('content-disposition'), 'attachment;filename="Division 12 - Phone List.pdf"')
