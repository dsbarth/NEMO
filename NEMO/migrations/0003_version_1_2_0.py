# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-08-15 15:23
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('NEMO', '0002_version_1_1_0'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScheduledOutageCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
            ],
            options={
                'verbose_name_plural': 'Scheduled outage categories',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='TaskHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(help_text="A text description of the task's status", max_length=200)),
                ('time', models.DateTimeField(auto_now_add=True, help_text='The date and time when the task status was changed')),
            ],
            options={
                'verbose_name_plural': 'task histories',
                'ordering': ['time'],
                'get_latest_by': 'time',
            },
        ),
        migrations.CreateModel(
            name='TaskStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True)),
                ('notify_primary_tool_owner', models.BooleanField(default=False, help_text='Notify the primary tool owner when a task transitions to this status')),
                ('notify_secondary_tool_owner', models.BooleanField(default=False, help_text='Notify the secondary tool owner when a task transitions to this status')),
                ('notify_tool_notification_email', models.BooleanField(default=False, help_text='Send an email to the tool notification email address when a task transitions to this status')),
                ('custom_notification_email_address', models.EmailField(blank=True, help_text="Notify a custom email address when a task transitions to this status. Leave this blank if you don't need it.", max_length=254)),
                ('notification_message', models.TextField(blank=True)),
            ],
            options={
                'verbose_name_plural': 'task statuses',
                'ordering': ['name'],
            },
        ),
        migrations.AlterModelOptions(
            name='resourcecategory',
            options={'ordering': ['name'], 'verbose_name_plural': 'resource categories'},
        ),
        migrations.RemoveField(
            model_name='task',
            name='first_responder',
        ),
        migrations.RemoveField(
            model_name='task',
            name='first_response_time',
        ),
        migrations.RemoveField(
            model_name='task',
            name='status',
        ),
        migrations.AddField(
            model_name='consumable',
            name='visible',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='scheduledoutage',
            name='category',
            field=models.CharField(blank=True, help_text='A categorical reason for why this outage is scheduled. Useful for trend analytics.', max_length=200),
        ),
        migrations.AddField(
            model_name='scheduledoutage',
            name='resource',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='NEMO.Resource'),
        ),
        migrations.AddField(
            model_name='task',
            name='cancelled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='task',
            name='resolved',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='tool',
            name='post_usage_questions',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='usageevent',
            name='run_data',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='resource',
            name='restriction_message',
            field=models.TextField(blank=True, help_text='The message that is displayed to users on the tool control page when this resource is unavailable.'),
        ),
        migrations.AlterField(
            model_name='scheduledoutage',
            name='details',
            field=models.TextField(blank=True, help_text='A detailed description of why there is a scheduled outage, and what users can expect during the outage'),
        ),
        migrations.AlterField(
            model_name='scheduledoutage',
            name='title',
            field=models.CharField(help_text='A brief description to quickly inform users about the outage', max_length=100),
        ),
        migrations.AlterField(
            model_name='scheduledoutage',
            name='tool',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='NEMO.Tool'),
        ),
        migrations.AddField(
            model_name='taskhistory',
            name='task',
            field=models.ForeignKey(help_text='The task that this historical entry refers to', on_delete=django.db.models.deletion.CASCADE, related_name='history', to='NEMO.Task'),
        ),
        migrations.AddField(
            model_name='taskhistory',
            name='user',
            field=models.ForeignKey(help_text='The user that changed the task to this status', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
