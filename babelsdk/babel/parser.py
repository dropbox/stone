from collections import OrderedDict
import logging
import ply.yacc as yacc

from babelsdk.babel.lexer import BabelLexer, BabelNull

class BabelOpDef(object):
    def __init__(self, name, path=None):
        self.name = name
        self.path = path
        self.request_segmentation = []
        self.response_segmentation = []
        self.error_data_type_name = None
        self.extras = {}
    def set_doc(self, docstring):
        self.doc = docstring
    def set_request_segmentation(self, segments):
        self.request_segmentation = segments
    def set_response_segmentation(self, segments):
        self.response_segmentation = segments
    def set_error_data_type_name(self, data_type_name):
        self.error_data_type_name = data_type_name
    def set_extras(self, extras):
        self.extras = extras

class BabelTypeDef(object):
    def __init__(self, composite_type, name, extends=None):
        self.composite_type = composite_type
        self.name = name
        self.extends = extends
        self.doc = None
        self.fields = []
        self.examples = OrderedDict()

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
                 nullable,
                 optional,
                 deprecated):
        """
        :param data_type_attrs: List of attributes.
        """
        self.name = name
        self.data_type_name = data_type_name
        self.data_type_attrs = data_type_attrs
        self.doc = None
        self.nullable = nullable
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
        self._logger = logging.getLogger('babelsdk.babel.parser')

    def parse(self, data):
        return self.yacc.parse(data.lstrip(), lexer=self.lexer, debug=self.debug)

    def test_lexing(self, data):
        self.lexer.test(data.lstrip())

    def p_statement_decl_to_desc(self, p):
        """desc : decl
                | typedef
                | opdef"""
        p[0] = [p[1]]

    def p_statement_desc_iter(self, p):
        """desc : desc decl
                | desc typedef
                | desc opdef"""
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

    def p_statement_typedef_struct(self, p):
        'typedef : STRUCT ID inheritance NEWLINE INDENT docsection field_list example_list DEDENT'
        p[0] = BabelTypeDef(p[1], p[2], extends=p[3])
        if p[6]:
            p[0].set_doc(self._normalize_docstring(p[6]))
        if p[7] is not None:
            p[0].set_fields(p[7])
        if p[8] is not None:
            for label, text, example in p[8]:
                p[0].add_example(label, text, example)

    def p_segment(self, p):
        """segment : ID ID NEWLINE
                   | ID NEWLINE"""
        if p[2].strip() == '':
            p[0] = BabelSegment(p[1], None)
        else:
            p[0] = BabelSegment(p[2], p[1])

    def p_segment_list_create(self, p):
        """segment_list : segment
                        | empty"""
        if p[1] is not None:
            p[0] = [p[1]]

    def p_segment_list_extend(self, p):
        'segment_list : segment_list segment'
        p[0] = p[1]
        p[0].append(p[2])

    def p_statement_request_section(self, p):
        """reqsection : REQUEST NEWLINE INDENT segment_list DEDENT"""
        p[0] = p[4]

    def p_statement_response_section(self, p):
        """respsection : RESPONSE NEWLINE INDENT segment_list DEDENT"""
        p[0] = p[4]

    def p_statement_error_section(self, p):
        """errorsection : ERROR NEWLINE INDENT ID NEWLINE DEDENT
                        | empty"""
        if p[1]:
            p[0] = p[4]

    def p_statement_extras_section(self, p):
        """extrassection : EXTRAS NEWLINE INDENT example_field_list DEDENT
                         | empty"""
        if p[1]:
            p[0] = p[4]

    def p_path(self, p):
        """path_option : PATH
                       | empty"""
        p[0] = p[1]

    def p_statement_opdef(self, p):
        'opdef : OP ID path_option NEWLINE INDENT docsection reqsection respsection errorsection extrassection DEDENT'
        p[0] = BabelOpDef(p[2], p[3])
        p[0].set_doc(self._normalize_docstring(p[6]))
        p[0].set_request_segmentation(p[7])
        p[0].set_response_segmentation(p[8])
        if p[9]:
            p[0].set_error_data_type_name(p[9])
        if p[10]:
            p[0].set_extras(dict(p[10]))

    def p_statement_add_doc(self, p):
        """docsection : KEYWORD COLON docstring DEDENT
                      | empty"""
        if p[1]:
            if p[1] != 'doc':
                raise Exception('Wrong keyword in doc section...')
            # Convert a lone newline to a space, and two consecutive newlines
            # to a single newline.
            p[0] = p[3]

    def _normalize_docstring(self, docstring):
        """We convert double newlines to single newlines, and single newlines
        to a single whitespace."""
        lines = docstring.strip().split('\n\n')
        return '\n'.join([line.replace('\n', ' ') for line in lines]).strip()

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

    def p_field_nullable(self, p):
        """nullable : PIPE NULL
                    | empty"""
        p[0] = p[1] is not None

    def p_field_presence(self, p):
        """presence : REQUIRED
                    | OPTIONAL
                    | empty"""
        if bool(p[1]):
            p[0] = (p[1] == 'optional')
        else:
            p[0] = False

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
        """field : ID ID attributes_group nullable default_option presence deprecation COLON docstring DEDENT
                 | ID ID attributes_group nullable default_option presence deprecation NEWLINE"""
        has_docstring = (p[8] == ':')
        p[0] = BabelField(p[1], p[2], p[3], p[4], p[6], p[7])
        if p[5] is not None:
            if p[5] is BabelNull:
                p[0].set_default(None)
            else:
                p[0].set_default(p[5])
        if has_docstring:
            p[0].set_doc(self._normalize_docstring(p[9]))

    def p_statement_field_symbol(self, p):
        'field : ID COLON docstring DEDENT'
        p[0] = BabelSymbol(p[1])
        if p[3]:
            p[0].set_doc(self._normalize_docstring(p[3]))

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
