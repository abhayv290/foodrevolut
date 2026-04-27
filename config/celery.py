import os 
from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.local')

app = Celery('foodRevolut')
app.config_from_object('django.conf.settings',namespace='CELERY')

#auto discover tasks in all installed apps 
#looks  for tasks.py  in each app 
app.autodiscover_tasks()