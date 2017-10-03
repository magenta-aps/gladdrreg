# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-10-03 13:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('addrreg', '0007_events_errorcode_length'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='objectID',
            field=models.UUIDField(db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='created',
            field=models.DateTimeField(auto_now=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='receipt_obtained',
            field=models.DateTimeField(db_index=True, null=True),
        ),
    ]
