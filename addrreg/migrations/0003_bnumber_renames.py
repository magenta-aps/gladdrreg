# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-08-14 13:06
from __future__ import unicode_literals

import addrreg.models.base
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [('addrreg', '0003_auto_20170623_1542')]

    dependencies = [
        ('addrreg', '0002_fix_defaults'),
    ]

    operations = [
        migrations.RenameField(
            model_name='bnumber',
            old_name='name',
            new_name='b_type',
        ),
        migrations.RenameField(
            model_name='bnumber',
            old_name='nickname',
            new_name='b_callname',
        ),
        migrations.RenameField(
            model_name='bnumberregistrations',
            old_name='name',
            new_name='b_type',
        ),
        migrations.RenameField(
            model_name='bnumberregistrations',
            old_name='nickname',
            new_name='b_callname',
        ),
        migrations.AlterField(
            model_name='address',
            name='sumiiffik_domain',
            field=addrreg.models.base.SumiiffikDomainField(default='https://data.gl/najugaq/address/v1', max_length=64, validators=[django.core.validators.URLValidator()], verbose_name='Sumiiffik Domain'),
        ),
        migrations.AlterField(
            model_name='addressregistrations',
            name='sumiiffik_domain',
            field=addrreg.models.base.SumiiffikDomainField(default='https://data.gl/najugaq/address/v1', max_length=64, validators=[django.core.validators.URLValidator()], verbose_name='Sumiiffik Domain'),
        ),
        migrations.AlterField(
            model_name='bnumber',
            name='sumiiffik_domain',
            field=addrreg.models.base.SumiiffikDomainField(default='https://data.gl/najugaq/number/v1', max_length=64, validators=[django.core.validators.URLValidator()], verbose_name='Sumiiffik Domain'),
        ),
        migrations.AlterField(
            model_name='bnumberregistrations',
            name='sumiiffik_domain',
            field=addrreg.models.base.SumiiffikDomainField(default='https://data.gl/najugaq/number/v1', max_length=64, validators=[django.core.validators.URLValidator()], verbose_name='Sumiiffik Domain'),
        ),
        migrations.AlterField(
            model_name='district',
            name='sumiiffik_domain',
            field=addrreg.models.base.SumiiffikDomainField(default='https://data.gl/najugaq/district/v1', max_length=64, validators=[django.core.validators.URLValidator()], verbose_name='Sumiiffik Domain'),
        ),
        migrations.AlterField(
            model_name='districtregistrations',
            name='sumiiffik_domain',
            field=addrreg.models.base.SumiiffikDomainField(default='https://data.gl/najugaq/district/v1', max_length=64, validators=[django.core.validators.URLValidator()], verbose_name='Sumiiffik Domain'),
        ),
        migrations.AlterField(
            model_name='locality',
            name='sumiiffik_domain',
            field=addrreg.models.base.SumiiffikDomainField(default='https://data.gl/najugaq/locality/v1', max_length=64, validators=[django.core.validators.URLValidator()], verbose_name='Sumiiffik Domain'),
        ),
        migrations.AlterField(
            model_name='localityregistrations',
            name='sumiiffik_domain',
            field=addrreg.models.base.SumiiffikDomainField(default='https://data.gl/najugaq/locality/v1', max_length=64, validators=[django.core.validators.URLValidator()], verbose_name='Sumiiffik Domain'),
        ),
        migrations.AlterField(
            model_name='municipality',
            name='sumiiffik_domain',
            field=addrreg.models.base.SumiiffikDomainField(default='https://data.gl/najugaq/municipality/v1', max_length=64, validators=[django.core.validators.URLValidator()], verbose_name='Sumiiffik Domain'),
        ),
        migrations.AlterField(
            model_name='municipalityregistrations',
            name='sumiiffik_domain',
            field=addrreg.models.base.SumiiffikDomainField(default='https://data.gl/najugaq/municipality/v1', max_length=64, validators=[django.core.validators.URLValidator()], verbose_name='Sumiiffik Domain'),
        ),
        migrations.AlterField(
            model_name='postalcode',
            name='sumiiffik_domain',
            field=addrreg.models.base.SumiiffikDomainField(default='https://data.gl/najugaq/postalcode/v1', max_length=64, validators=[django.core.validators.URLValidator()], verbose_name='Sumiiffik Domain'),
        ),
        migrations.AlterField(
            model_name='postalcoderegistrations',
            name='sumiiffik_domain',
            field=addrreg.models.base.SumiiffikDomainField(default='https://data.gl/najugaq/postalcode/v1', max_length=64, validators=[django.core.validators.URLValidator()], verbose_name='Sumiiffik Domain'),
        ),
        migrations.AlterField(
            model_name='road',
            name='sumiiffik_domain',
            field=addrreg.models.base.SumiiffikDomainField(default='https://data.gl/najugaq/road/v1', max_length=64, validators=[django.core.validators.URLValidator()], verbose_name='Sumiiffik Domain'),
        ),
        migrations.AlterField(
            model_name='roadregistrations',
            name='sumiiffik_domain',
            field=addrreg.models.base.SumiiffikDomainField(default='https://data.gl/najugaq/road/v1', max_length=64, validators=[django.core.validators.URLValidator()], verbose_name='Sumiiffik Domain'),
        ),
        migrations.AlterField(
            model_name='bnumber',
            name='b_callname',
            field=models.CharField(blank=True, max_length=60, null=True, verbose_name='B-Nickname'),
        ),
        migrations.AlterField(
            model_name='bnumber',
            name='b_type',
            field=models.CharField(blank=True, max_length=60, null=True, verbose_name='B-Type'),
        ),
        migrations.AlterField(
            model_name='bnumberregistrations',
            name='b_callname',
            field=models.CharField(blank=True, max_length=60, null=True, verbose_name='B-Nickname'),
        ),
        migrations.AlterField(
            model_name='bnumberregistrations',
            name='b_type',
            field=models.CharField(blank=True, max_length=60, null=True, verbose_name='B-Type'),
        ),
    ]
