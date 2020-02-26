from __future__ import absolute_import

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
# from  import app as celery_app
from .app import app as celery_aspp

__all__ = ['celery_app']
import pymysql
pymysql.install_as_MySQLdb()