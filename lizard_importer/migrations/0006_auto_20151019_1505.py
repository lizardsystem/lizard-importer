# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lizard_importer', '0005_auto_20151015_0500'),
    ]

    operations = [
        migrations.CreateModel(
            name='SourceActionLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('runtype', models.CharField(max_length=50, choices=[('CHECK', 'CHECK'), ('IMPORT', 'IMPORT')])),
                ('run_date', models.DateTimeField(null=True, blank=True)),
                ('run_by', models.CharField(max_length=255)),
                ('validated', models.BooleanField(default=False, verbose_name='validated')),
                ('imported', models.BooleanField(default=False, verbose_name='imported')),
                ('action_log', models.TextField(null=True, blank=True)),
            ],
            options={
                'ordering': ['source__name', 'run_date'],
                'verbose_name': 'Source Action Log',
                'verbose_name_plural': 'Source Action Log',
            },
        ),
        migrations.RemoveField(
            model_name='source',
            name='imported',
        ),
        migrations.RemoveField(
            model_name='source',
            name='validated',
        ),
        migrations.AlterField(
            model_name='importfile',
            name='attachment',
            field=models.FileField(upload_to=b'/home/alexandr/projecten/git/nens/spoc-hhnk/var/media', verbose_name='File'),
        ),
        migrations.AlterField(
            model_name='source',
            name='name',
            field=models.CharField(default='test', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='sourceactionlog',
            name='source',
            field=models.ForeignKey(to='lizard_importer.Source'),
        ),
    ]
