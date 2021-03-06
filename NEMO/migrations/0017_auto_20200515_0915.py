# Generated by Django 2.2.10 on 2020-05-15 13:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('NEMO', '0016_buddy_system_area'),
    ]

    operations = [
        migrations.AddField(
            model_name='area',
            name='maximum_capacity',
            field=models.PositiveIntegerField(default=0, help_text='The maximum number of people allowed in this area at any given time. Set to 0 for unlimited.'),
        ),
        migrations.AddField(
            model_name='comment',
            name='staff_only',
            field=models.BooleanField(default=False),
        ),
    ]
