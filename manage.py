#!/usr/bin/env python
import os
import sys
import signal
import threading

def handleKill(signum, frame):
    print("Killing Thread.")
    # Or whatever code you want here
    # ForceTerminate.FORCE_TERMINATE = True
    print(threading.active_count())
    exit(0)


if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crawlSpider.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    signal.signal(signal.SIGINT, handleKill)
    signal.signal(signal.SIGTERM, handleKill)
    execute_from_command_line(sys.argv)

