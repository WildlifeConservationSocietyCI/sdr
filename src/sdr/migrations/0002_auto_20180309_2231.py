# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-03-09 22:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sdr', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='feature',
            name='last_modified',
            field=models.DateTimeField(auto_now=True, verbose_name='last modified'),
        ),
        migrations.AddField(
            model_name='georef',
            name='last_modified',
            field=models.DateTimeField(auto_now=True, verbose_name='last modified'),
        ),
        migrations.AddField(
            model_name='scan',
            name='last_modified',
            field=models.DateTimeField(auto_now=True, verbose_name='last modified'),
        ),
    ]