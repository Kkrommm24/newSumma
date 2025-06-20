#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import multiprocessing as mp


def main():
    """Run administrative tasks."""
    if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
        try:
            mp.set_start_method('spawn', force=True)
        except RuntimeError as e:
            print(
                f"Warning: Could not set multiprocessing start method in manage.py: {e}")
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
