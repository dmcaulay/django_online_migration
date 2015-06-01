"Utilities"

import time

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.utils import OperationalError


DEADLOCK_MAX_RETRIES = getattr(settings, 'DEADLOCK_MAX_RETRIES', 3)
DEADLOCK_WAIT_TIMES = getattr(settings, 'DEADLOCK_WAIT_TIMES', [0, 1, 2])
if len(DEADLOCK_WAIT_TIMES) < DEADLOCK_MAX_RETRIES:
    raise ImproperlyConfigured("Invalid deadlock wait times length!")


def retry_on_deadlock(fn):
    "Retry a DB query on a deadlock"
    for attempt in range(DEADLOCK_MAX_RETRIES):
        try:
            fn()
            # succeeded, exit loop
            break
        except OperationalError as e:
            # retry on deadlock error 1213
            if e.args[0] == 1213 and attempt < (DEADLOCK_MAX_RETRIES - 1):
                time.sleep(DEADLOCK_WAIT_TIMES[attempt])
                continue
            # else raise the error
            raise
