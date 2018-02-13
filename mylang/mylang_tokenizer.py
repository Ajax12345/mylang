import collections
import re
import mylang_errors
class Variable:
    def __init__(self, value, line_number):
        self.line_number = line_number
        self.value = value
        self.rep = 'variable'
        self.valid_after = ['plus', 'larrow', 'rarrow', 'equals', 'comma', 'assign', 'bar', 'star', 'forwardslash']
    def isValid(self, token):
        print('offending', token.rep)
        if token.rep not in self.valid_after:
            raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
        return True
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))
class Digit:
    def __init__(self, value, line_number):
        self.line_number = line_number
        self.value = value
        self.rep = 'digit'
        self.valid_after = ['plus', 'larrow', 'rarrow', 'equals', 'comma', 'bar', 'star', 'forwardslash']
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))
    def isValid(self, token):
        if token.rep not in self.valid_after:
            raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
        return True
class String:
    def __init__(self, value, line_number):
        self.line_number = line_number
        self.value = value
        self.rep = 'string'
        self.valid_after = ['plus', 'larrow', 'rarrow', 'equals', 'comma']
    def isValid(self, token):

        if token.rep not in self.valid_after:
            raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
        return True
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))
class Assign:
    def __init__(self, value, line_number):
        self.line_number = line_number
        self.value = value
        self.rep = 'assign'
        self.valid_after = ['variable', 'larrow', 'rarrow', 'equals', 'string', 'digit']
    def isValid(self, token):
        if token.rep not in self.valid_after:
            raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
        return True
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))

class Plus:
    def __init__(self, value, line_number):
        self.line_number = line_number
        self.value = value
        self.rep = 'plus'
        self.valid_after = ['variable', 'equals', 'string', 'digit']
    def isValid(self, token):
        if token.rep not in self.valid_after:
            raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
        return True

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))

    #add overriding methods below for essential operations
class Star:
    def __init__(self, value, line_number):
        self.line_number = line_number
        self.value = value
        self.rep = 'star'
        self.valid_after = ['variable', 'equals', 'digit']
    def isValid(self, token):
        if token.rep not in self.valid_after:
            raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
        return True

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))

class Bar:
    def __init__(self, value, line_number):
        self.line_number = line_number
        self.value = value
        self.rep = 'bar'
        self.valid_after = ['variable', 'equals', 'digit']
    def isValid(self, token):
        if token.rep not in self.valid_after:
            raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
        return True

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))
class Forwardslash:
    def __init__(self, value, line_number):
        self.line_number = line_number
        self.value = value
        self.rep = 'forwardslash'
        self.valid_after = ['variable', 'equals', 'digit']
    def isValid(self, token):
        if token.rep not in self.valid_after:
            raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
        return True

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))

class Tokenize:
    token = collections.namedtuple('token', 'type, value')
    grammar = r'"[a-zA-Z0-9_]+"|\d+|\b[a-zA-Z0-9_]+\b|\=|\b[a-zA-Z0-9]+\b|\+|\*|\-|\/'
    types = [('STRING', r'"[a-zA-Z0-9_]+"'), ('DIGIT', r'\b\d+\b'), ('VARIABLE', r'\b[a-zA-Z0-9_]+\b'), ('ASSIGN', r'\='), ('PLUS', '\+'), ('STAR', r'\*'), ('BAR', r'\-'), ('FORWARDSLASH', '\/')]
    class_reps = {'STRING':String, 'DIGIT':Digit, 'VARIABLE':Variable, 'ASSIGN':Assign, 'PLUS':Plus, 'STAR':Star, 'BAR':Bar, 'FORWARDSLASH':Forwardslash}
    def __init__(self, filename):
        self.file_data = [i.strip('\n') for i in open(filename)]
        self.tokenized_data = list(Tokenize.parse_tokens(self.file_data))
        print(self.tokenized_data)
    @classmethod
    def parse_tokens(cls, file_data):
        for line_num, line in enumerate(file_data, start = 1):
            new_line = [cls.token([a for a, b in cls.types if re.findall(b, i)][0], i) for i in re.findall(cls.grammar, line)]
            yield [cls.token(i.type, cls.class_reps[i.type](i.value, line_num)) for i in new_line]
