# djangotasks/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Establece el módulo de configuración de Django para Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangotasks.settings')

app = Celery('djangotasks')

# Lee la configuración desde el archivo de configuración de Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Descubre y carga las tareas de todos los módulos de aplicaciones de Django
app.autodiscover_tasks()