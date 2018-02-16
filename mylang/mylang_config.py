import collections
import abc
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

options = collections.namedtuple('options', ['MAX_PARAMS'])
config = options(5)
