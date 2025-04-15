from celery import shared_task
from .email_services import send_monthly_report, check_high_value_transactions
from django.contrib.auth import get_user_model
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

@shared_task(bind=True, max_retries=3)
def send_monthly_report_task(self):
    """
    Celery task to send monthly expense report to all users
    """
    try:
        users = User.objects.filter(is_active=True)
        success_count = 0
        error_count = 0
        
        for user in users:
            try:
                send_monthly_report(user)
                success_count += 1
                logger.info(f"Monthly report sent successfully to user {user.username}")
            except Exception as e:
                error_count += 1
                logger.error(f"Failed to send monthly report to user {user.username}: {str(e)}")
        
        logger.info(f"Monthly report task completed. Success: {success_count}, Errors: {error_count}")
        
    except Exception as exc:
        logger.error(f"Monthly report task failed: {str(exc)}")
        self.retry(exc=exc, countdown=300)  # Retry after 5 minutes

@shared_task(bind=True, max_retries=3)
def check_high_value_transactions_task(self):
    """
    Celery task to check for high-value transactions and send alerts
    """
    try:
        users = User.objects.filter(is_active=True)
        success_count = 0
        error_count = 0
        
        for user in users:
            try:
                check_high_value_transactions(user)
                success_count += 1
                logger.info(f"High value transaction check completed for user {user.username}")
            except Exception as e:
                error_count += 1
                logger.error(f"Failed to check high value transactions for user {user.username}: {str(e)}")
        
        logger.info(f"High value transaction check completed. Success: {success_count}, Errors: {error_count}")
        
    except Exception as exc:
        logger.error(f"High value transaction check failed: {str(exc)}")
        self.retry(exc=exc, countdown=300)  # Retry after 5 minutes 