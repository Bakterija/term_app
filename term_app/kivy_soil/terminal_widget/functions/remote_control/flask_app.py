from kivy_soil.utils import get_unicode
from flask import Flask, request
from kivy.logger import Logger
from kivy.clock import Clock
from threading import Thread
from gevent import pywsgi
from time import sleep
import traceback
import urllib2
import copy
import json
import os
try:
    from queue import Queue, Empty
except:
    from Queue import Queue, Empty

app = Flask(__name__)
log_level = 'error'
app_data = {}

class AppController:
    _instance = None

    class GeventLoggerInfo:
        @staticmethod
        def write(msg):
            global log_level
            if log_level == 'info':
                msg = get_unicode(msg)
                Logger.info('Gevent: %s' % (msg))

    class GeventLoggerError:
        @staticmethod
        def write(msg):
            global log_level
            if log_level in ('info', 'error'):
                msg = get_unicode(msg)
                Logger.error('Gevent: %s' % (msg))

    class _AppController:
        started = False
        log_append_queue = Queue()
        thread = None

        def __init__(self, remote_control):
            self.parent = remote_control
            tsys = remote_control.term_system
            app_data['logs'] = copy.copy(tsys.data)
            tsys.bind(on_data_append=self.on_data_append)

        def on_data_append(self, _, value):
            self.log_append_queue.put(value)

        def start(self, crt_path=None, key_path=None, log_lvl='error'):
            global log_level
            if not self.started:
                log_level = log_lvl
                if not crt_path and not key_path:
                    crt_path = 'data/term.crt'
                    key_path = 'data/term.key'
                self.thread = Thread(target=self._run_app, kwargs={
                    'crt_path': crt_path, 'key_path': key_path})
                self.thread.daemon = True
                self.thread.start()

        def _run_app(self, crt_path=None, key_path=None):
            Logger.info('AppController: _run_app:')
            try:
                gevent_kwargs = {
                    'log': AppController.GeventLoggerInfo,
                    'error_log': AppController.GeventLoggerError}

                if crt_path and key_path:
                    found_ssl = True
                    for x in (crt_path, key_path):
                        if not os.path.exists(x):
                            found_ssl = False
                    if found_ssl:
                        gevent_kwargs['certfile'] = crt_path
                        gevent_kwargs['keyfile'] = key_path
                    else:
                        Logger.warning('AppController: _run_app: cert and key '
                                       'were not found, starting without')
                self.server = pywsgi.WSGIServer(
                    ('0.0.0.0', 5000), app, **gevent_kwargs)
                self.started = True
                self.server.serve_forever()
            except:
                Logger.error('AppController: %s' % traceback.format_exc())

        def _stop_app(self):
            if self.started:
                self.server.stop()
                Logger.info('AppController: stopped gevent')
                self.started = False

        def update(self):
            try:
                while True:
                    data = self.log_append_queue.get_nowait()
                    if data:
                        app_data['logs'].append(copy.copy(data))
            except Empty:
                return

        @app.route('/')
        def index():
            return 'Nothing here'

        @app.route('/get_logs_all')
        def get_logs_all():
            AppController.instance.update()
            return json.dumps(app_data['logs'])

        @app.route('/get_logs/<int:start>:<int:end>')
        def get_log_sliced(start, end):
            AppController.instance.update()
            ret = app_data['logs'][start:end]
            return json.dumps(ret)

        @app.route('/get_logs_after/<int:index>')
        def get_log_after_index(index):
            AppController.instance.update()
            ret = app_data['logs'][index:]
            return json.dumps(ret)

        @app.route('/get_log_len')
        def get_log_len():
            AppController.instance.update()
            rett = len(app_data['logs']) - 1
            return str(rett)

        @app.route('/handle_input', methods=['POST'])
        def handle_input():
            json_dict = request.get_json()
            AppController.instance.parent.term_system.handle_input(
                json_dict[u'data'])
            return str(json_dict[u'data'])

        @app.route('/stop')
        def stop_app():
            AppController.instance._stop_app()
            return 'App is stopping'

    instance = None

    def __init__(self, remote_control):
        if not AppController.instance:
            AppController.instance = AppController._AppController(
                remote_control)

    def __getattr__(self, name):
        return getattr(self.instance, name)
