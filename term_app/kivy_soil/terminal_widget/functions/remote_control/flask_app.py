from threading import Thread
from kivy.clock import Clock
from flask import Flask, request
from time import sleep
import copy
import json
try:
    from queue import Queue, Empty
except:
    from Queue import Queue, Empty

app = Flask(__name__)
app_data = {}


class AppController:
    _instance = None

    class _AppController(object):
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

        def start(self):
            if not self.started:
                self.thread = Thread(target=self.run_app)
                self.thread.daemon = True
                self.thread.start()
                self.started = True

        def run_app(self):
            app.run(host='0.0.0.0')

        def stop(self):
            if self.started:
                app.stop()

        def update(self):
            try:
                while True:
                    data = self.log_append_queue.get_nowait()
                    if data:
                        app_data['logs'].append(copy.copy(data))
            except Empty:
                return

        @app.route('/get_logs_all')
        def index():
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

    instance = None

    def __init__(self, remote_control):
        if not AppController.instance:
            AppController.instance = AppController._AppController(
                remote_control)

    def __getattr__(self, name):
        return getattr(self.instance, name)
