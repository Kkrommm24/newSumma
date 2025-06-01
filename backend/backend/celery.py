import multiprocessing
import sys  # Thêm sys để kiểm tra platform
import os
from celery import Celery

if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
    try:
        multiprocessing.set_start_method('spawn', force=True)
    except RuntimeError as e:
        # RuntimeError có thể xảy ra nếu context đã được sử dụng hoặc đã set và
        # force=False
        print(
            f"Warning: Could not set multiprocessing start method in celery.py (early): {e}")
# -----------------------------------------------------------------

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
