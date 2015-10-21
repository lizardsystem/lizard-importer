# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lizard_importer', '0006_auto_20151019_1505'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sourceactionlog',
            name='source',
            field=models.ForeignKey(related_name='lizard_importer_sourceactionlog_related_source_action_log', to='lizard_importer.Source'),
        ),
    ]
