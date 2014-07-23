from collections import OrderedDict
import logging
import ply.yacc as yacc

from babelsdk.babel.lexer import BabelLexer

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

    def add_example(self, label, example):
        self.examples[label] = example

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
    def __init__(self, name, data_type_name, data_type_attrs, nullable=False):
        """
        :param data_type_attrs: List of attributes.
        """
        self.name = name
        self.data_type_name = data_type_name
        self.data_type_attrs = data_type_attrs
        self.doc = None
        self.nullable = nullable

    def set_doc(self, docstring):
        self.doc = docstring

    def __repr__(self):
        return 'BabelField({!r}, {!r}, {!r})'.format(
            self.name,
            self.data_type_name,
            self.data_type_attrs,
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

    def p_statement_typedef(self, p):
        'typedef : KEYWORD ID COLON NEWLINE INDENT docsection field_list example_list DEDENT'
        if p[1] not in ('struct', 'union'):
            raise ValueError('Keyword must be struct or union')
        p[0] = BabelTypeDef(p[1], p[2])
        if p[6]:
            p[0].set_doc(self._normalize_docstring(p[6]))
        p[0].set_fields(p[7])
        if p[8]:
            for label, example in p[8]:
                p[0].add_example(label, example)

    def p_statement_typedef_with_inheritance(self, p):
        'typedef : KEYWORD ID KEYWORD ID COLON NEWLINE INDENT docsection field_list example_list DEDENT'
        if p[1] != 'struct':
            raise ValueError('Keyword must be struct')
        elif p[3] != 'extends':
            raise ValueError('Keyword must be extends')
        p[0] = BabelTypeDef(p[1], p[2], extends=p[4])
        if p[8]:
            p[0].set_doc(self._normalize_docstring(p[8]))
        if p[9] is not None:
            p[0].set_fields(p[9])
        if p[10] is not None:
            for label, example in p[10]:
                p[0].add_example(label, example)

    def p_statement_request_section(self, p):
        """reqsection : REQUEST COLON NEWLINE INDENT field_list DEDENT"""
        p[0] = p[5]

    def p_statement_response_section(self, p):
        """respsection : RESPONSE COLON NEWLINE INDENT field_list DEDENT"""
        p[0] = p[5]

    def p_statement_error_section(self, p):
        """errorsection : ERROR COLON NEWLINE INDENT ID NEWLINE DEDENT
                        | empty"""
        if p[1]:
            p[0] = p[5]

    def p_statement_extras_section(self, p):
        """extrassection : EXTRAS COLON NEWLINE INDENT example_field_list DEDENT
                         | empty"""
        if p[1]:
            p[0] = p[5]

    def p_statement_opdef(self, p):
        """opdef : OP ID COLON NEWLINE INDENT docsection reqsection respsection errorsection extrassection DEDENT
                 | OP ID PATH COLON NEWLINE INDENT docsection reqsection respsection errorsection extrassection DEDENT"""
        if p[3] == ':':
            p[0] = BabelOpDef(p[2])
            p[0].set_doc(self._normalize_docstring(p[6]))
            p[0].set_request_segmentation(p[7])
            p[0].set_response_segmentation(p[8])
            if p[9]:
                p[0].set_error_data_type_name(p[9])
            if p[10]:
                p[0].set_extras(dict(p[10]))
        else:
            p[0] = BabelOpDef(p[2], p[3])
            p[0].set_doc(self._normalize_docstring(p[7]))
            p[0].set_request_segmentation(p[8])
            p[0].set_response_segmentation(p[9])
            if p[10]:
                p[0].set_error_data_type_name(p[10])
            if p[11]:
                p[0].set_extras(dict(p[11]))

    def p_statement_add_doc(self, p):
        """docsection : KEYWORD DOUBLE_COLON docstring DEDENT
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

    def p_statement_field(self, p):
        """field : ID ID DOUBLE_COLON docstring DEDENT
                 | ID ID KEYWORD DOUBLE_COLON docstring DEDENT
                 | ID ID LPAR attributes_list RPAR DOUBLE_COLON docstring DEDENT
                 | ID ID LPAR attributes_list RPAR KEYWORD DOUBLE_COLON docstring DEDENT
                 | ID ID NEWLINE
                 | ID ID KEYWORD NEWLINE
                 | ID ID LPAR attributes_list RPAR NEWLINE
                 | ID ID LPAR attributes_list RPAR KEYWORD NEWLINE"""

        p2 = p[:]
        if '\n' in p2[-1]:
            has_docstring = False
            end_index = len(p2) - 1
        else:
            has_docstring = True
            end_index = p2.index('::')

        if end_index == 3:
            p[0] = BabelField(p[1], p[2], [])
        elif end_index == 4:
            if p[3] != 'nullable':
                raise ValueError('Keyword must be "nullable"')
            p[0] = BabelField(p[1], p[2], [], True)
        elif end_index == 6:
            p[0] = BabelField(p[1], p[2], p[4], False)
        elif end_index == 7:
            if p[6] != 'nullable':
                raise ValueError('Keyword must be "nullable"')
            p[0] = BabelField(p[1], p[2], p[4], True)

        if has_docstring:
            p[0].set_doc(self._normalize_docstring(p2[-2]))

    def p_statement_field_symbol(self, p):
        'field : ID DOUBLE_COLON docstring DEDENT'
        p[0] = BabelSymbol(p[1])
        if p[3]:
            p[0].set_doc(self._normalize_docstring(p[3]))

    def p_statement_example(self, p):
        'example : KEYWORD ID COLON NEWLINE INDENT example_field_list DEDENT'
        p[0] = (p[2], p[6])

    def p_statement_example_field_list(self, p):
        'example_field_list : example_field'
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
        p[0] = (p[1], p[3])

    def p_error(self, token):
        self._logger.error('Unexpected %s(%r) at line %d',
                           token.type,
                           token.value,
                           token.lineno)
