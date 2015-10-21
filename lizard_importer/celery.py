from __future__ import absolute_import

import os
import datetime

from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lizard_importer.testsettings')

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from lizard_importer import models
from lizard_importer.import_data import DataImport

app = Celery('lizard_importer')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
# app.conf.update(
#     CELERY_RESULT_BACKEND='djcelery.backends.database:DatabaseBackend',
#     BROKER_URL='django://',
#     CELERYBEAT_SCHEDULER='djcelery.schedulers.DatabaseScheduler',
# )


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))


@app.task(bind=True)
def check_csv_file(self, *args, **kwargs):
    """Check passed importrun or
    all active automatic importruns"""

    data_import = DataImport()
    result = False
    username = kwargs['username']
    source_action_log_id = kwargs['source_action_log_id']
    source_action_log = models.SourceActionLog.objects.get(
        pk=source_action_log_id)
    source_action_log.runtype = models.SourceActionLog.CSV_CHECK
    source_action_log.run_by = username
    source_action_log.run_date = datetime.datetime.now()
    source_action_log.add_log_separator()
    source_action_log.add_log_line("Start csv-check", username=username)
    source_action_log.save()
    
    csv_files = source_action_log.source.get_csv_files()
    for csv_file in csv_files:
        source_action_log.add_log_line(
            _("Check file %s") % csv_file)
        source_action_log.save(force_update=True, update_fields=['action_log'])
        result = data_import.check_csv(source_action_log, csv_file)
        source_action_log.add_log_line(_("End csv-check file %s is %s") % (
            csv_file, result))
        source_action_log.save(force_update=True, update_fields=['action_log'])

    if not csv_file:
        source_action_log.add_log_line(
            _("No any .csv to check."))
    source_action_log.add_log_line(_("Eind csv_check"), username=username)
    source_action_log.validated = result
    source_action_log.save()


@app.task(bind=True)
def import_csv_file(self, *args, **kwargs):
    """Import passed importrun or
    all active automatic importruns"""

    data_import = DataImport()
    result = False

    username = kwargs['username']
    source_action_log_id = kwargs['source_action_log_id']
    source_action_log = models.SourceActionLog.objects.get(
        pk=source_action_log_id)
    source_action_log.run_by = username
    source_action_log.run_date = datetime.datetime.now()
    source_action_log.runtype = models.SourceActionLog.CSV_IMPORT
    source_action_log.add_log_separator()
    source_action_log.add_log_line("Start csv-import", username=username)
    source_action_log.save()
    
    csv_files = source_action_log.source.get_csv_files()
    for csv_file in csv_files:
        source_action_log.add_log_line(
            _("Import file %s") % csv_file)
        source_action_log.save(force_update=True, update_fields=['action_log'])
        result = data_import.import_csv(source_action_log, csv_file)
        source_action_log.add_log_line(_("Einde import-check file %s is %s") % (
            csv_file, result))
        source_action_log.save(force_update=True, update_fields=['action_log'])

    if not csv_file:
        source_action_log.add_log_line(
            _("No any .csv to import."))
    source_action_log.add_log_line(_("Eind csv_import"), username=username)
    source_action_log.imported = result
    source_action_log.save()
