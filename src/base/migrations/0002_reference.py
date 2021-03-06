# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-10-10 23:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Reference',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('zotero', models.CharField(max_length=8, verbose_name='zotero ID')),
                ('name', models.CharField(max_length=255)),
                ('name_short', models.CharField(max_length=100)),
                ('year', models.IntegerField()),
                ('description', models.TextField(blank=True)),
                ('last_modified', models.DateTimeField(auto_now=True, verbose_name='last modified')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
    ]
