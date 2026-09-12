"""Dedicated background worker entrypoint.
Run separately from the API in production: python -m app.worker
"""
import logging, time
from .services.event_handlers import register_event_handlers
from .services.event_worker import process_domain_events
from .core.scheduler import start_scheduler

logging.basicConfig(level=logging.INFO)
register_event_handlers()
# In a dedicated worker process, scheduler owns event delivery + scheduled jobs.
scheduler = start_scheduler()
try:
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    scheduler.shutdown(wait=False)
