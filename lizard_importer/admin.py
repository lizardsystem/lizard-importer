# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import celery
#from celery.execute import send_task
from django import forms
from django.contrib import admin
from django.contrib import messages
from django.db import models as django_models
from django.utils.translation import ugettext_lazy as _
from django_admin_bootstrapped.admin.models import SortableInline

from lizard_importer import models


EXCLUDED_APPS = [
    'django',
    'admin',
    'auth',
    'sessions',
    'contenttypes',
    'sites',
    'djcelery',
    'kombu',
    'lizard_importer',
]


def task_choices():
    tasks = [('', '')]
    for task_name in celery.app.tasks.keys():
        if not task_name.lower().startswith('celery'):
            tasks.append((task_name, task_name))
    return tasks


def model_choices():
    target_models = [('', '')]

    for m in django_models.get_models():        
        if m._meta.app_label not in EXCLUDED_APPS:
            model_full_name = '%s.%s' % (
                m._meta.app_label, m._meta.model_name)
            target_models.append((model_full_name, model_full_name))
    return target_models


def fk_model_choices():
    fk_models = []
    related_models = {}

    for m in django_models.get_models():        
        if m._meta.app_label in EXCLUDED_APPS:
            continue
        for rel_field in m._meta.get_all_related_objects():
            model_full_name = '%s.%s' % (
                rel_field.model._meta.app_label, rel_field.model._meta.model_name)
            related_models[model_full_name] = None
    
    fk_models += [(key, key) for key in related_models.keys()]
    return fk_models


def import_source(modeladmin, request, queryset):

    for source in queryset:
        if not source.active:
            messages.warning(
                request,
                _("Source '%s' is not active." % source.name)
            )
            continue

        send_task(
            source.task,
            mapping=source.mapping,
            import_file=source.import_file,
            ftp_location=source.ftp_location)
        messages.success(
            request,
            _("Source '%s' is send to the worker.") % source.name)
import_source.short_description = _("Import selected sources")


@admin.register(models.ImportFile)
class ImportFileAdmin(admin.ModelAdmin):
    list_display = ('pk',
                    'attachment',
                    'uploaded_by',
                    'uploaded_date')
    

class TaskChoicesForm(forms.ModelForm):
    task = forms.ChoiceField(choices=task_choices())


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
    actions = [import_source]

class DataTypeChoicesForm(forms.ModelForm):
    datatype_choices = [
        ('', ''),
        ('CharField', 'CharField'),
        ('TextField', 'TextField'),
        ('float', 'float'),
        ('date', 'date'),
        ('time', 'time')
    ] + fk_model_choices()

    datatype = forms.ChoiceField(
        choices=datatype_choices,
        label=_("Data type")
    )


class TargetTableChoicesForm(forms.ModelForm):
    target_table = forms.ChoiceField(choices=model_choices)


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
