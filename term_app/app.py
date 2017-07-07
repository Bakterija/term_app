from kivy_soil.template_app import TemplateApp
from kivy.uix.floatlayout import FloatLayout


class RootWidget(FloatLayout):
    pass


class TermApp(TemplateApp):

    def build(self):
        return RootWidget()


def main_loop():
    app = TermApp()
    app.run()
