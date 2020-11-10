from django.test import TestCase
from django.urls import reverse

from employees.models import Employee


class TestEmployeeInfoView(TestCase):
    def setUp(self) -> None:
        """Create an authorized Django user for testing purposes"""
        self.user = Employee(
            username='test.user',
        )

    def test_redirect_when_logged_out(self):
        """Test that the user is redirected to the log in page when not logged in"""
        url = reverse('main-employee-info')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

    def test_get_when_logged_in(self):
        """Test that the view returns a HTTP 200 when the user is logged in"""
        url = reverse('main-employee-info')
        self.client.force_login(self.user)
        resp = self.client.get(url)
        self.client.logout()

        self.assertEqual(resp.status_code, 200)