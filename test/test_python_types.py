import textwrap

from stone.backends.python_types import PythonTypesBackend
from stone.ir import (
    AnnotationType,
    AnnotationTypeParam,
    ApiNamespace,
    ApiRoute,
    CustomAnnotation,
    Int32,
    Nullable,
    Struct,
    StructField,
    Void,
)
from test_python_type_stubs import _make_struct_with_nullable_and_dafault_fields

MYPY = False
if MYPY:
    import typing  # noqa: F401 # pylint: disable=import-error,unused-import,useless-suppression

import unittest

class TestGeneratedPythonTypes(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestGeneratedPythonTypes, self).__init__(*args, **kwargs)

    def _mk_route_schema(self):
        s = Struct('Route', ApiNamespace('stone_cfg'), None)
        s.set_attributes(None, [], None)
        return s

    def _mock_backend(self):
        # type: () -> PythonTypesBackend
        return PythonTypesBackend(
            target_folder_path='output',
            args=['-r', 'dropbox.dropbox.Dropbox.{ns}_{route}'])

    def _evaluate_namespace(self, ns):
        # type: (ApiNamespace) -> typing.Text
        backend = self._mock_backend()
        route_schema = self._mk_route_schema()
        backend._generate_routes(route_schema, ns)
        return backend.output_buffer_to_string()

    def _evaluate_struct(self, ns, struct):
        # type: (ApiNamespace, Struct) -> typing.Text
        backend = self._mock_backend()
        backend._generate_struct_class(ns, struct)
        return backend.output_buffer_to_string()

    def _evaluate_annotation_type(self, ns, annotation_type):
        # type: (ApiNamespace, AnnotationType) -> typing.Text
        backend = self._mock_backend()
        backend._generate_annotation_type_class(ns, annotation_type)
        return backend.output_buffer_to_string()

    def test_route_with_version_number(self):
        # type: () -> None

        route1 = ApiRoute('alpha/get_metadata', 1, None)
        route1.set_attributes(None, None, Void(), Void(), Void(), {})
        route2 = ApiRoute('alpha/get_metadata', 2, None)
        route2.set_attributes(None, None, Void(), Int32(), Void(), {})
        ns = ApiNamespace('files')
        ns.add_route(route1)
        ns.add_route(route2)

        result = self._evaluate_namespace(ns)

        expected = textwrap.dedent("""\
            alpha_get_metadata = bb.Route(
                'alpha/get_metadata',
                1,
                False,
                bv.Void(),
                bv.Void(),
                bv.Void(),
                {},
            )
            alpha_get_metadata_v2 = bb.Route(
                'alpha/get_metadata',
                2,
                False,
                bv.Void(),
                bv.Int32(),
                bv.Void(),
                {},
            )

            ROUTES = {
                'alpha/get_metadata': alpha_get_metadata,
                'alpha/get_metadata:2': alpha_get_metadata_v2,
            }

        """)

        self.assertEqual(result, expected)

    def test_route_with_version_number_name_conflict(self):
        # type: () -> None

        route1 = ApiRoute('alpha/get_metadata', 2, None)
        route1.set_attributes(None, None, Void(), Int32(), Void(), {})
        route2 = ApiRoute('alpha/get_metadata_v2', 1, None)
        route2.set_attributes(None, None, Void(), Void(), Void(), {})
        ns = ApiNamespace('files')
        ns.add_route(route1)
        ns.add_route(route2)

        with self.assertRaises(RuntimeError) as cm:
            self._evaluate_namespace(ns)
        self.assertEqual(
            'There is a name conflict between {!r} and {!r}'.format(route1, route2),
            str(cm.exception))

    def test_struct_with_custom_annotations(self):
        # type: () -> None
        ns = ApiNamespace('files')
        annotation_type = AnnotationType('MyAnnotationType', ns, None, [
            AnnotationTypeParam('test_param', Int32(), None, False, None, None)
        ])
        ns.add_annotation_type(annotation_type)
        annotation = CustomAnnotation('MyAnnotation', ns, None, 'MyAnnotationType',
            None, [], {'test_param': 42})
        annotation.set_attributes(annotation_type)
        ns.add_annotation(annotation)
        struct = Struct('MyStruct', ns, None)
        struct.set_attributes(None, [
            StructField('annotated_field', Int32(), None, None),
            StructField('unannotated_field', Int32(), None, None),
        ])
        struct.fields[0].set_annotations([annotation])

        result = self._evaluate_struct(ns, struct)

        expected = textwrap.dedent('''\
            class MyStruct(bb.Struct):

                __slots__ = [
                    '_annotated_field_value',
                    '_annotated_field_present',
                    '_unannotated_field_value',
                    '_unannotated_field_present',
                ]

                _has_required_fields = True

                def __init__(self,
                             annotated_field,
                             unannotated_field):
                    self._annotated_field_value = None
                    self._annotated_field_present = False
                    self._unannotated_field_value = None
                    self._unannotated_field_present = False
                    if annotated_field is not None:
                        self.annotated_field = annotated_field
                    if unannotated_field is not None:
                        self.unannotated_field = unannotated_field

                @property
                def annotated_field(self):
                    """
                    :rtype: int
                    """
                    if self._annotated_field_present:
                        return self._annotated_field_value
                    else:
                        raise AttributeError("missing required field 'annotated_field'")

                @annotated_field.setter
                def annotated_field(self, val):
                    val = self._annotated_field_validator.validate(val)
                    self._annotated_field_value = val
                    self._annotated_field_present = True

                @annotated_field.deleter
                def annotated_field(self):
                    self._annotated_field_value = None
                    self._annotated_field_present = False

                @property
                def unannotated_field(self):
                    """
                    :rtype: int
                    """
                    if self._unannotated_field_present:
                        return self._unannotated_field_value
                    else:
                        raise AttributeError("missing required field 'unannotated_field'")

                @unannotated_field.setter
                def unannotated_field(self, val):
                    val = self._unannotated_field_validator.validate(val)
                    self._unannotated_field_value = val
                    self._unannotated_field_present = True

                @unannotated_field.deleter
                def unannotated_field(self):
                    self._unannotated_field_value = None
                    self._unannotated_field_present = False

                def _process_custom_annotations(self, annotation_type, field_path, processor):
                    super(MyStruct, self)._process_custom_annotations(annotation_type, field_path, processor)

                    if annotation_type is MyAnnotationType:
                        self.annotated_field = bb.partially_apply(processor, MyAnnotationType(test_param=42))('{}.annotated_field'.format(field_path), self.annotated_field)

                def __repr__(self):
                    return 'MyStruct(annotated_field={!r}, unannotated_field={!r})'.format(
                        self._annotated_field_value,
                        self._unannotated_field_value,
                    )

            MyStruct_validator = bv.Struct(MyStruct)

        ''') # noqa
        self.maxDiff = None
        self.assertEqual(result, expected)

    def test_annotation_type_class(self):
        # type: () -> None
        ns = ApiNamespace('files')
        annotation_type = AnnotationType('MyAnnotationType', ns, "documented", [
            AnnotationTypeParam(
                'test_param',
                Int32(),
                "test parameter",
                False,
                None,
                None,
            ),
            AnnotationTypeParam(
                'test_default_param',
                Int32(),
                None,
                True,
                5,
                None,
            ),
        ])
        result = self._evaluate_annotation_type(ns, annotation_type)
        expected = textwrap.dedent('''\
            class MyAnnotationType(bb.AnnotationType):
                """
                documented

                :ivar test_param: test parameter
                """

                __slots__ = [
                    '_test_param',
                    '_test_default_param',
                ]

                def __init__(self,
                             test_param=None,
                             test_default_param=5):
                    self._test_param = test_param
                    self._test_default_param = test_default_param

                @property
                def test_param(self):
                    """
                    test parameter

                    :rtype: int
                    """
                    return self._test_param

                @property
                def test_default_param(self):
                    """
                    :rtype: int
                    """
                    return self._test_default_param


        ''')
        self.assertEqual(result, expected)

    # TODO: add more unit tests for client code generation

    def test_annotation_type_class(self):
        ns = ApiNamespace('Foo')
        struct = _make_struct_with_nullable_and_dafault_fields(ns)
        result = self._evaluate_struct(ns, struct)
        expected = textwrap.dedent('''\
                class Struct1(bb.Struct):

                    __slots__ = [
                        '_nullable_field_value',
                        '_nullable_field_present',
                        '_default_field_value',
                        '_default_field_present',
                        '_non_nullable_field_value',
                        '_non_nullable_field_present',
                    ]

                    _has_required_fields = True

                    def __init__(self,
                                 non_nullable_field,
                                 nullable_field=None,
                                 default_field=3.14159265359):
                        self._nullable_field_value = None
                        self._nullable_field_present = False
                        self._default_field_value = None
                        self._default_field_present = False
                        self._non_nullable_field_value = None
                        self._non_nullable_field_present = False
                        if nullable_field is not None:
                            self.nullable_field = nullable_field
                        if default_field is not None:
                            self.default_field = default_field
                        if non_nullable_field is not None:
                            self.non_nullable_field = non_nullable_field

                    @property
                    def nullable_field(self):
                        """
                        :rtype: int
                        """
                        if self._nullable_field_present:
                            return self._nullable_field_value
                        else:
                            return None

                    @nullable_field.setter
                    def nullable_field(self, val):
                        if val is None:
                            del self.nullable_field
                            return
                        val = self._nullable_field_validator.validate(val)
                        self._nullable_field_value = val
                        self._nullable_field_present = True

                    @nullable_field.deleter
                    def nullable_field(self):
                        self._nullable_field_value = None
                        self._nullable_field_present = False

                    @property
                    def default_field(self):
                        """
                        :rtype: float
                        """
                        if self._default_field_present:
                            return self._default_field_value
                        else:
                            return 3.14159265359

                    @default_field.setter
                    def default_field(self, val):
                        val = self._default_field_validator.validate(val)
                        self._default_field_value = val
                        self._default_field_present = True

                    @default_field.deleter
                    def default_field(self):
                        self._default_field_value = None
                        self._default_field_present = False

                    @property
                    def non_nullable_field(self):
                        """
                        :rtype: int
                        """
                        if self._non_nullable_field_present:
                            return self._non_nullable_field_value
                        else:
                            raise AttributeError("missing required field 'non_nullable_field'")

                    @non_nullable_field.setter
                    def non_nullable_field(self, val):
                        val = self._non_nullable_field_validator.validate(val)
                        self._non_nullable_field_value = val
                        self._non_nullable_field_present = True

                    @non_nullable_field.deleter
                    def non_nullable_field(self):
                        self._non_nullable_field_value = None
                        self._non_nullable_field_present = False

                    def _process_custom_annotations(self, annotation_type, field_path, processor):
                        super(Struct1, self)._process_custom_annotations(annotation_type, field_path, processor)

                    def __repr__(self):
                        return 'Struct1(non_nullable_field={!r}, nullable_field={!r}, default_field={!r})'.format(
                            self._non_nullable_field_value,
                            self._nullable_field_value,
                            self._default_field_value,
                        )

                Struct1_validator = bv.Struct(Struct1)

        ''')
        self.assertEqual(expected, result)
