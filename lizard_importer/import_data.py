from datetime import datetime
import csv
import logging
import os

from django.conf import settings

from django.db import IntegrityError
from django.db import models as django_models
from django.db.models import ManyToManyField

from lizard_importer import models

logger = logging.getLogger(__name__)


class DataImport(object):
    help = '''
    Expect decimals compared with a point.
    '''

    def __init__(self):
        self.log = False
        self.data_dir = os.path.join(
            settings.DATA_IMPORT_DIR, 'domain')


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
        class_inst = django_models.get_model('lizard_efcis', datatype)
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
                datatype = mapping_field.db_datatype
                class_inst = django_models.get_model('lizard_efcis', datatype)
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
        fk_models = models.TargetTable.objects.filter(is_fk=True).values_list('name', flat=True)
        for mapping_field in mapping:
            if isinstance(
                inst._meta.get_field(mapping_field.db_field),
                ManyToManyField
            ):
                continue
            value = None
            val_raw = None
            datatype = mapping_field.db_datatype
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
                    logger.info(_("Error on time formating: %s, %s, %s." % (
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

    def check_csv(self, import_run, datetime_format, ignore_duplicate_key=True):
        """TODO create separate function per validation."""
        filepath = import_run.attachment.path
        mapping_code = import_run.import_mapping.code
        mapping = import_run.import_mapping
        is_valid = True

        logger.info("File check {}.".format(filepath))

        # Check or mapping contains fields
        mapping_fields = mapping.mappingfield_set.all()
        if mapping_fields.count() <= 0:
            message = "%s %s." % (
                "Geen veld in mapping",
                mapping_code)
            self.save_action_log(import_run, message)
            is_valid = False

        # Check delimeter
        if not mapping.scheiding_teken or len(mapping.scheiding_teken) > 1:
            message = "%s %s." % (
                "Scheidingsteken moet 1-character string zijn i.p.v.",
                mapping.scheiding_teken)
            self.save_action_log(import_run, message)
            is_valid = False

        if not is_valid:
            return is_valid

        # check headers
        with open(filepath, 'rb') as f:
            reader = csv.reader(f, delimiter=str(mapping.scheiding_teken))
            headers = reader.next()
            if not headers:
                message = "%s %s." % (
                    "Bestand is leeg",
                    filepath)
                self.save_action_log(import_run, message)
                is_valid = False
            if headers and len(headers) <= 1:
                message = "%s %s." % (
                    "Scheidingsteken is onjuist of het header bevat "
                    "alleen 1 veld",
                    headers[0])
                self.save_action_log(import_run, message)
                is_valid = False

        if not is_valid:
            return is_valid

        # check mapping
        with open(filepath, 'rb') as f:
            reader = csv.reader(f, delimiter=str(mapping.scheiding_teken))
            headers = reader.next()
            for mapping_field in mapping_fields:
                if mapping_field.file_field.find('[') >= 0:
                    continue
                if mapping_field.file_field not in headers:
                    message = "CSV-header bevat geen veld %s" % (
                        mapping_field.file_field)
                    self.save_action_log(import_run, message)
                    is_valid = False

        if not is_valid:
            return is_valid

        # check data integrity
        with open(filepath, 'rb') as f:
            reader = csv.reader(f, delimiter=str(mapping.scheiding_teken))
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
                    self.save_action_log(import_run, message)
                    is_valid = False
                inst = django_models.get_model(
                    'lizard_efcis',
                    mapping.tabel_naam)()
                try:
                    self.set_data(inst, mapping_fields, row, headers)
                    if hasattr(inst.__class__, 'activiteit') and not hasattr(inst, 'activiteit'):
                        setattr(inst, 'activiteit', import_run.activiteit)
                    if isinstance(inst, models.Locatie):
                        self.check_many2many_data(inst, mapping_fields, row, headers)
                    if inst.id:
                        count_updates += 1
                        fields_excluded = []
                        for inst_field in inst._meta.fields:
                            if inst_field.unique or inst_field.primary_key:
                                fields_excluded.append(inst_field)
                        inst.clean_fields(exclude=fields_excluded)
                    else:
                        count_imports += 1
                        inst.clean_fields(exclude='id')
                except ValidationError as e:
                    message = "  regelnr.: %d, Foutmeldingen - %s" % (
                        reader.line_num,
                        ", ".join(["%s: %s" % (k, ", ".join(v)) for k, v in e.message_dict.iteritems()])
                    )
                    self.save_action_log(import_run, message)
                    is_valid = False
                except Exception as e:
                    message = "  regelnr.: %d, overige foutmelding - %s" % (
                        reader.line_num,
                        e.message)
                    self.save_action_log(import_run, message)
                    is_valid = False

            message = "Aantal rijen %d, waarvan %d nieuwe en %d bestaande." % (
                counter, count_imports, count_updates)
            self.save_action_log(import_run, message)
        return is_valid

    def import_csv(self, filename, mapping_code,
                   activiteit=None, ignore_duplicate_key=True):
        logger.info("Import {}.".format(mapping_code))
        mapping = models.ImportMapping.objects.get(code=mapping_code)
        mapping_fields = mapping.mappingfield_set.all()
        filepath = os.path.join(self.data_dir, filename)
        if not os.path.isfile(filepath):
            logger.warn(
                "Stop import {0}, dit is geen file '{1}'.".format(
                    mapping_code, filepath))
            return

        created = 0
        with open(filepath, 'rb') as f:
            reader = csv.reader(f, delimiter=str(mapping.scheiding_teken))
            # read headers
            headers = reader.next()
            for row in reader:
                inst = django_models.get_model('lizard_efcis',
                                               mapping.tabel_naam)()
                if activiteit and hasattr(inst.__class__, 'activiteit'):
                    inst.activiteit = activiteit
                try:
                    self.set_data(inst, mapping_fields, row, headers)
                    inst.save()
                    if isinstance(inst, models.Locatie):
                        self.set_many2many_data(inst, mapping_fields, row, headers)
                        inst.save()
                    created = created + 1
                except IntegrityError as ex:
                    if ignore_duplicate_key:
                        continue
                    else:
                        logger.error(ex.message)
                        break
        logger.info(
            'End import: created={}.'.format(created))

    def manual_import_csv(self, import_run, datetime_format, ignore_duplicate_key=True):

        is_imported = False
        filepath = import_run.attachment.path
        mapping = import_run.import_mapping
        activiteit = import_run.activiteit
        mapping_fields = mapping.mappingfield_set.all()

        count_imports = 0
        count_updates = 0
        count_errors = 0
        counter = 0
        with open(filepath, 'rb') as f:
            reader = csv.reader(f, delimiter=str(mapping.scheiding_teken))
            # read headers
            headers = reader.next()
            for row in reader:
                counter += 1
                inst = django_models.get_model('lizard_efcis',
                                               mapping.tabel_naam)()
                try:
                    self.set_data(inst, mapping_fields, row, headers)
                    if mapping.tabel_naam == 'Opname':
                        setattr(inst, 'import_run', import_run)
                        setattr(inst, 'activiteit', activiteit)
                    if inst.id:
                        # exlude id and many2many fields
                        if isinstance(inst, models.Locatie):
                            fields_to_update = mapping_fields.exclude(
                                db_datatype='Meetnet').exclude(db_field='id').values_list('db_field', flat=True)
                        else:
                            fields_to_update = mapping_fields.exclude(
                                db_field='id').values_list('db_field', flat=True)
                        inst.save(force_update=True, update_fields=fields_to_update)
                        count_updates += 1
                    else:
                        inst.save()
                        count_imports += 1
                    if isinstance(inst, models.Locatie):
                        self.set_many2many_data(inst, mapping_fields, row, headers)
                        inst.save()
                except IntegrityError as ex:
                    count_errors += 1
                    if ignore_duplicate_key:
                        message = "regelnr.: %d, Foutmelding %s" % (
                            reader.line_num, ex.message)
                        self.save_action_log(import_run, message)
                    else:
                        logger.error(ex.message)
                        self.save_action_log(import_run, ex.message)
                        break
                except Exception as ex:
                    count_errors += 1
                    logger.error("%s." % ex.message)
                    message = "regelnr.: %d, Foutmelding %s" % (
                        reader.line_num, ex.message)
                    self.save_action_log(import_run, message)
                    break
        is_imported = True
        message = "Aantal rijen %d, waarvan %d toegevoegd, %d geupdated, "\
                  "%d niet toegevoegd/geupdated objecten" % (
                      counter, count_imports, count_updates, count_errors)
        self.save_action_log(import_run, message)
        return is_imported

    def check_xml(self, import_run, datetime_format, ignore_dublicate_key=True):

        filepath = import_run.attachment.path
        activiteit = import_run.activiteit
        counter = 0
        is_valid = True
        umaquo_parser = None
        try:
            umaquo_parser = Parser(filepath)
            umaquo_parser.parse()
        except XMLSyntaxError as ex:
            message = "Foutmeldingen - %s" % ex.message
            self.save_action_log(import_run, message)
            return False

        if umaquo_parser.waardereekstijden <= 0:
            message = "Geen waaardereekstijden gevonden, gezocht met '%s'" % (
                umaquo_parser.WAARDEREEKSTIJD_XPATH
            )
            self.save_action_log(import_run, message)
            is_valid = False
            return is_valid

        for waardereekstijd in umaquo_parser.waardereekstijden.values():
            counter += 1
            tijdserie = umaquo_parser.get_tijdserie(waardereekstijd)
            opname = models.Opname()
            try:
                opname.datum = datetime.strptime(
                    tijdserie[0], '%Y-%m-%d')
                opname.tijd = datetime.strptime(
                    tijdserie[1], '%H:%M:%S')
                opname.waarde_n = tijdserie[2]
                opname.wns = self._get_foreignkey_inst(
                    umaquo_parser.get_wns_oms(waardereekstijd),
                    'WNS',
                    'wns_oms')
                opname.locatie = self._get_foreignkey_inst(
                    umaquo_parser.get_locatie_id(waardereekstijd),
                    'Locatie',
                    'loc_id')
                opname.activiteit = activiteit
                opname.full_clean()
            except ValidationError as e:
                message = "  regelnr.: %d, Foutmeldingen - %s" % (
                    waardereekstijd.sourceline,
                    ", ".join(["%s: %s" % (k, ", ".join(v)) for k, v in e.message_dict.iteritems()])
                )
                self.save_action_log(import_run, message)
                is_valid = False
            except ValueError as e:
                message = "  regelnr.: %d, Foutmeldingen - %s" % (
                    waardereekstijd.sourceline,
                    e.message
                )
                self.save_action_log(import_run, message)
                is_valid = False

        message = "%s %d." % (
            "Aantal rijen",
            counter)
        self.save_action_log(import_run, message)
        return is_valid

    def manual_import_xml(self, import_run, datetime_format, ignore_dublicate_key=True):

        is_imported = False
        filepath = import_run.attachment.path
        activiteit = import_run.activiteit
        created = 0
        umaquo_parser = Parser(filepath)
        umaquo_parser.parse()
        for waardereekstijd in umaquo_parser.waardereekstijden.values():
            tijdserie = umaquo_parser.get_tijdserie(waardereekstijd)
            opname = models.Opname()
            opname.datum = datetime.strptime(
                        tijdserie[0], '%Y-%m-%d')
            opname.tijd = datetime.strptime(
                        tijdserie[1], '%H:%M:%S')
            opname.waarde_n = tijdserie[2]
            opname.wns = self._get_foreignkey_inst(
                umaquo_parser.get_wns_oms(waardereekstijd),
                'WNS',
                'wns_oms')
            opname.locatie = self._get_foreignkey_inst(
                umaquo_parser.get_locatie_id(waardereekstijd),
                'Locatie',
                'loc_id')
            opname.activiteit = activiteit
            try:
                opname.save()
                created += 1
            except IntegrityError as ex:
                if ignore_dublicate_key:
                    if self.log:
                        logger.error(ex.message)
                        self.save_action_log(import_run, ex.message)
                        continue
                    else:
                        logger.error(ex.message)
                        self.save_action_log(import_run, ex.message)
                        break
            except Exception as ex:
                logger.error("%s." % ex.message)
                self.save_action_log(import_run, ex.message)
                break
        is_imported = True
        message = "Created %d objects." % created
        self.save_action_log(import_run, message)
        return is_imported
