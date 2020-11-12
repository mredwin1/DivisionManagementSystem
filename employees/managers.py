from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import ugettext_lazy as _


class EmployeeManager(BaseUserManager):
    def create_user(self, username, password, **extra_fields):
        """Create and save a User with the given username and password.
        """
        if not username:
            raise ValueError(_('The Username must be set'))
        employee = self.model(username=username, **extra_fields)
        employee.set_password(password)
        employee.save()
        return employee

    def create_superuser(self, username, password, **extra_fields):
        """Create and save a SuperUser with the given username and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(username, password, **extra_fields)
