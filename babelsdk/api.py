from collections import OrderedDict
from distutils.version import StrictVersion

class Api(object):
    """
    A full description of an API's namespaces, data types, and operations.
    """
    def __init__(self, version):
        self.version = StrictVersion(version)
        self.namespaces = OrderedDict()

    def ensure_namespace(self, name):
        """
        Only creates a namespace if it hasn't yet been defined.

        :param str name: Name of the namespace.

        :return ApiNamespace:
        """
        if name not in self.namespaces:
            self.namespaces[name] = ApiNamespace(name)
        return self.namespaces.get(name)

class ApiNamespace(object):
    """
    Represents a category of API endpoints and their associated data types.
    """

    def __init__(self, name):
        self.name = name
        self.operations = []
        self.operation_by_name = {}
        self.data_types = []
        self.data_type_by_name = {}
    def add_operation(self, operation):
        self.operations.append(operation)
        self.operation_by_name[operation.name] = operation
    def add_data_type(self, data_type):
        self.data_types.append(data_type)
        self.data_type_by_name[data_type.name] = data_type

class ApiOperation(object):
    """
    Represents an API endpoint.
    """

    def __init__(self,
                 name,
                 path,
                 doc,
                 request_segmentation,
                 response_segmentation,
                 error_data_type,
                 extras):
        """
        :param str name: Friendly name of the endpoint.
        :param str path: Request path.
        :param str doc: Description of the endpoint.
        :param Segmentation request_segmentation: The segmentation of the
            request.
        :param Segmentation segmentation: The segmentation of the response.
        :param DataType error_data_type: The data type that represents
            possible errors.
        """

        self.name = name
        self.path = path
        self.doc = doc
        self.request_segmentation = request_segmentation
        self.response_segmentation = response_segmentation
        self.error_data_type = error_data_type
        self.extras = extras

