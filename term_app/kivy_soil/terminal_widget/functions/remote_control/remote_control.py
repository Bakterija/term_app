from kivy.properties import NumericProperty, StringProperty, ObjectProperty
from kivy_soil.terminal_widget.functions._base import FunctionBase
from kivy_soil.terminal_widget import shared_globals
from kivy.properties import ListProperty
from kivy.logger import Logger
from kivy.clock import Clock
from threading import Thread
from time import sleep
from functools import partial
from .flask_app import AppController
import traceback
import json
import urllib2
import os
try:
    from queue import Queue, Empty
except:
    from Queue import Queue, Empty


class Function(FunctionBase):
    name = 'remote_control'
    doc = 'Allows to control and be controlled by other terminal widgets'
    server = None
    client_addr = ''
    client_data_index = -1
    methods_subclass = {
        'flask_server': '',
        'client': ''
    }

    def on_import(self, term_system):
        self.term_system = term_system

    def client(self, task, *args):
        if task == 'connect':
            if self.client_addr:
                ret = '# Already connected'
            else:
                ip_addr = args[0]
                self.client_addr = ip_addr
                url = 'http://%s:5000/get_log_len' % (ip_addr)
                self.term_system.add_text('# Connecting to %s' % (url))
                req = urllib2.Request(url)
                self.client_data_index = int(urllib2.urlopen(req).read())
                Clock.schedule_interval(self.client_update, 0.4)
                self.term_system.grab_input = self
                ret = '# Connected, %s' % (self.client_data_index)
        elif task == 'disconect':
            if self.client_addr:
                Clock.unschedule(self.client_update)
                self.client_addr = ''
                if self.term_system.grab_input == self:
                    self.term_system.grab_input = None
                ret = '# Disconnected'
            else:
                ret = '# Client is not connected'
        return ret

    def _client_send(self, text):
        url = 'http://%s:5000/handle_input' % (self.client_addr)
        headers = {'Content-Type' : 'application/json'}
        data = json.dumps({'data': text})
        req = urllib2.Request(url, data, headers)
        response = urllib2.urlopen(req)
        return response

    def client_update(self, dt):
        url = 'http://%s:5000/get_logs_after/%s' % (
            self.client_addr, self.client_data_index)
        response = urllib2.urlopen(url).read()
        if response:
            response = json.loads(response)
            for x in response:
                self.client_data_index += 1
                x['text_raw'] = 'remote: %s' % (x['text_raw'])
                self.term_system.add_text(
                    x['text_raw'], text_time=x['time'], level=x['level'])

    def flask_server(self, *args):
        if args[0] == 'start':
            if self.server:
                ret = '# Server already started'
            else:
                self.server = AppController(self)
                self.server.start()
                ret = '# Started server'
        return ret

    def handle_input(self, term_system, term_globals, exec_locals, text):
        if self.client_addr:
            self._client_send(text)
        else:
            return super(Function, self).handle_input(
                term_system, term_globals, exec_locals, text)
