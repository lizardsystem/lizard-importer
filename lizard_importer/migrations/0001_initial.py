# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FTPLocation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('hostname', models.CharField(max_length=255)),
                ('username', models.CharField(max_length=255)),
                ('password', models.CharField(max_length=255)),
                ('directory', models.CharField(help_text='Base directory (TEST or PROD, currently)', max_length=255, blank=True)),
            ],
            options={
                'ordering': ['hostname'],
                'verbose_name': 'FTP location',
                'verbose_name_plural': 'FTP location',
            },
        ),
        migrations.CreateModel(
            name='ImportFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('attachment', models.FileField(upload_to=b'/home/alexandr/projecten/git/nens/lizard-importer/var/media', verbose_name='File')),
                ('uploaded_by', models.CharField(max_length=200, blank=True)),
                ('uploaded_date', models.DateTimeField(null=True, blank=True)),
            ],
            options={
                'ordering': ['uploaded_by'],
                'verbose_name': 'Files',
                'verbose_name_plural': 'Files',
            },
        ),
        migrations.CreateModel(
            name='Mapping',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(unique=True, max_length=50)),
                ('description', models.TextField(null=True, blank=True)),
                ('field_separator', models.CharField(default=';', max_length=3, verbose_name='Field separator')),
            ],
            options={
                'ordering': ['code'],
                'verbose_name': 'Fields mapping',
            },
        ),
        migrations.CreateModel(
            name='MappingField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('db_field', models.CharField(max_length=255)),
                ('file_field', models.CharField(max_length=255)),
                ('db_datatype', models.CharField(blank=True, max_length=255, null=True, help_text='DataType like float or related table.', choices=[('CharField', 'CharField'), ('TextField', 'TextField'), ('float', 'float'), ('date', 'date'), ('time', 'time')])),
                ('foreignkey_field', models.CharField(help_text='Field name of a Foreign table, usualy id or code.', max_length=255, null=True, blank=True)),
                ('data_format', models.CharField(help_text='example: %d-%m-%Y as date format.', max_length=50, null=True, blank=True)),
            ],
            options={
                'ordering': ['db_field'],
                'verbose_name': 'mapping field',
                'verbose_name_plural': 'mapping field',
            },
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, null=True, blank=True)),
                ('import_dir', models.CharField(max_length=255, null=True, blank=True)),
                ('validated', models.BooleanField(default=False, verbose_name='validated')),
                ('imported', models.BooleanField(default=False, verbose_name='imported')),
                ('actief', models.BooleanField(default=True)),
                ('task', models.CharField(max_length=250, null=True, blank=True)),
                ('ftp_location', models.ForeignKey(blank=True, to='lizard_importer.FTPLocation', null=True)),
                ('import_file', models.ForeignKey(verbose_name='File', blank=True, to='lizard_importer.ImportFile', null=True)),
                ('mapping', models.ForeignKey(blank=True, to='lizard_importer.Mapping', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='TargetTable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('is_fk', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='mapping',
            name='target_table',
            field=models.ForeignKey(verbose_name='Import table', to='lizard_importer.TargetTable'),
        ),
    ]
