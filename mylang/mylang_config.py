import collections
import abc
__all__ = ['Config', 'config', 'ObjectifyImport', 'ImportAll', 'options']
class Options:
    __metaclass__ = abc.ABCMeta
    @abc.abstractmethod
    def parse_config(self):
        '''read from config file and create dictionary
        layout of file will be similar to UBUNTU
        '''
        return

class Config(Options):
    def __init__(self):
        self.config = {}
    def parse_assign(self):
        return

class ImportAll:
    def __init__(self):
        self.import_flag = True
        self.message = 'import all'
        self.rep = '*'
    def __repr__(self):
        return str(self)
    def __str__(self):
        return 'ImportObject(message="{message}")'.format(**self.__dict__)

class ObjectifyImport:
    def __init__(self):
        self.import_flag = False
        self.message = 'keep as object'
    def __repr__(self):
        return str(self)
    def __str__(self):
        return 'ImportObject(message="{message}")'.format(**self.__dict__)

options = collections.namedtuple('options', ['MAX_PARAMS', 'MAX_SCOPE_PARAMS', 'ALLOWED_RETURN_TYPES', 'PRIVATE_VARIABLE_LEVEL', 'PRIVATE_PROCEDURE_LEVEL', 'MAX_PROCEDURE_PARAMS'])
config = options(5, 5, ['int', 'string', 'str', 'bool', "ArrayList"], True, False, 10)
