# Generated by Django 2.2.10 on 2020-04-22 19:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('NEMO', '0015_auto_20200323_1329'),
    ]

    operations = [
        migrations.AddField(
            model_name='area',
            name='buddy_end',
            field=models.PositiveIntegerField(default=8, help_text='Time in 24 hour format of end of buddy system, if active and not forced'),
        ),
        migrations.AddField(
            model_name='area',
            name='buddy_start',
            field=models.PositiveIntegerField(default=20, help_text='Time in 24 hour format of start of buddy system, if active and not forced'),
        ),
        migrations.AddField(
            model_name='area',
            name='force_buddy',
            field=models.BooleanField(default=False, help_text='Toggle to force activation of buddy system outside of usual hours (i.e. for a holiday).'),
        ),
        migrations.AddField(
            model_name='area',
            name='require_buddy',
            field=models.BooleanField(default=False, help_text='Indicates that the buddy system is required in this area.'),
        ),
    ]
