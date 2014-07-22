
class TargetLanguage(object):

    _language_short_name = 'unk'

    def get_language_short_name(self):
        return self._language_short_name

    def get_supported_extensions(self):
        return []

    def format_method(self, s):
        return s

    def format_class(self, s):
        return s

    def format_type(self, data_type):
        return str(data_type)

    def format_obj(self, o):
        return str(o)
