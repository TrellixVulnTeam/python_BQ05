# pylint: disable=C0302, line-too-long, too-few-public-methods, too-many-branches, too-many-statements, no-member
'''Has config file settings read from textract.ini
'''
from inspect import getsourcefile as _getsourcefile
import os.path as _path

import funclib.iolib as _iolib
import funclib.inifilelib as _inifilelib


_PTH = _iolib.get_file_parts2(_path.abspath(_getsourcefile(lambda: 0)))[0]
_INIPATH = _path.normpath(_path.join(_PTH, 'textract.ini'))

_ConfigFile = _inifilelib.ConfigFile(_INIPATH)


class Db():
    '''db settings'''
    server = _ConfigFile.tryread('db', 'server')
    security = _ConfigFile.tryread('db', 'security')
    user = _ConfigFile.tryread('db', 'user')
    password = _ConfigFile.tryread('db', 'password')
    dbname = _ConfigFile.tryread('db', 'dbname')
    is_integrated = _ConfigFile.tryread('db', 'security').lower() == 'integrated'


class textract():
    '''general settings'''
    is_sentence_word_limit = _ConfigFile.tryread('textract', 'IS_SENTENCE_WORD_LIMIT', value_on_create=5, astype=int)
    log_file = _path.normpath(_ConfigFile.tryread('textract', 'LOG_FILE', value_on_create='C:/temp/textract.log', astype=str))
