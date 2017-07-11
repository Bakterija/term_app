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
from .flask_client import RemoteClient
import traceback
import os
try:
    from queue import Queue, Empty
except:
    from Queue import Queue, Empty


class Function(FunctionBase):
    name = 'remote_control'
    doc = 'Allows to control and be controlled by other terminal widgets'
    server = None
    client_instance = None
    methods_subclass = {
        'flask_server': '',
        'client': ''
    }

    def on_import(self, term_system):
        self.term_system = term_system

    def client(self, task, ip_addr, **kwargs):
        ret = ''
        if task == 'connect':
            self.client_instance = RemoteClient(self)
            self.client_instance.bind(on_disconnect=self.on_client_disconnect)
            self.client_instance.bind(on_new_data=self.on_client_new_data)
            self.client_instance.bind(on_send_fail=self.on_client_send_fail)
            self.client_instance.bind(
                on_connect_success=self.on_client_connect_success)
            self.client_instance.bind(
                on_connect_fail=self.on_client_connect_fail)

            passwd = kwargs.get('passwd', None)
            port = ip_addr.split(':')
            if len(port) > 1:
                ret = self.client_instance.connect(
                    ip_addr, passwd=passwd, port=port[1])
            else:
                ret = self.client_instance.connect(ip_addr, passwd=passwd)

        elif task == 'disconect':
            if self.client_instance:
                ret = self.client_instance.disconect()
            else:
                ret = '# Client is not connected'
            if self.term_system.grab_input == self:
                self.term_system.grab_input = None
        return ret

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
        ret = ''
        if self.client_instance:
            ret = self.client_instance.send(text)
        else:
            ret = super(Function, self).handle_input(
                term_system, term_globals, exec_locals, text)
        return ret

    def on_client_connect_success(self, cl):
        self.term_system.grab_input = self
        self.term_system.add_text(
            '# %s: successfully connected' % cl.__class__.__name__)

    def on_client_connect_fail(self, cl):
        self.term_system.add_text(
            '# %s: failed to connect' % cl.__class__.__name__)

    def on_client_disconnect(self, _):
        if self.term_system.grab_input == self:
            self.term_system.grab_input = self
        self.term_system.add_text(
            '# %s: disconnected' % cl.__class__.__name__)

    def on_client_send_fail(self, _):
        self.term_system.add_text(
            '# %s: failed to send input' % cl.__class__.__name__)

    def on_client_new_data(self, _, data):
        self.term_system.add_text(
            data['text_raw'], text_time=data['time'], level=data['level'])
