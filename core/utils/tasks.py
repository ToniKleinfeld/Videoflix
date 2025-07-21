from django.db import transaction
import django_rq
from rq import Retry

DEFAULT_RETRY = Retry(max=3, interval=[10, 30, 60])  # Retry nach 10s, 30s, 60s


def enqueue_after_commit(task, *args, retry=DEFAULT_RETRY, **kwargs):
    """
    Queue einen Task nach erfolgreichem DB-Commit, mit automatischem Retry.
    """
    transaction.on_commit(lambda: django_rq.enqueue(task, *args, retry=retry, **kwargs))
