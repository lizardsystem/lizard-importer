# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lizard_importer', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mappingfield',
            name='db_datatype',
        ),
        migrations.AddField(
            model_name='mappingfield',
            name='datatype',
            field=models.CharField(help_text='DataType like float or related table.', max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='mappingfield',
            name='mapping',
            field=models.ForeignKey(default=1, to='lizard_importer.Mapping'),
            preserve_default=False,
        ),
    ]
