# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-10-16 16:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('species', '0006_auto_20181016_1614'),
    ]

    operations = [
        migrations.RenameField(
            model_name='speciesreference',
            old_name='documentation_text',
            new_name='distribution',
        ),
        migrations.AlterField(
            model_name='species',
            name='name_common_ref',
            field=models.CharField(blank=True, help_text='Enter if different from COL common name', max_length=255, verbose_name='common name (reference)'),
        ),
    ]
