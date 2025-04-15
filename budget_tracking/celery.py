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

# Configure periodic tasks
app.conf.beat_schedule = {
    # Send monthly report on the last day of each month at 11:59 PM
    'send-monthly-report': {
        'task': 'budget.tasks.send_monthly_report',
        'schedule': crontab(hour=23, minute=59, day_of_month='28-31'),  # This will run on the last few days of each month
    },
    # Check daily expenses every day at 9:00 PM
    'check-daily-expenses': {
        'task': 'budget.tasks.check_daily_expenses',
        'schedule': crontab(hour=21, minute=0),
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 