from collections import OrderedDict
import logging
import ply.yacc as yacc

from babelapi.babel.lexer import BabelLexer, BabelNull

class BabelRouteDef(object):
    def __init__(self, name):
        self.name = name
        self.request_data_type_name = None
        self.response_data_type_name = None
        self.error_data_type_name = None
        self.attrs = {}
    def set_doc(self, docstring):
        self.doc = docstring
    def set_request_data_type_name(self, data_type_name):
        self.request_data_type_name = data_type_name
    def set_response_data_type_name(self, data_type_name):
        self.response_data_type_name = data_type_name
    def set_error_data_type_name(self, data_type_name):
        self.error_data_type_name = data_type_name
    def set_attrs(self, attrs):
        self.attrs = attrs

class BabelTypeDef(object):
    def __init__(self, composite_type, name, extends=None, coverage=None):
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

class BabelSymbol(object):
    def __init__(self, name):
        self.name = name
        self.doc = None
    def set_doc(self, docstring):
        self.doc = docstring
    def __str__(self):
        return self.__repr__()
    def __repr__(self):
        return 'BabelSymbol({!r})'.format(
            self.name,
        )

class BabelNamespace(object):
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return self.__repr__()
    def __repr__(self):
        return 'BabelNamespace({!r})'.format(
            self.name,
        )

class BabelInclude(object):
    def __init__(self, target):
        self.target = target
    def __str__(self):
        return self.__repr__()
    def __repr__(self):
        return 'BabelInclude({!r})'.format(
            self.target,
        )

class BabelAlias(object):
    def __init__(self, name, data_type_name, data_type_attrs):
        """
        :param data_type_attrs: List of attributes.
        """
        self.name = name
        self.data_type_name = data_type_name
        self.data_type_attrs = data_type_attrs

    def __repr__(self):
        return 'BabelAlias({!r}, {!r}, {!r})'.format(
            self.name,
            self.data_type_name,
            self.data_type_attrs,
        )

class BabelField(object):
    def __init__(self,
                 name,
                 data_type_name,
                 data_type_attrs,
                 optional,
                 deprecated):
        """
        :param data_type_attrs: List of attributes.
        """
        self.name = name
        self.data_type_name = data_type_name
        self.data_type_attrs = data_type_attrs
        self.doc = None
        self.has_default = False
        self.default = None
        self.optional = optional
        self.deprecated = deprecated

    def set_doc(self, docstring):
        self.doc = docstring

    def set_default(self, default):
        self.has_default = True
        self.default = default

    def __repr__(self):
        return 'BabelField({!r}, {!r}, {!r})'.format(
            self.name,
            self.data_type_name,
            self.data_type_attrs,
        )

class BabelSymbolField(object):
    def __init__(self, name, catch_all):
        self.name = name
        self.catch_all = catch_all
        self.doc = None
    def set_doc(self, docstring):
        self.doc = docstring
    def __str__(self):
        return self.__repr__()
    def __repr__(self):
        return 'BabelSymbolField({!r}, {!r})'.format(
            self.name,
            self.catch_all,
        )

class BabelSegment(object):
    def __init__(self, data_type_name, name):
        self.data_type_name = data_type_name
        self.name = name
    def __repr__(self):
        return 'BabelSegment({!r}, {!r})'.format(
            self.data_type_name,
            self.name,
        )

