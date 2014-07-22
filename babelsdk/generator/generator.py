import logging

class Generator(object):
    def __init__(self, api):
        self.api = api
        self._logger = logging.getLogger('bablesdk.generator.%s'
                                         % self.__class__.__name__)

    def render(self, extension, text):
        raise NotImplemented