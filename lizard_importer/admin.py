# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import celery
#from celery.execute import send_task
from django import forms
from django.contrib import admin
from django.contrib import messages

from django.utils.translation import ugettext_lazy as _

from lizard_importer import models
from lizard_importer import utils


TASK_CHOICES = utils.task_choices()
MODEL_CHOICES = utils.model_choices()
FK_MODEL_CHOICES = utils.fk_model_choices()


def run_source(modeladmin, request, queryset):
    username = request.user.get_full_name()
    if not username:
        username = request.user.username
    for source in queryset:
        if not source.active:
            messages.warning(
                request,
                _("Source '%s' is not active." % source.name)
            )
            continue
        source_action_log = source.lizard_importer_sourceactionlog_set.create()
        celery.app.send_task(
            source.task,
            kwargs={'username': username,
             'source_action_log_id': source_action_log.id})
run_source.short_description = _("Run selected sources")


@admin.register(models.ImportFile)
class ImportFileAdmin(admin.ModelAdmin):
    list_display = ('pk',
                    'attachment',
                    'uploaded_by',
                    'uploaded_date')
    

class TaskChoicesForm(forms.ModelForm):
    task = forms.ChoiceField(choices=TASK_CHOICES)


class SourceActionLogInlineAdmin(admin.TabularInline):
    model = models.SourceActionLog
    extra = 0


@admin.register(models.Source)
class SourceAdmin(admin.ModelAdmin):
    fields = ['name',
              'task',
              'import_file',
              'import_dir',
              'ftp_location',
              'mapping',
              'active']
    form = TaskChoicesForm
    actions = [run_source]
    inlines = [SourceActionLogInlineAdmin]


class DataTypeChoicesForm(forms.ModelForm):
    datatype_choices = [
        ('', ''),
        ('CharField', 'CharField'),
        ('TextField', 'TextField'),
        ('float', 'float'),
        ('date', 'date'),
        ('time', 'time')
    ] + FK_MODEL_CHOICES

    datatype = forms.ChoiceField(
        choices=datatype_choices,
        label=_("Data type")
    )


class TargetTableChoicesForm(forms.ModelForm):
    target_table = forms.ChoiceField(choices=MODEL_CHOICES)


class MappingFieldInlineAdmin(admin.TabularInline):
    model = models.MappingField
    list_display = ['db_field',
                    'file_field',
                    'datatype',
                    'foreignkey_field',
                    'data_format',
    ]
    form = DataTypeChoicesForm


@admin.register(models.Mapping)
class MappingAdmin(admin.ModelAdmin):
    list_display = ['code',
                    'description',
                    'target_table',
                    'field_separator',
    ]
    form = TargetTableChoicesForm
    inlines = [MappingFieldInlineAdmin]


@admin.register(models.FTPLocation)
class FTPLocationAdmin(admin.ModelAdmin):
    list_display = ('hostname',
                    'username',
                    'password',
                    'directory')
