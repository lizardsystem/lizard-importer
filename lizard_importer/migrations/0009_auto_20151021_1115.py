# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lizard_importer', '0008_auto_20151019_1523'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='sourceactionlog',
            options={'ordering': ['source__name', '-run_date'], 'verbose_name': 'Source Action Log', 'verbose_name_plural': 'Source Action Log'},
        ),
        migrations.AlterField(
            model_name='sourceactionlog',
            name='runtype',
            field=models.CharField(max_length=50, choices=[('CSV-CHECK', 'CSV-CHECK'), ('CSV-IMPORT', 'CSV-IMPORT')]),
        ),
    ]
