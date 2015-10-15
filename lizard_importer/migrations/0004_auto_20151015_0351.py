# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lizard_importer', '0003_auto_20151014_1012'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='mapping',
            options={'ordering': ['code'], 'verbose_name': 'Mapping'},
        ),
    ]
