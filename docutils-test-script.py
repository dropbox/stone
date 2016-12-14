import docutils
print(docutils.__version__)

from docutils.parsers.rst import Parser
from docutils import frontend
parser = Parser()
settings = frontend.OptionParser(components=(Parser,)).get_default_values()
import pprint
pprint.pprint(settings.__dict__)
