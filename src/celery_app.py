from celery import Celery
from config import config

app = Celery(
    'augur',
    broker=config.broker_url,
    backend=config.backend_url,
)

app.conf.update(
    task_serializer='json',
    result_expires=3600,
)

beat_schedule = {}
for integration_id in config.integration_ids:
    beat_schedule[f'sync-{integration_id}'] = {
        'task': 'jobs.tasks.sync_vendor_indicators',
        'schedule': config.sync_interval_seconds,
        'args': (integration_id,),
    }

app.conf.beat_schedule = beat_schedule