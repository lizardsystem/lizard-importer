# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


class Mapping(models.Model):

    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)
    target_table = models.CharField(
        max_length=255,
        verbose_name=_("Import table"))
    field_separator = models.CharField(
        max_length=3,
        default=";",
        verbose_name=_("Field separator"))

    class Meta:
        ordering = ['code']
        verbose_name = _("Mapping")

    def __unicode__(self):
        return self.code


class ImportFile(models.Model):
    attachment = models.FileField(
        upload_to=settings.UPLOAD_DIR,
        verbose_name=_("File")
    )
    uploaded_by = models.CharField(
        max_length=200,
        blank=True)
    uploaded_date = models.DateTimeField(
        blank=True,
        null=True)

    def __unicode__(self):
        import pdb; pdb.set_trace()
    
    class Meta:
        ordering = ['uploaded_by']
        verbose_name = _("Files")
        verbose_name_plural = _("Files")


class FTPLocation(models.Model):

    hostname = models.CharField(
        max_length=255)
    username = models.CharField(
        max_length=255)
    password = models.CharField(
        max_length=255)
    directory = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Base directory (TEST or PROD, currently)"))

    class Meta:
        ordering = ['hostname']
        verbose_name = _("FTP location")
        verbose_name_plural = _("FTP location")

    def __unicode__(self):
        if self.directory:
            return _('FTP location %s/%s') % (self.hostname, self.directory)
        else:
            return _('FTP location %s') % self.hostname


class Source(models.Model):

    name = models.CharField(
        max_length=100,
        blank=True,
        null=True)
    import_file = models.ForeignKey(
        ImportFile,
        null=True,
        blank=True,
        verbose_name=_("File")
    )
    import_dir = models.CharField(
        max_length=255,
        null=True,
        blank=True)
    ftp_location = models.ForeignKey(
        FTPLocation,
        null=True,
        blank=True)
    mapping = models.ForeignKey(
       Mapping,
       blank=True,
       null=True)
    validated = models.BooleanField(
        verbose_name=_("validated"),
        default=False)
    imported = models.BooleanField(
        verbose_name=_("imported"),
        default=False)
    active = models.BooleanField(default=True)
    task = models.CharField(max_length=250,
                            null=True,
                            blank=True)

    def __unicode__(self):
        return 'import run %s' % (self.name)

    @property
    def has_attachment_file(self):
        if not self.attachment:
            return False
        if not os.path.isfile(self.attachment.path):
            return False
        return True

    @property
    def has_csv_attachment(self):
        if self.has_attachment_file:
            file_ext = os.path.splitext(self.attachment.file.name)[1]
            if file_ext == '.csv':
                return True
        return False

    @property
    def has_xml_attachment(self):
        if self.has_attachment_file:
            file_ext = os.path.splitext(self.attachment.file.name)[1]
            if file_ext == '.xml':
                return True
        return False

    def can_run_any_action(self):
        """Check fields of import_run."""
        can_run = True
        messages = []
        if self.attachment:
            if not os.path.isfile(self.attachment.path):
                messages.append(
                    "het bestand '%s' is niet "
                    "aanwezig." % self.attachment.path)
                can_run = False
            if not (self.has_csv_attachment or self.has_xml_attachment):
                messages.append(
                    "de bestandextensie is geen "
                    ".csv of .xml")
                can_run = False
        else:
            messages.append("geen bestand")
            can_run = False

        if not self.import_mapping and self.has_csv_attachment:
            messages.append("geen mapping")
            can_run = False
        if not self.activiteit:
            messages.append("geen activiteit")
            can_run = False
        return (can_run, messages)

    def add_log_line(self, text, username=None):
        """Add log text including timestamp."""
        datetime_format = '%Y-%m-%d %H:%M'
        datetime_string = datetime.now().strftime(datetime_format)
        if username:
            datetime_string = datetime_string + ' ' + username
        text = '%s: %s\n' % (datetime_string, text)
        self.action_log = utils.add_text_to_top(self.action_log, text)

    def add_log_separator(self):
        """Add separator line to action log."""
        text = '-------------------------------\n'
        self.action_log = utils.add_text_to_top(self.action_log, text)

    def action_log_for_logfile(self):
        """Return action log string in regular date order."""
        lines = self.action_log.split('\n')
        lines.reverse()
        return '\n'.join(lines)


class MappingField(models.Model):

    db_field = models.CharField(max_length=255)
    file_field = models.CharField(max_length=255)
    datatype = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=_('DataType like float or related table.'))
    foreignkey_field = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=_('Field name of a Foreign table, usualy id or code.'))
    mapping = models.ForeignKey(Mapping)
    data_format = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="example: %d-%m-%Y as date format.")

    def __unicode__(self):
        return '{0}-{1}'.format(self.db_field, self.file_field)

    class Meta:
        ordering = ['db_field']
        verbose_name = _("mapping field")
        verbose_name_plural = _("mapping field")
