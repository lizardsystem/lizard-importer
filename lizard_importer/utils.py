import celery

from django.db import models as django_models


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


def fk_models():
    fk_models = []
    related_models = {}

    for m in django_models.get_models():        
        if m._meta.app_label in EXCLUDED_APPS:
            continue
        for rel_field in m._meta.get_all_related_objects():
            model_full_name = '%s.%s' % (
                rel_field.model._meta.app_label, rel_field.model._meta.model_name)
            related_models[model_full_name] = None
    return related_models.keys()


def fk_model_choices():
    return [(key, key) for key in fk_models()]


def add_text_to_top(dest_text, text):
    """Add text on top, the dest_text contains lines"""
    if dest_text is None:
        dest_text = ''
    if text is None:
        text = ''
    lines = dest_text.split('\n')
    lines.insert(0, text)
    return '\n'.join(lines)

