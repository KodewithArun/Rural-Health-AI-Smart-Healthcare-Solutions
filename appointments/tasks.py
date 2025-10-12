from celery import shared_task
from .views import auto_cancel_no_show_appointments

@shared_task
def auto_cancel_appointments():
    count = auto_cancel_no_show_appointments()
    return f"Cancelled {count} appointments"
