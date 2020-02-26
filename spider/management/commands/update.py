# coding:utf-8
from django.core.management.base import BaseCommand
from django.conf import settings
import os
import sys
from contextlib import contextmanager
from datetime import datetime
import logging
import requests
import traceback
import json

handler = logging.handlers.RotatingFileHandler("log/tasks.log", maxBytes=100 * 1024 * 1024, backupCount=5)
fmt = '%(asctime)s - %(name)s - %(message)s'
formatter = logging.Formatter(fmt)
handler.setFormatter(formatter)
logger = logging.getLogger('TASK')
logger.addHandler(handler)
logger.setLevel(logging.INFO)

command_path = os.path.join(settings.BASE_DIR, 'spider')


class Command(BaseCommand):
    help = '更新爬虫Cookie组件'

    def add_arguments(self, parser):
        parser.add_argument('method_name', nargs="*", type=str)
        parser.add_argument('method_args', nargs="*", type=str)
        parser.add_argument(
            '-user',
            '--user',
            action='store',
            dest='user',
            default='Spider',
            help='角色',
        )

    @contextmanager
    def factory_error_handler(self, command_name, method_name, method_args):
        task_type = 'collect/pol/%s/%s/%s' % (command_name, method_name, method_args[0])
        try:
            logger.info(json.dumps({'task_type': task_type, 'log_type': 'Notice', 'log_name': 'task_begin',
                                    'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}))
            yield
            logger.info(json.dumps({'task_type': task_type, 'log_type': 'Notice', 'log_name': 'task_end',
                                    'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}))
        except requests.RequestException as  err:
            tb = traceback.format_exc()
            print(tb)
            logger.info(json.dumps(
                {'task_type': task_type, 'log_type': 'Fatal', 'err_title': 'Network error', 'err_stack': tb,
                 'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}))
        except SystemExit as err:
            import sys
            sys.exit(0)
        except Exception as err:
            tb = traceback.format_exc()
            print(tb)
            logger.info(json.dumps(
                {'task_type': task_type, 'log_type': 'Error', 'err_title': err.__class__.__name__, 'err_stack': tb,
                 'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}))

    def handle(self, *args, **options):
        command_name = sys.argv[1]
        method_name = options['method_name'][0]
        name = "spider.tasklibs." + method_name
        mod = __import__(name, fromlist=['*'])
        method_args = options['method_args']
        if command_name == 'update':
            with self.factory_error_handler(command_name, method_name, ['']):
                mod.update(*args, **options)
        else:
            print('right command?')
