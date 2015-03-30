from __future__ import absolute_import, division, print_function, unicode_literals

from collections import OrderedDict
import logging

import ply.yacc as yacc

from babelapi.babel.lexer import BabelLexer, BabelNull

class _Element(object):
    def __init__(self, lineno, lexpos):
        self.lineno = lineno
        self.lexpos = lexpos

class BabelNamespace(_Element):
    def __init__(self, lineno, lexpos, name):
        """
        Args:
            name (str): The namespace of the spec.
        """
        super(BabelNamespace, self).__init__(lineno, lexpos)
        self.name = name

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return 'BabelNamespace({!r})'.format(self.name)

class BabelInclude(_Element):
    def __init__(self, lineno, lexpos, target):
        """
        Args:
            target (str): The filename of the header file.
        """
        super(BabelInclude, self).__init__(lineno, lexpos)
        self.target = target

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return 'BabelInclude({!r})'.format(self.target)

class BabelAlias(_Element):
    def __init__(self, lineno, lexpos, name, type_ref):
        """
        Args:
            name (str): The name of the alias.
            type_ref (BabelTypeRef): The data type of the field.
        """
        super(BabelAlias, self).__init__(lineno, lexpos)
        self.name = name
        self.type_ref = type_ref

    def __repr__(self):
        return 'BabelAlias({!r}, {!r})'.format(self.name, self.type_ref)

class BabelTypeDef(_Element):
    def __init__(self, lineno, lexpos, composite_type, name, extends=None,
                 coverage=None):
        super(BabelTypeDef, self).__init__(lineno, lexpos)
        self.composite_type = composite_type
        self.name = name
        self.extends = extends
        self.doc = None
        self.fields = []
        self.examples = OrderedDict()
        self.coverage = coverage

    def set_doc(self, docstring):
        self.doc = docstring

    def set_fields(self, fields):
        self.fields = fields

    def add_example(self, label, text, example):
        self.examples[label] = (text, example)

    def __str__(self):
        return self.__repr__()
    def __repr__(self):
        return 'BabelType({!r}, {!r}, {!r})'.format(
            self.composite_type,
            self.name,
            self.fields,
        )

class BabelTypeRef(_Element):
    def __init__(self, lineno, lexpos, name, args, nullable):
        """
        Args:
            name (str): Name of the referenced type.
            args (tuple[list, dict]): Arguments to type.
            nullable (bool): Whether the type is nullable (can be null)
        """
        super(BabelTypeRef, self).__init__(lineno, lexpos)
        self.name = name
        self.args = args
        self.nullable = nullable

    def __repr__(self):
        return 'BabelTypeRef({!r}, {!r})'.format(
            self.name,
            self.args,
            self.nullable,
        )

class BabelTagRef(_Element):
    def __init__(self, lineno, lexpos, tag, union_name=None):
        """
        Args:
            tag (str): Name of the referenced type.
            union_name (str): The name of the union the tag belongs to.
        """
        super(BabelTagRef, self).__init__(lineno, lexpos)
        self.tag = tag
        self.union_name = union_name

    def __repr__(self):
        return 'BabelTagRef({!r}, {!r})'.format(
            self.tag,
            self.union_name,
        )

class BabelField(_Element):
    """
    Represents both a field of a struct and a field of a union.
    TODO(kelkabany): Split this into two different classes.
    """
    def __init__(self, lineno, lexpos, name, type_ref, deprecated):
        """
        Args:
            name (str): The name of the field.
            type_ref (BabelTypeRef): The data type of the field.
            deprecated (bool): Whether the field is deprecated.
        """
        super(BabelField, self).__init__(lineno, lexpos)
        self.name = name
        self.type_ref = type_ref
        self.doc = None
        self.has_default = False
        self.default = None
        self.deprecated = deprecated

    def set_doc(self, docstring):
        self.doc = docstring

    def set_default(self, default):
        self.has_default = True
        self.default = default

    def __repr__(self):
        return 'BabelField({!r}, {!r})'.format(
            self.name,
            self.type_ref,
        )

class BabelVoidField(_Element):
    def __init__(self, lineno, lexpos, name, catch_all):
        super(BabelVoidField, self).__init__(lineno, lexpos)
        self.name = name
        self.catch_all = catch_all
        self.doc = None
    def set_doc(self, docstring):
        self.doc = docstring
    def __str__(self):
        return self.__repr__()
    def __repr__(self):
        return 'BabelVoidField({!r}, {!r})'.format(
            self.name,
            self.catch_all,
        )

