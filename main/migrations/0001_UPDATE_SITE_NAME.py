from django.db import migrations
from django.conf import settings
import os


def update_site_name(apps, schema_editor):
    SiteModel = apps.get_model('sites', 'Site')
    domain = os.environ.get('DOMAIN', 'example.com')

    SiteModel.objects.update_or_create(
        pk=settings.SITE_ID,
        defaults={'domain': domain,
                  'name': domain}
    )


class Migration(migrations.Migration):

    dependencies = [
        # Make sure the dependency that was here by default is also included here
        ('sites', '0002_alter_domain_unique'), # Required to reference `sites` in `apps.get_model()`
    ]

    operations = [
        migrations.RunPython(update_site_name),
    ]