# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lizard_importer', '0002_auto_20151014_0719'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mapping',
            name='target_table',
            field=models.CharField(max_length=255, verbose_name='Import table'),
        ),
        migrations.DeleteModel(
            name='TargetTable',
        ),
    ]