class BabelParser(object):
    """
    Due to how ply.yacc works, the docstring of each parser method is a BNF
    rule. Comments that would normally be docstrings for each parser rule
    method are kept before the method definition.
    """

    # Ply parser requiment: Tokens must be re-specified in parser
    tokens = BabelLexer.tokens

    # Ply feature: Starting grammar rule
    start = 'desc'

    def __init__(self, debug=False):
        self.debug = debug
        self.yacc = yacc.yacc(module=self, debug=self.debug, write_tables=self.debug)
        self.lexer = BabelLexer()
        self._logger = logging.getLogger('babelapi.babel.parser')

    def parse(self, data):
        return self.yacc.parse(data.lstrip(), lexer=self.lexer, debug=self.debug)

    def test_lexing(self, data):
        self.lexer.test(data.lstrip())

    def p_statement_decl_to_desc(self, p):
        """desc : decl
                | typedef
                | routedef"""
        p[0] = [p[1]]

    def p_statement_desc_iter(self, p):
        """desc : desc decl
                | desc typedef
                | desc routedef"""
        p[0] = p[1]
        p[0].append(p[2])

    # This covers the case where we have garbage characters in a file that
    # splits a NEWLINE token into two separate tokens.
    def p_statement_desc_ignore_newline(self, p):
        'desc : desc NEWLINE'
        p[0] = p[1]

    def p_statement_decl(self, p):
        'decl : KEYWORD ID NEWLINE'
        if p[1] == 'namespace':
            p[0] = BabelNamespace(p[2])
        else:
            raise ValueError('Expected namespace keyword')

    def p_statement_include(self, p):
        'decl : INCLUDE ID NEWLINE'
        p[0] = BabelInclude(p[2])

    def p_statement_alias(self, p):
        """decl : KEYWORD ID EQ ID NEWLINE
                | KEYWORD ID EQ ID LPAR attributes_list RPAR NEWLINE"""
        if p[1] == 'alias':
            if len(p) > 6:
                alias = BabelAlias(p[2], p[4], p[6])
            else:
                alias = BabelAlias(p[2], p[4], [])
            p[0] = alias
        else:
            raise ValueError('Expected alias keyword')

    def p_statement_attribute_single(self, p):
        """attribute : ID"""
        p[0] = (p[1], True)

    def p_statement_attribute_kv(self, p):
        """attribute : ID EQ INTEGER
                     | ID EQ FLOAT
                     | ID EQ STRING
                     | ID EQ BOOLEAN"""
        p[0] = (p[1], p[3])

    def p_statement_attribute_kv_symbol(self, p):
        'attribute : ID EQ ID'
        p[0] = (p[1], BabelSymbol(p[3]))

    def p_statement_attributes_list_create(self, p):
        """attributes_list : attribute"""
        p[0] = [p[1]]

    def p_statement_attributes_list_extend(self, p):
        """attributes_list : attributes_list COMMA attribute"""
        p[0] = p[1]
        p[0].append(p[3])

    def p_statement_attributes_group(self, p):
        """attributes_group : LPAR attributes_list RPAR
                            | empty"""
        if p[1] is not None:
            p[0] = p[2]
        else:
            p[0] = []

    def p_statement_typedef_union(self, p):
        'typedef : UNION ID NEWLINE INDENT docsection field_list example_list DEDENT'
        p[0] = BabelTypeDef(p[1], p[2])
        if p[5]:
            p[0].set_doc(self._normalize_docstring(p[5]))
        if p[6] is not None:
            p[0].set_fields(p[6])
        if p[7]:
            for label, text, example in p[7]:
                p[0].add_example(label, text, example)

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

    def p_statement_typedef_struct(self, p):
        'typedef : STRUCT ID inheritance coverage NEWLINE INDENT docsection field_list example_list DEDENT'
        p[0] = BabelTypeDef(p[1], p[2], extends=p[3], coverage=p[4])
        if p[7]:
            p[0].set_doc(self._normalize_docstring(p[7]))
        if p[8] is not None:
            p[0].set_fields(p[8])
        if p[9] is not None:
            for label, text, example in p[9]:
                p[0].add_example(label, text, example)

    def p_statement_attrs_section(self, p):
        """attrssection : ATTRS NEWLINE INDENT example_field_list DEDENT
                         | empty"""
        if p[1]:
            p[0] = p[4]

    def p_route_name_path_suffix(self, p):
        """route_path : PATH
                      | empty"""
        p[0] = p[1]

    def p_statement_routedef(self, p):
        """routedef : ROUTE ID route_path attributes_group NEWLINE INDENT docsection attrssection DEDENT"""
        if p[3]:
            p[2] += p[3]
        p[0] = BabelRouteDef(p[2])
        p[0].set_doc(self._normalize_docstring(p[7]))
        data_types = p[4]
        if len(data_types) == 2:
            request, response = data_types
            error = (None, None)
        elif len(data_types) == 3:
            request, response, error = data_types
        else:
            raise ValueError('Incorrect number of arguments to route %d' % len(data_types))
        p[0].set_request_data_type_name(request[0])
        p[0].set_response_data_type_name(response[0])
        p[0].set_error_data_type_name(error[0])
        if p[8]:
            p[0].set_attrs(dict(p[8]))

    def p_statement_add_doc(self, p):
        """docsection : KEYWORD COLON docstring DEDENT
                      | docstring NEWLINE
                      | empty"""
        if p[1]:
            if p[2] == ':':
                if p[1] != 'doc':
                    raise Exception('Wrong keyword in doc section...')
                else:
                    # Convert a lone newline to a space, and two consecutive newlines
                    # to a single newline.
                    p[0] = p[3]
            else:
                p[0] = p[1]

    def _normalize_docstring(self, docstring):
        """We convert double newlines to single newlines, and single newlines
        to a single whitespace."""
        lines = docstring.strip().split('\n\n')
        return '\n'.join([line.replace('\n', ' ') for line in lines]).strip()

    def p_docstring_string(self, p):
        'docstring : STRING'
        lines = p[1].strip().split('\n\n')
        p[0] = '\n'.join([line.replace('\n' + ' ' * self.lexer.cur_indent, ' ')
                          for line in lines]).strip()

    def p_statement_docstring_create(self, p):
        'docstring : LINE'
        p[0] = p[1]

    def p_statement_docstring_extend(self, p):
        'docstring : docstring LINE'
        p[0] = p[1] + p[2]

    def p_field_list_create(self, p):
        """field_list : field
                      | empty"""
        if p[1] is not None:
            p[0] = [p[1]]

    def p_field_list_extend(self, p):
        'field_list : field_list field'
        p[0] = p[1]
        p[0].append(p[2])

    def p_field_optional(self, p):
        """optional : Q
                    | empty"""
        p[0] = p[1] == '?'

    def p_field_deprecation(self, p):
        """deprecation : DEPRECATED
                       | empty"""
        p[0] = (p[1] == 'deprecated')

    def p_eq_primitive(self, p):
        """eq_primitive : EQ INTEGER
                        | EQ FLOAT
                        | EQ STRING
                        | EQ BOOLEAN
                        | EQ NULL"""
        p[0] = p[2]

    def p_default_option(self, p):
        """default_option : eq_primitive
                          | empty"""
        p[0] = p[1]

    def p_statement_field(self, p):
        """field : ID ID attributes_group optional default_option deprecation NEWLINE INDENT docstring NEWLINE DEDENT
                 | ID ID attributes_group optional default_option deprecation NEWLINE"""
        has_docstring = len(p) > 9
        p[0] = BabelField(p[1], p[2], p[3], p[4], p[6])
        if p[5] is not None:
            if p[5] is BabelNull:
                p[0].set_default(None)
            else:
                p[0].set_default(p[5])
        elif has_docstring:
            p[0].set_doc(p[9])

    def p_asterix_option(self, p):
        """asterix_option : ASTERIX
                          | empty"""
        p[0] = (p[1] is not None)

    def p_statement_field_symbol(self, p):
        """field : ID asterix_option NEWLINE
                 | ID asterix_option NEWLINE INDENT docstring NEWLINE DEDENT"""
        p[0] = BabelSymbolField(p[1], p[2])
        if len(p) > 4:
            p[0].set_doc(p[5])

    def p_statement_example(self, p):
        """example : KEYWORD ID STRING NEWLINE INDENT example_field_list DEDENT
                   | KEYWORD ID empty NEWLINE INDENT example_field_list DEDENT"""
        p[0] = (p[2], p[3], p[6])

    def p_statement_example_field_list(self, p):
        """example_field_list : example_field
                              | PASS NEWLINE"""
        if p[1] == 'pass':
            p[0] = []
        else:
            p[0] = [p[1]]

    def p_statement_example_field_list_2(self, p):
        'example_field_list : example_field_list example_field'
        p[0] = p[1]
        p[0].append(p[2])

    def p_empty(self, p):
        'empty :'
        pass

    def p_statement_example_create(self, p):
        """example_list : example
                        | empty"""
        if p[1] is not None:
            p[0] = [p[1]]

    def p_statement_example_list_extend(self, p):
        'example_list : example_list example'
        p[0] = p[1]
        p[0].append(p[2])

    def p_statement_example_field(self, p):
        """example_field : ID EQ INTEGER NEWLINE
                         | ID EQ FLOAT NEWLINE
                         | ID EQ STRING NEWLINE
                         | ID EQ BOOLEAN NEWLINE
                         | ID EQ NULL NEWLINE"""
        if p[3] is BabelNull:
            p[0] = (p[1], None)
        else:
            p[0] = (p[1], p[3])

    def p_error(self, token):
        self._logger.error('Unexpected %s(%r) at line %d',
                           token.type,
                           token.value,
                           token.lineno)
