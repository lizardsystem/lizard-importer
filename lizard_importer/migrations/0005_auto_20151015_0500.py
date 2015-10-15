# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lizard_importer', '0004_auto_20151015_0351'),
    ]

    operations = [
        migrations.RenameField(
            model_name='source',
            old_name='actief',
            new_name='active',
        ),
    ]
