from __future__ import absolute_import

import logging
import os

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def add(x, y):
    return x + y
