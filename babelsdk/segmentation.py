"""
Note that BabelSDK has no understanding of how a segment of Struct, Union,
or Binary data type is serialized on the wire. Likewise, a full segmentation
description does not have any defacto RPC format.
"""

from babelsdk.data_type import (
    Binary,
    Struct,
    Union,
)

class Segment(object):
    """
    One segment of a segmentation.
    """
    def __init__(self, name, data_type):
        """
        Creates a new Segment.
        :param str name: The name of the segment.
        :param DataType data_type: The data type of the segment. Must be either
            a Struct, Union, or Binary binary type..
        """
        if not isinstance(data_type, (Binary, Struct, Union)):
            raise TypeError('Segment must be either a struct, union, or '
                            'binary -- not %r' % data_type)
        self.name = name
        self.data_type = data_type
    def __repr__(self):
        return 'Segment({!r}, {!r})'.format(self.name, self.data_type)

class SegmentList(Segment):
    """
    Represents a segment in a segmentation that is a list of segments.
    """
    list = True
    def __repr__(self):
        return 'SegmentList({!r}, {!r})'.format(self.name, self.data_type)

class Segmentation(object):
    """
    High-level representation of the body of an HTTP Request or Response.
    """
    def __init__(self, segments):
        """
        Creates a new Segmentation.
        :param list(Segment) segments: Format of body.
        """
        if not segments:
            raise ValueError('At least one segment must be specified.')
        self.segments = segments
        self.segments_by_name = {}
        for segment in segments:
            self.segments_by_name[segment.name] = segment
    def __repr__(self):
        return 'Segmentation({!r})'.format(self.segments)
