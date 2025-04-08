import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'budget_tracking.settings')

app = Celery('budget_tracking')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Configure Celery Beat schedule
app.conf.beat_schedule = {
    'send-budget-alerts': {
        'task': 'budget.tasks.send_budget_alerts',
        'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
    },
    'generate-monthly-reports': {
        'task': 'budget.tasks.generate_monthly_reports',
        'schedule': crontab(0, 0, day_of_month='1'),  # First day of each month
    },
    'cleanup-old-data': {
        'task': 'budget.tasks.cleanup_old_data',
        'schedule': crontab(hour=0, minute=0, day_of_week='sunday'),  # Weekly cleanup
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 