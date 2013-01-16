'''
PHP code parser

Functions for tokenizing and parsing PHP source code using a command line PHP.

Copyright 2012 John Watson <https://github.com/jotson>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

import os
import re
import json
import subprocess
import tempfile


_constants = {}


def get_all_token_names():
    '''
    Gets names for all token constants.

    The token constants (http://us2.php.net/manual/en/tokens.php) values
    aren't consistent between different versions of PHP. The values are
    automatically generated based on PHP's underlying parser infrastructure.
    This code generates a dictionary of token constants from the installed
    version of PHP. The dictionary is later used to convert the token codes
    returned by PHP's token_get_all() into names.
    '''
    global _constants
    _constants[0] = None
    php = ''
    for i in range(0, 999):
        php += "echo '{code},'.token_name({code}).'|';".format(code=i)
    result = subprocess.Popen(['php', '-r', php], bufsize=1, stdout=subprocess.PIPE, shell=False).communicate()[0]
    for constant in result.split('|'):
        if constant.find(',') >= 0:
            code, name = constant.split(',')
            if name != 'UNKNOWN':
                _constants[str(code)] = name


def get_token_name(code):
    '''
    Get name for a given token code.
    '''
    name = None
    code = str(code)
    if code in _constants:
        name = _constants[code]
    return name


def token(token):
    '''
    Parse the raw token data into a more consistent form.
    '''
    if type(token).__name__ == 'list':
        kind = get_token_name(token[0])
        stmt = token[1]
        line = token[2]
    else:
        kind = get_token_name(0)
        stmt = token
        line = 0

    return kind, stmt, line


def get_all_tokens(source=None, filename=None):
    '''
    Returns all of the tokens for a given snippet of code or source file.
    '''
    tmp = None
    if source:
        '''Write source to a temp file'''
        tmp, filename = tempfile.mkstemp()
        with os.fdopen(tmp, "wb") as f:
            f.write(source.encode('utf-8'))
    php = "echo json_encode(token_get_all(file_get_contents('{source}')));".format(source=filename)
    tokens = subprocess.Popen(['php', '-r', php], bufsize=1, stdout=subprocess.PIPE, shell=False).communicate()[0]
    tokens = json.loads(tokens)
    for i in range(0, len(tokens)):
        tokens[i] = token(tokens[i])

    if source and tmp:
        os.unlink(filename)

    return tokens


def get_context(source, point):
    '''
    Given a snippet of code, return a list of tokens for the classes and
    functions within the last statement. For example, given code:

        ...
        $class->setAlpha($a)->
        ...

    Return an array:

        ['$class', 'setAlpha']

    Steps:
        - Replace all factory regexs in the source defined in the settings.
        - Read the list backwards until we get to an enclosing block or the previous statement.
        - Create the context from that point and forward.
    '''

    source = source[:point]

    visibility = None
    context = []
    operator = None
    tokens = get_all_tokens(source)
    tokens.reverse()
    nest = 0
    end = 0
    for t in tokens:
        kind, stmt, line = t
        # print kind, stmt, line
        if kind == 'T_DOUBLE_COLON' and visibility is None:
            visibility = 'public'
        if kind == 'T_DOUBLE_COLON' and operator is None:
            operator = '::'
        if kind == 'T_OBJECT_OPERATOR' and operator is None:
            operator = '->'
        if len(context) == 0 and (kind == 'T_DOUBLE_COLON' or kind == 'T_OBJECT_OPERATOR'):
            context.append('')
        if kind is None and stmt == '(':
            nest += 1
        if kind is None and stmt == ')':
            nest -= 1
        if kind is None and stmt == '=':
            break
        if kind == 'T_CONCAT_EQUAL':
            break
        if kind == 'T_PLUS_EQUAL':
            break
        if kind is None and stmt == ';':
            break
        if kind is None and stmt == '.':
            break
        if kind is None and stmt == ',':
            break
        if kind is None and (stmt == '{' or stmt == '}'):
            break
        if kind == 'T_OPEN_TAG':
            break
        if kind == 'T_NEW':
            break
        if nest == 0 and kind == 'T_VARIABLE':
            context.append(stmt)
            if stmt == '$this' and visibility is None:
                visibility = 'all'
            if visibility is None:
                visibility = 'public'
        if nest == 0 and kind == 'T_STRING':
            context.append(stmt)
            if visibility is None:
                visibility = 'public'
        if nest > 0:
            break

        end += 1

    context.reverse()

    if context and context[0].startswith('$'):
        class_name = None
        if context[0].startswith('$this'):
            tokens = convert_raw_tokens(get_all_tokens(source))
            class_name = tokens[0]['class'] if tokens else None
        else:
            searchtext = context[0].replace('$', '\$')
            searchtext = searchtext.replace('(', '\(')
            searchtext = searchtext.replace(')', '\)')
            searchtext += '\s+(.*?)[\s|$]'
            t = re.findall('@var\s+' + searchtext, source)
            if t:
                class_name = t[0]
        if class_name:
            context[0] = class_name

    return context, visibility, operator


def convert_raw_tokens(raw_tokens):
    '''
    Converts raw tokens into an array of class, function, and member
    variable declarations.

    Each definition is a dictionary object with keys for its attributes.
    '''
    nest = 0
    in_class = False
    class_name = None
    kind = None
    visibility = None
    static = False
    name = None
    extends = None
    implements = None
    args = []
    in_args = False
    returns = None
    doc = None
    declarations = []

    def save():
        if class_name or name:
            fields = {
                'class': unicode(class_name) if class_name else '__global__',
                'extends': unicode(extends) if extends else '',
                'implements': unicode(implements) if implements else '',
                'visibility': unicode(visibility) if visibility else 'public',
                'static': '1' if static else '0',
                'kind': unicode(kind) if kind else '',
                'name': unicode(name) if name else '',
                'args': args,
                'returns': unicode(returns) if returns else '',
                'doc': unicode(doc) if doc else '',
            }
            declarations.append(fields)

    def search_ahead(n, search):
        for i in range(n, len(raw_tokens)):
            t, stmt, line = raw_tokens[i]
            if t == search:
                return stmt

    n = 0
    for t, stmt, line in raw_tokens:
        if t == 'T_WHITESPACE':
            pass
        elif stmt == '{':
            nest += 1
        elif stmt == '}':
            nest -= 1
            if nest == 0:
                save()
                visibility = None
                kind = None
                in_class = False
                class_name = None
                extends = None
                implements = None
                name = None
                args = []
                in_args = False
                static = False
                doc = None
                returns = None
            if in_class and nest == 1:
                save()
                visibility = None
                kind = None
                name = None
                args = []
                in_args = False
                static = False
                doc = None
                returns = None
        elif t is None and stmt == ';' and in_class and nest == 1:
            save()
            visibility = None
            kind = None
            name = None
            static = False
            returns = None
            doc = None
        elif t == 'T_PUBLIC':
            visibility = 'public'
        elif t == 'T_PROTECTED':
            visibility = 'protected'
        elif t == 'T_PRIVATE':
            visibility = 'private'
        elif t == 'T_STATIC':
            static = True
        elif t == 'T_DOC_COMMENT':
            doc = stmt
        elif t == 'T_VARIABLE' and kind is None and in_class and nest == 1 and name is None:
            kind = 'var'
            name = stmt
            args = []
            if doc:
                data = re.findall('@var\s+([\w|\||\$]*?)[\s|$]', doc)
                if data:
                    returns = data[0]
        elif t == 'T_CONST':
            kind = 'var'
            name = search_ahead(n, 'T_STRING')
            args = []
            static = True
            if doc:
                data = re.findall('@var\s+([\w|\||\$]*?)[\s|$]', doc)
                if data:
                    returns = data[0]
        elif t == 'T_FUNCTION':
            kind = 'func'
            name = search_ahead(n, 'T_STRING')
            if name == '__construct' and class_name:
                returns = class_name
            if doc:
                data = re.findall('@return\s+([\w|\||\$]*?)[\s|$]', doc)
                if data:
                    returns = data[0]
        elif kind == 'func' and stmt == '(' and not args and (nest == 0 or in_class and nest == 1):
            in_args = True
        elif kind == 'func' and stmt == ')' and in_args:
            in_args = False
        elif kind == 'func' and t == 'T_VARIABLE' and in_args:
            vtype = ''
            if doc:
                v = stmt.replace('$', '')
                data = re.findall('@param\s+([\w|\||\$]*?)\s+\$' + v + '[\s|$]', doc)
                if data:
                    vtype = data[0]
            args.append([stmt, vtype])
        elif t == 'T_CLASS':
            in_class = True
            class_name = search_ahead(n, 'T_STRING')
        elif t == 'T_INTERFACE':
            class_name = search_ahead(n, 'T_STRING')
        elif t == 'T_EXTENDS':
            extends = search_ahead(n, 'T_STRING')
        elif t == 'T_IMPLEMENTS':
            implements = search_ahead(n, 'T_STRING')

        n += 1

    return declarations


def scan_file(filename, extension='.php'):
    '''
    Returns array of class, function, and member declarations for a given
    PHP source file.
    '''
    declarations = []

    name, ext = os.path.splitext(filename)
    if ext == extension:
        raw_tokens = get_all_tokens(filename=filename)
        declarations = convert_raw_tokens(raw_tokens)

        for i in range(0, len(declarations)):
            declarations[i]['path'] = filename

    return declarations


def scan_all_files(base_folder, extension='.php'):
    '''
    Returns array of class, function, and member declarations for all of the
    PHP source files on a given path.
    '''
    declarations = []
    for root, dirs, files in os.walk(base_folder):
        for name in files:
            filename, ext = os.path.splitext(name)
            if ext == extension:
                path = os.path.join(root, name)
                item = (os.path.abspath(path), scan_file(path))
                declarations.append(item)

    return declarations


'''
Initialization
'''
get_all_token_names()
