from ._base import FunctionBase

class Function(FunctionBase):
    name = 'functions'
    doc = 'Reuturns list of all loaded plugin functions'
    methods_subclass = {}

    def handle_input(self, term_system, term_globals, exec_locals, text):
        fname, method, args = self.get_method_args(text)

        ret = list(term_system.functions)

        return ret
