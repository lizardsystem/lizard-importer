from datetime import datetime
import csv
import logging
import os

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.db import models as django_models
from django.db.models import ManyToManyField

from lizard_importer import models
from lizard_importer import utils


logger = logging.getLogger(__name__)


class DataImport(object):
    help = '''
    Expect decimals compared with a point.
    '''

    def __init__(self):
        self.log = False
        self.data_dir = os.path.join(
            settings.UPLOAD_DIR)

    def _datestr_to_date(self, datestr):
        dt = None
        try:
            if datestr:
                dt = datetime.strptime(
                    datestr,
                    settings.IMPORT_DATE_FORMAT).date()
        except ValueError as err:
            logger.debug(err.message)
        except TypeError as err:
            logger.debug(err.message)
        return dt

    def _str_to_float(self, floatstr):
        fl = None
        try:
            if floatstr:
                fl = float(floatstr.replace(',', '.'))
        except ValueError as err:
            logger.debug(err.message)
        except:
            logger.debug("THE rest")
        return fl

    def _remove_leading_quotes(self, quotedstr):

        if not isinstance(quotedstr, str):
            return quotedstr

        newstr = quotedstr.strip('"')

        return newstr

    def _get_foreignkey_inst(
            self, val_raw, datatype, foreignkey_field, log=False):
        class_inst = django_models.get_model(datatype)
        inst = None
        try:
            if datatype == 'WNS' and foreignkey_field == 'wns_oms':
                if self.log:
                    logger.info("get wns %s %s" % (
                        datatype, ''.join(val_raw.split(' '))))
                inst = class_inst.objects.get(
                    wns_oms__iexact=''.join(val_raw.split(' ')))
            else:
                inst = class_inst.objects.get(
                    **{foreignkey_field: val_raw})
        except Exception as ex:
            if self.log:
                logger.error(
                    '{0}, Value: "{1}"'.format(ex.message, val_raw))
        return inst

    def check_many2many_data(self,  inst, mapping, row, headers):
        """Check many2many value exists."""
        for mapping_field in mapping:
            value = row[headers.index(mapping_field.file_field)].strip(' "')
            if value in [None, '']:
                continue
            if isinstance(
                inst._meta.get_field(mapping_field.db_field),
                ManyToManyField
            ):
                datatype = mapping_field.datatype
                class_inst = django_models.get_model(datatype)
                class_inst.objects.get(**{mapping_field.foreignkey_field: value})

    def set_many2many_data(self, inst, mapping, row, headers):
        for mapping_field in mapping:
            value = row[headers.index(mapping_field.file_field)].strip(' "')
            if value in [None, '']:
                continue
            if isinstance(
                inst._meta.get_field(mapping_field.db_field),
                ManyToManyField
            ):
                values = list(inst._meta.get_field(
                    mapping_field.db_field).value_from_object(inst))
                values.append(value)
                setattr(inst, mapping_field.db_field, values)

    def set_data(self, inst, mapping, row, headers):
        """Set values to model instance. """
        fk_models = utils.fk_models()
        for mapping_field in mapping:
            if isinstance(
                inst._meta.get_field(mapping_field.db_field),
                ManyToManyField
            ):
                continue
            value = None
            val_raw = None
            datatype = mapping_field.datatype
            if not val_raw:
                val_raw = row[headers.index(mapping_field.file_field)].strip(' "')
            if datatype == 'date':
                try:
                    value = datetime.strptime(
                        val_raw, mapping_field.data_format)
                except:
                    logger.info(_("Error on date formating: %s, %s, %s.") % (
                        mapping_field.db_field, val_raw,  mapping_field.data_format))
                    continue
            elif datatype == 'time':
                try:
                    value = datetime.strptime(
                        val_raw, mapping_field.data_format)
                except:
                    logger.info(_("Error on time formating: %s, %s, %s.") % (
                        mapping_field.db_field, val_raw,  mapping_field.data_format))
                    continue
            elif datatype == 'float':
                value = self._str_to_float(val_raw)
            elif datatype in fk_models:
                val_space_omitted = val_raw
                if val_space_omitted:
                    val_space_omitted = val_space_omitted.strip(' ')
                value = self._get_foreignkey_inst(
                    val_space_omitted,
                    datatype,
                    mapping_field.foreignkey_field)
                if value is None:
                    if self.log:
                        logger.error("Value is None.")
                    continue
            elif datatype == 'boolean':
                value = bool(val_raw.lower() in ['true', 'ja', '1'])
            else:
                if val_raw == '':
                    val_raw = None
                value = val_raw

            if self.log:
                logger.info("setattr %s, %s, %s." % (
                    mapping_field.db_field, value, type(value)))
            setattr(inst, mapping_field.db_field, value)

    def save_action_log(self, source_action_log, message):
        source_action_log.add_log_line(message)
        source_action_log.save(force_update=True, update_fields=['action_log'])

    def check_csv(self, source_action_log, filepath):
        """TODO create separate function per validation."""
        mapping_code = source_action_log.source.mapping.code
        mapping = source_action_log.source.mapping
        is_valid = True

        logger.info("File check {}.".format(filepath))

        # Check or mapping contains fields
        mapping_fields = mapping.mappingfield_set.all()
        if mapping_fields.count() <= 0:
            message = "%s %s." % (
                "Geen veld in mapping",
                mapping_code)
            self.save_action_log(source_action_log, message)
            is_valid = False

        # Check delimeter
        if not mapping.field_separator or len(mapping.field_separator) > 1:
            message = "%s %s." % (
                "Scheidingsteken moet 1-character string zijn i.p.v.",
                mapping.field_separator)
            self.save_action_log(source_action_log, message)
            is_valid = False

        if not is_valid:
            return is_valid

        # check headers
        with open(filepath, 'rb') as f:
            reader = csv.reader(f, delimiter=str(mapping.field_separator))
            headers = reader.next()
            if not headers:
                message = "%s %s." % (
                    "Bestand is leeg",
                    filepath)
                self.save_action_log(source_action_log, message)
                is_valid = False
            if headers and len(headers) <= 1:
                message = "%s %s." % (
                    "Scheidingsteken is onjuist of het header bevat "
                    "alleen 1 veld",
                    headers[0])
                self.save_action_log(source_action_log, message)
                is_valid = False

        if not is_valid:
            return is_valid

        # check mapping
        with open(filepath, 'rb') as f:
            reader = csv.reader(f, delimiter=str(mapping.field_separator))
            headers = reader.next()
            for mapping_field in mapping_fields:
                if mapping_field.file_field.find('[') >= 0:
                    continue
                if mapping_field.file_field not in headers:
                    message = "CSV-header bevat geen veld %s" % (
                        mapping_field.file_field)
                    self.save_action_log(source_action_log, message)
                    is_valid = False

        if not is_valid:
            return is_valid

        # check data integrity
        with open(filepath, 'rb') as f:
            reader = csv.reader(f, delimiter=str(mapping.field_separator))
            headers = reader.next()
            counter = 0
            count_updates = 0
            count_imports = 0
            for row in reader:
                counter += 1
                if len(row) != len(headers):
                    message = "regelnr.: %s, %d." % (
                        "Aantal kolommen komt niet overeen "
                        "met het aantal headers",
                        reader.line_num)
                    self.save_action_log(source_action_log, message)
                    is_valid = False
                inst_class = django_models.get_model(mapping.target_table)
                inst = inst_class()
                try:
                    self.set_data(inst, mapping_fields, row, headers)
                    if inst.pk and inst_class.objects.filter(pk=inst.pk).exists():
                        count_updates += 1
                        fields_excluded = []
                        for inst_field in inst._meta.fields:
                            if inst_field.unique or inst_field.primary_key:
                                fields_excluded.append(inst_field)
                        inst.clean_fields(exclude=fields_excluded)
                    else:
                        count_imports += 1
                        inst.clean_fields(exclude='pk')
                except ValidationError as e:
                    message = "  regelnr.: %d, Foutmeldingen - %s" % (
                        reader.line_num,
                        ", ".join(["%s: %s" % (k, ", ".join(v)) for k, v in e.message_dict.iteritems()])
                    )
                    self.save_action_log(source_action_log, message)
                    is_valid = False
                except Exception as e:
                    message = "  regelnr.: %d, overige foutmelding - %s" % (
                        reader.line_num,
                        e.message)
                    self.save_action_log(source_action_log, message)
                    is_valid = False

            message = "Aantal rijen %d, waarvan %d nieuwe en %d bestaande." % (
                counter, count_imports, count_updates)
            self.save_action_log(source_action_log, message)
        return is_valid


    def import_csv(self, source_action_log, filepath):

        is_imported = False
        mapping = source_action_log.source.mapping
        mapping_fields = mapping.mappingfield_set.all()

        count_imports = 0
        count_updates = 0
        count_errors = 0
        counter = 0
        with open(filepath, 'rb') as f:
            reader = csv.reader(f, delimiter=str(mapping.field_separator))
            # read headers
            headers = reader.next()
            for row in reader:
                counter += 1
                inst_class = django_models.get_model(mapping.target_table)
                inst = inst_class()
                try:
                    self.set_data(inst, mapping_fields, row, headers)
                    if inst.pk and inst_class.objects.filter(pk=inst.pk).exists():
                        # update
                        fields_to_update = mapping_fields.values_list(
                            'db_field', flat=True)
                        inst.save(force_update=True, update_fields=fields_to_update)
                        count_updates += 1
                    else:
                        # insert
                        inst.save()
                        count_imports += 1
                except IntegrityError as ex:
                    count_errors += 1
                    message = "regelnr.: %d, Foutmelding %s" % (
                        reader.line_num, ex.message)
                    self.save_action_log(source_action_log, message)
                except Exception as ex:
                    count_errors += 1
                    logger.error("%s." % ex.message)
                    message = "regelnr.: %d, Foutmelding %s" % (
                        reader.line_num, ex.message)
                    self.save_action_log(source_action_log, message)
                    break
        is_imported = True
        message = "Aantal rijen %d, waarvan %d toegevoegd, %d geupdated, "\
                  "%d niet toegevoegd/geupdated objecten" % (
                      counter, count_imports, count_updates, count_errors)
        self.save_action_log(source_action_log, message)
        return is_imported
