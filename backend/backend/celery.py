import os
from celery import Celery
import multiprocessing

# Đặt phương thức khởi tạo là 'spawn'
multiprocessing.set_start_method('spawn', force=True)

# Set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

# Create the Celery app
app = Celery("backend")

# Load config from Django settings, using the CELERY namespace
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

