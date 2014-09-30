
class TargetLanguage(object):

    _language_short_name = 'unk'

    def get_language_short_name(self):
        return self._language_short_name

    def get_supported_extensions(self):
        raise NotImplemented

    def format_method(self, words):
        raise NotImplemented

    def format_class(self, words):
        raise NotImplemented

    def format_variable(self, words):
        raise NotImplemented

    def format_type(self, data_type):
        raise NotImplemented

    def format_string_value(self, s):
        if s == 'true':
            return self.format_obj(True)
        elif s == 'false':
            return self.format_obj(False)
        elif s == 'null':
            return self.format_obj(None)
        else:
            return self.format_obj(eval(s))

    def format_obj(self, o):
        """The representation of an object in the target language. For example,
        it may convert a None to null for certain languages."""
        raise NotImplemented

    def format_func_call_args(self, values):
        return ', '.join([self.format_obj(value) for value in values])