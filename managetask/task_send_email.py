from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_task_notification(email, task_name, status):
    subject = f'Tarea {task_name} {status}'
    message = f'La tarea "{task_name}" fue {status} exitosamente.'
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])