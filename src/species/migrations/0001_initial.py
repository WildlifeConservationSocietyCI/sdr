# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-10-10 23:26
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('base', '0002_reference'),
    ]

    operations = [
        migrations.CreateModel(
            name='Family',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name_plural': 'families',
            },
        ),
        migrations.CreateModel(
            name='Genus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('family', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='species.Family')),
            ],
            options={
                'ordering': ('name',),
                'verbose_name_plural': 'genera',
            },
        ),
        migrations.CreateModel(
            name='Likelihood',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Species',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('name_common', models.CharField(max_length=255, verbose_name='common name')),
                ('col', models.CharField(max_length=32, verbose_name='Catalog of Life ID')),
                ('introduced', models.BooleanField(default=False)),
                ('notes', models.TextField(blank=True)),
                ('genus', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='species.Genus')),
                ('historical_likelihood', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='species.Likelihood')),
            ],
            options={
                'ordering': ['taxon', 'genus__family', 'genus', 'name'],
            },
        ),
        migrations.CreateModel(
            name='SpeciesReference',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('documentation_text', models.TextField(blank=True)),
                ('pagenumbers', models.CharField(blank=True, max_length=255)),
                ('reference', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.Reference')),
                ('species', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='species.Species')),
            ],
            options={
                'ordering': ('species', 'reference'),
            },
        ),
        migrations.CreateModel(
            name='Taxon',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name_plural': 'taxa',
            },
        ),
        migrations.AddField(
            model_name='species',
            name='taxon',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='species.Taxon'),
        ),
    ]