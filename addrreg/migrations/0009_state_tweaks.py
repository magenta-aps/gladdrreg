# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2017-10-12 12:52
from __future__ import unicode_literals

import addrreg.models.base
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('addrreg', '0008_events_add_objectid'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='bnumber',
            options={'default_permissions': (), 'ordering': ('code', 'b_type'), 'verbose_name': 'B-Number', 'verbose_name_plural': 'B-Numbers'},
        ),
        migrations.AlterModelOptions(
            name='bnumberregistrations',
            options={'default_permissions': (), 'ordering': ('code', 'b_type'), 'verbose_name': 'Registrering for B-nummer', 'verbose_name_plural': 'Registreringer for B-nummer'},
        ),
        migrations.AlterModelOptions(
            name='state',
            options={'default_permissions': (), 'ordering': ('code',), 'verbose_name': 'Condition', 'verbose_name_plural': 'Conditions'},
        ),
        migrations.AlterModelOptions(
            name='stateregistrations',
            options={'default_permissions': (), 'ordering': ('code',), 'verbose_name': 'Registrering for Status', 'verbose_name_plural': 'Registreringer for Status'},
        ),
        migrations.AlterField(
            model_name='address',
            name='state',
            field=models.ForeignKey(default=addrreg.models.base._default_state, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='addrreg.State', verbose_name='Condition'),
        ),
        migrations.AlterField(
            model_name='addressregistrations',
            name='state',
            field=models.ForeignKey(default=addrreg.models.base._default_state, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='addrreg.State', verbose_name='Condition'),
        ),
        migrations.AlterField(
            model_name='bnumber',
            name='state',
            field=models.ForeignKey(default=addrreg.models.base._default_state, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='addrreg.State', verbose_name='Condition'),
        ),
        migrations.AlterField(
            model_name='bnumberregistrations',
            name='state',
            field=models.ForeignKey(default=addrreg.models.base._default_state, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='addrreg.State', verbose_name='Condition'),
        ),
        migrations.AlterField(
            model_name='district',
            name='state',
            field=models.ForeignKey(default=addrreg.models.base._default_state, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='addrreg.State', verbose_name='Condition'),
        ),
        migrations.AlterField(
            model_name='districtregistrations',
            name='state',
            field=models.ForeignKey(default=addrreg.models.base._default_state, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='addrreg.State', verbose_name='Condition'),
        ),
        migrations.AlterField(
            model_name='locality',
            name='state',
            field=models.ForeignKey(default=addrreg.models.base._default_state, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='addrreg.State', verbose_name='Condition'),
        ),
        migrations.AlterField(
            model_name='localityregistrations',
            name='state',
            field=models.ForeignKey(default=addrreg.models.base._default_state, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='addrreg.State', verbose_name='Condition'),
        ),
        migrations.AlterField(
            model_name='municipality',
            name='state',
            field=models.ForeignKey(default=addrreg.models.base._default_state, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='addrreg.State', verbose_name='Condition'),
        ),
        migrations.AlterField(
            model_name='municipalityregistrations',
            name='state',
            field=models.ForeignKey(default=addrreg.models.base._default_state, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='addrreg.State', verbose_name='Condition'),
        ),
        migrations.AlterField(
            model_name='postalcode',
            name='state',
            field=models.ForeignKey(default=addrreg.models.base._default_state, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='addrreg.State', verbose_name='Condition'),
        ),
        migrations.AlterField(
            model_name='postalcoderegistrations',
            name='state',
            field=models.ForeignKey(default=addrreg.models.base._default_state, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='addrreg.State', verbose_name='Condition'),
        ),
        migrations.AlterField(
            model_name='road',
            name='state',
            field=models.ForeignKey(default=addrreg.models.base._default_state, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='addrreg.State', verbose_name='Condition'),
        ),
        migrations.AlterField(
            model_name='roadregistrations',
            name='state',
            field=models.ForeignKey(default=addrreg.models.base._default_state, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='addrreg.State', verbose_name='Condition'),
        ),
        migrations.AlterField(
            model_name='state',
            name='state',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='addrreg.State', verbose_name='Condition'),
        ),
        migrations.AlterField(
            model_name='stateregistrations',
            name='state',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='addrreg.State', verbose_name='Condition'),
        ),
    ]
