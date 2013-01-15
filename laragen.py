#!/usr/bin/python
'''
Laravel Code-intelignece Helper Generator

Copyright 2013 Max Ehsan <http://laravelbook.com/>

Github: https://github.com/laravelbook/laravel-codeintel-generator

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
import sys
import json
import phpparser

MAGIC_METHODS = ['__construct', '__destruct', '__call', '__callStatic', 
                 '__get', '__set', '__isset', '__unset', '__sleep', 
                 '__wakeup', '__toString', '__invoke', '__set_state', '__clone']

LARAVEL_CLASSMAP = [
    {
        'class': 'Application',
        'path': ('Foundation', 'Application.php'),
        'superclass': 'Illuminate\Foundation\Application',
        'subclass':  'App'
    },
    {
        'class': 'Artisan',
        'superclass': 'Illuminate\Foundation\Artisan',
        'path': ('Foundation', 'Artisan.php'),
        'subclass': 'Artisan'
    },
    {
        'class': 'Guard',
        'superclass': 'Illuminate\Auth\Guard',
        'subclass': 'Auth'
    },
    {
        'class': 'Store',
        'superclass': 'Illuminate\Cache\Store',
        'path': ('Store', 'Store.php'),
        'subclass': 'Cache'
    },
    {
        'class': 'Repository',
        'superclass': 'Illuminate\Config\Repository',
        'path': ('Config', 'Repository.php'),
        'subclass': 'Config'
    },
    {
        'class': 'Controller',
        'superclass': 'Illuminate\Routing\Controllers\Controller',
        'path': ('Controllers', 'Controller.php'),
        'subclass': 'Controller'
    },
    {
        'class': 'Cookie',
        'superclass': 'Illuminate\Cookie\CookieJar',
        'path': ('x', 'Cookie.php'),
        'subclass': 'Cookie'
    },
    {
        'class': 'Encrypter',
        'superclass': 'Illuminate\Encryption\Encrypter',
        'path': ('Encryption', 'Encrypter.php'),
        'subclass': 'Crypt'
    },
    {
        'class': 'Connection',
        'superclass': 'Illuminate\Database\Connection',
        'path': ('Database', 'Connection.php'),
        'subclass': 'DB'
    },
    {
        'class': 'Model',
        'superclass': 'Illuminate\Database\Eloquent\Model',
        'path': ('Eloquent', 'Model.php'),
        'subclass': 'Eloquent'
    },
    {
        'class': 'Event',
        'superclass': 'Illuminate\Events\Event',
        'path': ('Events', 'Event.php'),
        'subclass': 'Event'
    },
    {
        'class': 'Filesystem',
        'superclass': 'Illuminate\Filesystem\Filesystem',
        'path': ('Filesystem', 'Filesystem.php'),
        'subclass': 'File'
    },
    {
        'class': 'BcryptHasher',
        'superclass': 'Illuminate\Hashing\BcryptHasher',
        'path': ('Hashing', 'BcryptHasher.php'),
        'subclass': 'Hash'
    },
    {
        'class': 'Request',
        'superclass': 'Illuminate\Http\Request',
        'path': ('Http', 'Request.php'),
        'subclass': 'Input'
    },
    {
        'class': 'Translator',
        'superclass': 'Illuminate\Translation\Translator',
        'path': ('Translation', 'Translator.php'),
        'subclass': 'Lang'
    },
    {
        'class': 'Writer',
        'superclass': 'Illuminate\Log\Writer',
        'path': ('Log', 'Writer.php'),
        'subclass': 'Log'
    },
    {
        'class': 'Mailer',
        'superclass': 'Illuminate\Mail\Mailer',
        'path': ('Mail', 'Mailer.php'),
        'subclass': 'Mail'
    },
    {
        'class': 'Paginator',
        'superclass': 'Illuminate\Pagination\Paginator',
        'path': ('Pagination', 'Paginator.php'),
        'subclass': 'Paginator'
    },
    {
        'class': 'Redirector',
        'superclass': 'Illuminate\Routing\Redirector',
        'path': ('Routing', 'Redirector.php'),
        'subclass': 'Redirect'
    },
    {
        'class': 'Request',
        'superclass': 'Illuminate\Http\Request',
        'path': ('Http', 'Request.php'),
        'subclass': 'Request'
    },
    {
        'class': 'Response',
        'superclass': 'Illuminate\Http\Response',
        'path': ('Http', 'Response.php'),
        'subclass': 'Response'
    },
    {
        'class': 'Database',
        'superclass': 'Illuminate\Redis\Database',
        'path': ('Redis', 'Database.php'),
        'subclass': 'Redis'
    },
    {
        'class': 'Router',
        'superclass': 'Illuminate\Routing\Router',
        'path': ('Routing', 'Router.php'),
        'subclass': 'Route'
    },
    {
        'class': 'Builder',
        'superclass': 'Illuminate\Database\Schema\Builder',
        'path': ('Schema', 'Builder.php'),
        'subclass': 'Schema'
    },
    {
        'class': 'Store',
        'superclass': 'Illuminate\Session\Store',
        'path': ('Session', 'Store.php'),
        'subclass': 'Session'
    },
    {
        'class': 'UrlGenerator',
        'superclass': 'Illuminate\Routing\UrlGenerator',
        'path': ('Routing', 'UrlGenerator.php'),
        'subclass': 'URL'
    },
    {
        'class': 'Validator',
        'path': ('Validation', 'Validator.php'),
        'superclass': 'Illuminate\Validation\Factory',
        'subclass':  'Validator'
    },
    {
        'class': 'Environment',
        'superclass': 'Illuminate\View\Environment',
        'path': ('View', 'Environment.php'),
        'subclass': 'View'
    },
]

ATTRIBUTE_KIND_MAP = [
    {'src': 'func', 'dest': '@method'},
    {'src': 'prop', 'dest': '@property'},
    {'src': 'var',  'dest': '@var'}
]

def extract_doc_string(input):
    lines = [line.strip('/*\t\r\n ') for line in input.split('\n') if line]
    docstring, returns = '', ''
    params = []
    
    for line in lines:
        if line == '':
            continue
        if docstring == '':
            docstring = line
        
        if (line.startswith('@param')):
            params.append(line[len('@param'):].strip())
        elif (line.startswith('@return')):
            returns = line[len('@return'):].strip()
    
    return (docstring, ', '.join(params).strip(), returns)
    
def transmogrify_method_args(args):
    result = []
    for arg in args:
        arg.reverse()
        result.append(' '.join(arg).strip())
    return ', '.join(result).strip()

def transmogrify_attribute_kind(kind):
    global ATTRIBUTE_KIND_MAP    
    
    for kindmap in ATTRIBUTE_KIND_MAP:
        if kind == kindmap['src']:
            return kindmap['dest']
    
    return kind

def extract_relevant_info(source):
    docstring, params, returns = extract_doc_string(source['doc'])
    if returns:
        returns = source['returns']
    return dict(
        name = source['name'].strip('$'),
        kind = transmogrify_attribute_kind(source['kind']),
        returns = returns if returns else 'void',
        doc = docstring,
        args = params if params else transmogrify_method_args(source['args'])
    )

def filter_relevant_declarations_only(source_list):
    global MAGIC_METHODS
    result = []
    for item in source_list:
        if item['visibility'].lower() == 'public' and item['name'].strip():
            if item['name'] not in MAGIC_METHODS:
                result.append(extract_relevant_info(item))
    return result

def class_is_allowed(classname, filename):
    class_map = find_class_map(classname)
    if class_map == None:
        return False
    path_comp = class_map.get('path')
    if path_comp != None:
        folder, fname = os.path.split(filename)
        return True if folder.endswith(path_comp[0]) and fname == path_comp[1] else False
    return True            

def get_class_name(source_list):
    return source_list[0]['class'] if len(source_list) > 0 else ''

def find_class_map(classname):
    global LARAVEL_CLASSMAP
    for class_map in LARAVEL_CLASSMAP:
        if class_map['class'] == classname:
            return class_map
    return None
    

def generate_doc_block(classname, source_list):
    lines = []
    class_map = find_class_map(classname)
    if class_map == None:
        return lines
    
    lines.append('/**')
    for elem in source_list:
        params = '(%s)' % elem['args'] if elem['kind'] == '@method' else ''
        # *  @method static void                  registerAliasLoader(array $aliases) Register the aliased class loader.
        line = ' * ' + '\t'.join([elem['kind'], 'static', elem['returns'], elem['name'] + params, elem['doc']])
        lines.append(line)
    
    lines.append(' */\n')
    lines.append('class %s extends %s {}\n\n' % (class_map['subclass'], class_map['superclass']))
    return lines

def process_class_declaration(filename, decl):
    cname = get_class_name(decl)
    lines = []
    if class_is_allowed(cname, filename):
        decl = filter_relevant_declarations_only(decl)
        lines.extend(generate_doc_block(cname, decl))
    return lines

if __name__ == '__main__':
    
    filename = sys.argv[1]

    lines = []
    lines.append('''<?php die("Access denied!");
/**
 * ---------------- DO NOT UPLOAD THIS FILE TO LIVE SERVER ------------------------
 * Laravel IDE Helper <http://LaravelBook.com>
 * Implements code completion for Laravel 4 in JetBrains PhpStorm and SublimeText 2
 * --------------------------------------------------------------------------------
 */
 ''')

    if os.path.isdir(filename):
        all_declarations = phpparser.scan_all_files(filename)
        for (fname, declarations) in all_declarations:
            lines.extend(process_class_declaration(os.path.abspath(fname), declarations))        
    else:
        declarations = phpparser.scan_file(filename)
        lines.extend(process_class_declaration(os.path.abspath(filename), declarations))
    
    with file('_ide_helper.php', 'wb') as f:
        f.write('\n'.join(lines).strip())