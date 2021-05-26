# Generated by Django 3.1.11 on 2021-05-26 21:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0042_auto_20210526_2041'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='employee',
            name='email_attendance_doc_day3',
        ),
        migrations.AddField(
            model_name='employee',
            name='email_attendance_doc_day14',
            field=models.BooleanField(default=True, help_text='Receive an email when it has been 14 or more days since an attendance point was given but not signed', verbose_name='3 Days Past Due Attendance'),
        ),
        migrations.AlterField(
            model_name='employee',
            name='email_attendance_doc_day10',
            field=models.BooleanField(default=True, help_text='Receive an email when it has been 10 days since an attendance point was given but not signed', verbose_name='10 Days Past Due Attendance'),
        ),
        migrations.AlterField(
            model_name='employee',
            name='email_attendance_doc_day5',
            field=models.BooleanField(default=True, help_text='Receive an email when it has been 5 days since an attendance point was given but not signed', verbose_name='5 Days Past Due Attendance'),
        ),
        migrations.AlterField(
            model_name='employee',
            name='email_attendance_doc_day7',
            field=models.BooleanField(default=True, help_text='Receive an email when it has been 7 days since an attendance point was given but not signed', verbose_name='7 Days Past Due Attendance'),
        ),
    ]