class BabelRouteDef(_Element):
    def __init__(self, lineno, lexpos, name, request_type_ref,
                 response_type_ref, error_type_ref=None):
        super(BabelRouteDef, self).__init__(lineno, lexpos)
        self.name = name
        self.request_type_ref = request_type_ref
        self.response_type_ref = response_type_ref
        self.error_type_ref = error_type_ref
        self.doc = None
        self.attrs = {}

    def set_doc(self, docstring):
        self.doc = docstring

    def set_attrs(self, attrs):
        self.attrs = attrs


class BabelParser(object):
    """
    Due to how ply.yacc works, the docstring of each parser method is a BNF
    rule. Comments that would normally be docstrings for each parser rule
    method are kept before the method definition.
    """

    # Ply parser requiment: Tokens must be re-specified in parser
    tokens = BabelLexer.tokens

    # Ply feature: Starting grammar rule
    start = str('spec')  # PLY wants a 'str' instance; this makes it work in Python 2 and 3

    def __init__(self, debug=False):
        self.debug = debug
        self.yacc = yacc.yacc(module=self, debug=self.debug, write_tables=self.debug)
        self.lexer = BabelLexer()
        self._logger = logging.getLogger('babelapi.babel.parser')
        # [(token type, token value, line number), ...]
        self.errors = []

    def parse(self, data):
        return self.yacc.parse(data, lexer=self.lexer, debug=self.debug)

    def test_lexing(self, data):
        self.lexer.test(data)

    def got_errors_parsing(self):
        """Whether the lexer or parser had errors."""
        return self.errors or self.lexer.errors

    def get_error_strings(self):
        """Call this if got_errors_parsing() returns True to get a list of
        error strings."""
        errors = []
        for char, lineno in self.lexer.errors:
            errors.append('Line %d: Illegal character %r' % (lineno, char))
        for token_type, token_value, lineno, msg in self.errors:
            if msg is None:
                errors.append('Line %d: Unexpected %s with value %r' %
                                  (lineno, token_type, token_value))
            else:
                errors.append(msg)
        return errors

    # --------------------------------------------------------------
    # Spec := Namespace Include* Definition*

    def p_spec_init(self, p):
        """spec : NEWLINE
                | empty"""
        p[0] = []

    def p_spec_init_decl(self, p):
        """spec : namespace
                | include
                | definition"""
        p[0] = [p[1]]

    def p_spec_iter(self, p):
        """spec : spec namespace
                | spec include
                | spec definition"""
        p[0] = p[1]
        p[0].append(p[2])

    # This covers the case where we have garbage characters in a file that
    # splits a NEWLINE token into two separate tokens.
    def p_spec_ignore_newline(self, p):
        'spec : spec NEWLINE'
        p[0] = p[1]

    def p_definition(self, p):
        """definition : alias
                      | struct
                      | union
                      | route"""
        p[0] = p[1]

    def p_namespace(self, p):
        'namespace : KEYWORD ID NEWLINE'
        if p[1] == 'namespace':
            p[0] = BabelNamespace(p.lineno(1), p.lexpos(1), p[2])
        else:
            raise ValueError('Expected namespace keyword')

    def p_include(self, p):
        'include : INCLUDE ID NEWLINE'
        p[0] = BabelInclude(p.lineno(1), p.lexpos(1), p[2])

    def p_alias(self, p):
        'alias : KEYWORD ID EQ type_ref NEWLINE'
        if p[1] == 'alias':
            p[0] = BabelAlias(p.lineno(1), p.lexpos(1), p[2], p[4])
        else:
            raise ValueError('Expected alias keyword')

    # --------------------------------------------------------------
    # Primitive Types

    def p_primitive(self, p):
        """primitive : BOOLEAN
                     | FLOAT
                     | INTEGER
                     | NULL
                     | STRING"""
        p[0] = p[1]

    # --------------------------------------------------------------
    # References to Types
    #
    # There are several places references to types are made:
    # 1. Alias targets
    #    alias x = TypeRef
    # 2. Field data types
    #    struct S
    #        f TypeRef
    # 3. In arguments to type references
    #    struct S
    #        f TypeRef(key=TypeRef)
    #
    # A type reference can have positional and keyword arguments:
    #     TypeRef(value1, ..., kwarg1=kwvalue1)
    # If it has no arguments, the parentheses can be omitted.
    #
    # If a type reference has a '?' suffix, it is a nullable type.

    def p_pos_arg(self, p):
        """pos_arg : primitive
                   | type_ref"""
        p[0] = p[1]

    def p_pos_args_list_create(self, p):
        """pos_args_list : pos_arg"""
        p[0] = [p[1]]

    def p_pos_args_list_extend(self, p):
        """pos_args_list : pos_args_list COMMA pos_arg"""
        p[0] = p[1]
        p[0].append(p[3])

    def p_kw_arg(self, p):
        """kw_arg : ID EQ primitive
                  | ID EQ type_ref"""
        p[0] = {p[1]: p[3]}

    def p_kw_args(self, p):
        """kw_args : kw_arg"""
        p[0] = p[1]

    def p_kw_args_update(self, p):
        """kw_args : kw_args COMMA kw_arg"""
        p[0] = p[1]
        for key in p[3]:
            if key in p[1]:
                msg = 'Line %d: Keyword argument %r defined more than once.' % (
                    p.lineno(3), key)
                self.errors.append(('kw_arg', key, p.lineno(3), msg))
        p[0].update(p[3])

    def p_args(self, p):
        """args : LPAR pos_args_list COMMA kw_args RPAR
                | LPAR pos_args_list RPAR
                | LPAR kw_args RPAR
                | LPAR RPAR
                | empty"""
        if len(p) > 3:
            if p[3] == ',':
                p[0] = (p[2], p[4])
            elif isinstance(p[2], dict):
                p[0] = ([], p[2])
            else:
                p[0] = (p[2], {})
        else:
            p[0] = ([], {})

    def p_field_nullable(self, p):
        """nullable : Q
                    | empty"""
        p[0] = p[1] == '?'

    def p_type_ref(self, p):
        'type_ref : ID args nullable'
        p[0] = BabelTypeRef(p.lineno(1), p.lexpos(1), p[1], p[2], p[3])

    def p_tag_ref(self, p):
        """tag_ref : ID DOT ID
                   | ID"""
        if len(p) > 2:
            p[0] = BabelTagRef(p.lineno(1), p.lexpos(1), p[3], p[1])
        else:
            p[0] = BabelTagRef(p.lineno(1), p.lexpos(1), p[1])

    # --------------------------------------------------------------
    # Structs
    #
    # An example struct looks as follows:
    #
    # struct S extends P
    #     "This is a docstring for the struct"
    #
    #     typed_field String
    #         "This is a docstring for the field"

    def p_inheritance(self, p):
        """inheritance : EXTENDS ID
                       | empty"""
        if p[1]:
            p[0] = p[2]

    def p_coverage_list_create(self, p):
        'coverage_list : ID'
        p[0] = [p[1]]

    def p_coverage_list_extend(self, p):
        'coverage_list : coverage_list PIPE ID'
        p[0] = p[1]
        p[0].append(p[3])

    def p_coverage(self, p):
        """coverage : OF coverage_list
                    | empty"""
        if p[1]:
            p[0] = p[2]

    def p_struct(self, p):
        """
        struct : STRUCT ID inheritance coverage NEWLINE \
                     INDENT docsection field_list example_list DEDENT
        """
        p[0] = BabelTypeDef(p.lineno(1), p.lexpos(1), p[1], p[2], extends=p[3], coverage=p[4])
        if p[7]:
            p[0].set_doc(p[7])
        if p[8] is not None:
            p[0].set_fields(p[8])
        if p[9] is not None:
            for label, text, example in p[9]:
                p[0].add_example(label, text, example)

    # --------------------------------------------------------------
    # Fields
    #
    # Each struct has zero or more fields. A field has a name, type,
    # and docstring. The "deprecated" keyword is currently unused.
    #
    # TODO(kelkabany): Split fields into struct fields and union fields
    # since they differ in capabilities rather significantly now.

    def p_field_list_create(self, p):
        """field_list : field
                      | empty"""
        if p[1] is not None:
            p[0] = [p[1]]

    def p_field_list_extend(self, p):
        'field_list : field_list field'
        p[0] = p[1]
        p[0].append(p[2])

    def p_field_deprecation(self, p):
        """deprecation : DEPRECATED
                       | empty"""
        p[0] = (p[1] == 'deprecated')

    def p_default_option(self, p):
        """default_option : EQ primitive
                          | EQ tag_ref
                          | empty"""
        if p[1]:
            if isinstance(p[2], BabelTagRef):
                p[0] = p[2]
            else:
                p[0] = p[2]

    def p_field(self, p):
        """field : ID type_ref default_option deprecation NEWLINE INDENT docstring NEWLINE DEDENT
                 | ID type_ref default_option deprecation NEWLINE"""
        has_docstring = len(p) > 6
        p[0] = BabelField(p.lineno(1), p.lexpos(1), p[1], p[2], p[4])
        if p[3] is not None:
            if p[3] is BabelNull:
                p[0].set_default(None)
            else:
                p[0].set_default(p[3])
        if has_docstring:
            p[0].set_doc(p[7])

    # --------------------------------------------------------------
    # Unions
    #
    # An example union looks as follows:
    #
    # union U
    #     "This is a docstring for the union"
    #
    #     void_field*
    #         "Docstring for field with type Void"
    #     typed_field String
    #
    # void_field demonstrates the notation for a catch all variant.

    def p_union(self, p):
        'union : UNION ID inheritance NEWLINE INDENT docsection field_list example_list DEDENT'
        p[0] = BabelTypeDef(p.lineno(1), p.lexpos(1), p[1], p[2], extends=p[3])
        if p[6]:
            p[0].set_doc(p[6])
        if p[7] is not None:
            p[0].set_fields(p[7])
        if p[8]:
            for label, text, example in p[8]:
                p[0].add_example(label, text, example)

    def p_asterix_option(self, p):
        """asterix_option : ASTERIX
                          | empty"""
        p[0] = (p[1] is not None)

    def p_field_void(self, p):
        """field : ID asterix_option NEWLINE
                 | ID asterix_option NEWLINE INDENT docstring NEWLINE DEDENT"""
        p[0] = BabelVoidField(p.lineno(1), p.lexpos(1), p[1], p[2])
        if len(p) > 4:
            p[0].set_doc(p[5])

    # --------------------------------------------------------------
    # Routes
    #
    # An example route looks as follows:
    #
    # route sample-route/sub-path (request, response, error)
    #     "This is a docstring for the route"
    #
    #     attrs
    #         key="value"
    #
    # The error type is optional.

    def p_route_path_suffix(self, p):
        """route_path : PATH
                      | empty"""
        p[0] = p[1]

    def p_route_io(self, p):
        """route_io : LPAR type_ref COMMA type_ref RPAR
                    | LPAR type_ref COMMA type_ref COMMA type_ref RPAR"""
        if len(p) > 6:
            p[0] = (p[2], p[4], p[6])
        else:
            p[0] = (p[2], p[4], None)

    def p_route(self, p):
        """route : ROUTE ID route_path route_io NEWLINE INDENT docsection attrssection DEDENT
                 | ROUTE ID route_path route_io NEWLINE"""
        if p[3]:
            p[2] += p[3]
        p[0] = BabelRouteDef(p.lineno(1), p.lexpos(1), p[2], *p[4])
        if len(p) > 6:
            p[0].set_doc(p[7])
            if p[8]:
                p[0].set_attrs(dict(p[8]))

    def p_attrs_section(self, p):
        """attrssection : ATTRS NEWLINE INDENT example_field_list DEDENT
                         | empty"""
        if p[1]:
            p[0] = p[4]

    # --------------------------------------------------------------
    # Doc sections
    #
    # Doc sections appear after struct, union, and route signatures;
    # also after field declarations.
    #
    # They're represented by text (multi-line supported) enclosed by
    # quotations.
    #
    # struct S
    #     "This is a docstring
    #     for struct S"
    #
    #     number Int64
    #         "This is a docstring for this field"

    def p_docsection(self, p):
        """docsection : docstring NEWLINE
                      | empty"""
        if p[1]:
            p[0] = p[1]

    def p_docstring_string(self, p):
        'docstring : STRING'
        # Remove trailing whitespace on every line.
        p[0] = '\n'.join([line.rstrip() for line in p[1].split('\n')])

    # --------------------------------------------------------------
    # Examples
    #
    # Examples appear at the bottom of struct definitions to give
    # illustrative examples of what struct values may look like.
    #
    # struct S
    #     number Int64
    #
    #     example default "This is a label"
    #         number=42

    def p_example(self, p):
        """example : KEYWORD ID STRING NEWLINE INDENT example_field_list DEDENT
                   | KEYWORD ID empty NEWLINE INDENT example_field_list DEDENT"""
        p[0] = (p[2], p[3], p[6])

    def p_example_field_list(self, p):
        """example_field_list : example_field
                              | PASS NEWLINE"""
        if p[1] == 'pass':
            p[0] = []
        else:
            p[0] = [p[1]]

    def p_example_field_list_2(self, p):
        'example_field_list : example_field_list example_field'
        p[0] = p[1]
        p[0].append(p[2])

    def p_example_create(self, p):
        """example_list : example
                        | empty"""
        if p[1] is not None:
            p[0] = [p[1]]

    def p_example_list_extend(self, p):
        'example_list : example_list example'
        p[0] = p[1]
        p[0].append(p[2])

    def p_example_field(self, p):
        'example_field : ID EQ primitive NEWLINE'
        if p[3] is BabelNull:
            p[0] = (p[1], None)
        else:
            p[0] = (p[1], p[3])

    # --------------------------------------------------------------

    # In ply, this is how you define an empty rule. This is used when we want
    # the parser to treat a rule as optional.
    def p_empty(self, p):
        'empty :'
        pass

    # Called by the parser whenever a token doesn't match any rule.
    def p_error(self, token):
        assert token is not None, "Unknown error, please report this."
        self._logger.debug('Unexpected %s(%r) at line %d',
                           token.type,
                           token.value,
                           token.lineno)
        self.errors.append((token.type, token.value, token.lineno, None))
