# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-11-21 20:45
from __future__ import unicode_literals

import NEMO.utilities
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('NEMO', '0012_auto_20190218_1739'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaskImages',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to=NEMO.utilities.get_task_image_filename, verbose_name='Image')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name_plural': 'Task images',
                'ordering': ['-uploaded_at'],
            },
        ),
        migrations.CreateModel(
            name='UserPreferences',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attach_created_reservation', models.BooleanField(default=False, help_text='Whether or not to send a calendar invitation when creating a new reservation', verbose_name='created_reservation_invite')),
                ('attach_cancelled_reservation', models.BooleanField(default=False, help_text='Whether or not to send a calendar invitation when cancelling a reservation', verbose_name='cancelled_reservation_invite')),
            ],
            options={
                'verbose_name': 'User preferences',
                'verbose_name_plural': 'User preferences',
            },
        ),
        migrations.AddField(
            model_name='tool',
            name='policy_off_between_times',
            field=models.BooleanField(default=False, help_text='Check this box to disable policy rules every day between the given times'),
        ),
        migrations.AddField(
            model_name='tool',
            name='policy_off_end_time',
            field=models.TimeField(blank=True, help_text='The end time when policy rules should NOT be enforced', null=True),
        ),
        migrations.AddField(
            model_name='tool',
            name='policy_off_start_time',
            field=models.TimeField(blank=True, help_text='The start time when policy rules should NOT be enforced', null=True),
        ),
        migrations.AddField(
            model_name='tool',
            name='policy_off_weekend',
            field=models.BooleanField(default=False, help_text='Whether or not policy rules should be enforced on weekends'),
        ),
        migrations.AlterField(
            model_name='alert',
            name='creator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='chemicalrequest',
            name='approver',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='chemical_approver', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='chemicalrequest',
            name='requester',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='chemical_requester', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='comment',
            name='hidden_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='hidden_comments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='door',
            name='area',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='doors', to='NEMO.Area'),
        ),
        migrations.AlterField(
            model_name='reservation',
            name='cancelled_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='resource',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='NEMO.ResourceCategory'),
        ),
        migrations.AlterField(
            model_name='safetyissue',
            name='reporter',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reported_safety_issues', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='safetyissue',
            name='resolver',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='resolved_safety_issues', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='task',
            name='last_updated_by',
            field=models.ForeignKey(blank=True, help_text='The last user who modified this task. This should always be a staff member.', null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='task',
            name='problem_category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='problem_category', to='NEMO.TaskCategory'),
        ),
        migrations.AlterField(
            model_name='task',
            name='resolution_category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='resolution_category', to='NEMO.TaskCategory'),
        ),
        migrations.AlterField(
            model_name='task',
            name='resolver',
            field=models.ForeignKey(blank=True, help_text='The staff member who resolved the task.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='task_resolver', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='tool',
            name='grant_physical_access_level_upon_qualification',
            field=models.ForeignKey(blank=True, help_text='The designated physical access level is granted to the user upon qualification for this tool.', null=True, on_delete=django.db.models.deletion.PROTECT, to='NEMO.PhysicalAccessLevel'),
        ),
        migrations.AlterField(
            model_name='tool',
            name='primary_owner',
            field=models.ForeignKey(help_text='The staff member who is responsible for administration of this tool.', on_delete=django.db.models.deletion.PROTECT, related_name='primary_tool_owner', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='tool',
            name='requires_area_access',
            field=models.ForeignKey(blank=True, help_text='Indicates that this tool is physically located in a billable area and requires an active area access record in order to be operated.', null=True, on_delete=django.db.models.deletion.PROTECT, to='NEMO.Area'),
        ),
        migrations.AlterField(
            model_name='userchemical',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='userchemical',
            name='request',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='NEMO.ChemicalRequest'),
        ),
        migrations.AddField(
            model_name='taskimages',
            name='task',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='NEMO.Task'),
        ),
        migrations.AddField(
            model_name='user',
            name='preferences',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='NEMO.UserPreferences'),
        ),
    ]
