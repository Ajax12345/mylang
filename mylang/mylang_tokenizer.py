import collections
import re
import mylang_errors
class Variable:
    def __init__(self, value, line_number):
        self.line_number = line_number
        self.value = value
        self.rep = 'variable'
        self.valid_after = ['plus', 'modulo', 'larrow', 'rarrow', 'equals', 'comma', 'assign', 'bar', 'star', 'forwardslash', 'obracket', 'startarrow', 'endarrow', 'dot', 'oparen', 'cparen', 'colon', 'cbracket', 'digit', 'toreturn']
    def isValid(self, token):
        #print('offending', token.rep)
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
        self.valid_after = ['plus', 'modulo', 'larrow', 'rarrow', 'equals', 'comma', 'bar', 'star', 'forwardslash', 'cparen', 'cbracket']
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
        self.valid_after = ['plus', 'larrow', 'rarrow', 'equals', 'comma', 'cbracket']
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
        self.valid_after = ['variable', 'larrow', 'rarrow', 'equals', 'string', 'digit', 'OBRACKET']
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
class Scope:
    def __init__(self, value, line_number):
        self.line_number = line_number
        self.value = value
        self.rep = 'scope'
        self.valid_after = ['variable']
    def isValid(self, token):
        if token.rep not in self.valid_after:
            raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
        return True

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))

class OBracket:
    def __init__(self, value, line_number):
        self.line_number = line_number
        self.value = value
        self.rep = 'obracket'
        self.valid_after = []
    def isValid(self, token):
        raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))


    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))
class CBracket:
    def __init__(self, value, line_number):
        self.line_number = line_number
        self.value = value
        self.rep = 'cbracket'
        self.valid_after = []
    def isValid(self, token):
        raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))


    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))
class Startarrow:
    def __init__(self, value, line_number):
        self.line_number = line_number
        self.value = value
        self.rep = 'startarrow'
        self.valid_after = ['variable']
    def isValid(self, token):
        if token.rep not in self.valid_after:
            raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
        return True
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))

class Endarrow:
    def __init__(self, value, line_number):
        self.line_number = line_number
        self.value = value
        self.rep = 'endarrow'
        self.valid_after = ['obracket']
    def isValid(self, token):
        if token.rep not in self.valid_after:
            raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
        return True
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))

class Comma:
    def __init__(self, value, line_number):
        self.value = value
        self.rep = 'comma'
        self.line_number = line_number
        self.valid_after = ['variable']
    def isValid(self, token):
        if token.rep not in self.valid_after:
            raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
        return True
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))
class Dot:
    def __init__(self, value, line_number):
        self.value = value
        self.rep = 'dot'
        self.line_number = line_number
        self.valid_after = ['variable']
    def isValid(self, token):
        if token.rep not in self.valid_after:
            raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
        return True
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))

class OParen:
    def __init__(self, value, line_number):
        self.value = value
        self.line_number = line_number
        self.rep = 'oparen'
        self.valid_after = ['variable', 'digit', 'string', 'cparen']
    def isValid(self, token):
        if token.rep not in self.valid_after:
            raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
        return True
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))
class CParen:
    def __init__(self, value, line_number):
        self.value = value
        self.line_number = line_number
        self.rep = 'cparen'
        self.valid_after = ['obracket', 'plus', 'bar', 'star', 'toreturn']
    def isValid(self, token):
        if token.rep not in self.valid_after:
            raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
        return True
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))


class Global:
    def __init__(self, value, line_number):
        self.value = value
        self.line_number = line_number
        self.rep = 'global'
        self.valid_after = ['variable', 'transmute', 'scope', 'procedure']
    def isValid(self, token):
        if token.rep not in self.valid_after:
            raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
        return True
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))

class Procedure:
    def __init__(self, value, line_number):
        self.value = value
        self.line_number = line_number
        self.valid_after = ['variable', 'OPAREN']
        self.rep = 'procedure'
    def isValid(self, token):
        if token.rep not in self.valid_after:
            raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
        return True
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))

class Return:
    def __init__(self, value, line_number):
        self.value = value
        self.line_number = line_number
        self.rep = 'return'
        self.valid_after = ['variable', 'digit', 'string']
    def isValid(self, token):
        if token.rep not in self.valid_after:
            raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
        return True
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))

class Colon:
    def __init__(self, value, line_number):
        self.value = value
        self.line_number = line_number
        self.rep = 'colon'
        self.valid_after = ['variable', 'int', 'string', 'bool', 'arraylist']
    def isValid(self, token):
        if token.rep not in self.valid_after:
            raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
        return True
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))
class Int:
    def __init__(self, value, line_number):
        self.value = value
        self.line_number = line_number
        self.rep = 'int'
        self.valid_after = ['comma', 'cparen', 'cbracket', 'obracket']
    def isValid(self, token):

        if token.rep not in self.valid_after:
            print 'token.rep here', token.rep
            raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
        return True
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))
class String:
    def __init__(self, value, line_number):
        self.value = value
        self.line_number = line_number
        self.rep = 'string'
        self.valid_after = ['comma', 'cparen']
    def isValid(self, token):
        if token.rep not in self.valid_after:
            raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
        return True
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))
class Toreturn:
    def __init__(self, value, line_number):
        self.value = value
        self.line_number = line_number
        self.rep = 'toreturn'
        self.valid_after = ['INT', 'STRING', 'arraylist']
    def isValid(self, token):
        if token.rep not in self.valid_after:
            raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
        return True
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))
class Transmute:
    def __init__(self, value, line_number):
        self.value = value
        self.line_number = line_number
        self.rep = 'transmute'
        self.valid_after = ['procedure']
    def isValid(self, token):
        if token.rep not in self.valid_after:
            raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
        return True
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))

class Accumulate:
    def __init__(self, value, line_number):
        self.value = value
        self.line_number = line_number
        self.rep = 'accumulate'
        self.valid_after = ['variable', 'string', 'digit']
    def isValid(self, token):
        if token.rep not in self.valid_after:
            raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
        return True
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))
class Private:
    def __init__(self, value, line_number):
        self.value = value
        self.line_number = line_number
        self.rep = 'private'
        self.valid_after = ['variable', 'privateprocedure']
    def __contains__(self, v):
        return v in self.valid_after if isinstance(v, str) else v.rep in self.valid_after
    def isValid(self, token):
        if token.rep not in self.valid_after:
            raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
        return True
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))

class Privateprocedure:
    def __init__(self, value, line_number):
        self.value = value
        self.line_number = line_number
        self.rep = self.__class__.__name__.lower()
        self.valid_after = []
    def __contains__(self):
        return False
    def isValid(self, token):
        raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))

class Bool:
    def __init__(self, value, line_number):
        self.value = value
        self.line_number = line_number
        self.rep = self.__class__.__name__.lower()
        self.valid_after = ['comma', 'cparen', 'cbracket', 'obracket']
    def isValid(self, token):

        if token.rep not in self.valid_after:
            raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))

class Import:
    def __init__(self, value, line_number):
        self.value = value
        self.line_number = line_number
        self.rep = self.__class__.__name__.lower()
        self.valid_after = ['dot', 'variable']
    def isValid(self, token):
        if token.rep not in self.valid_after:
            raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))
class ArrayList:
    def __init__(self, value, line_number):
        self.value = value
        self.line_number = line_number
        self.rep = self.__class__.__name__.lower()
        self.valid_after = ['comma', 'obracket', 'cparen']
    def isValid(self, token):
        if token.rep not in self.valid_after:
            raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))
class Switch:
    def __init__(self, value, line_number):
        self.value = value
        self.line_number = line_number
        self.rep = self.__class__.__name__.lower()
        self.valid_after = ['oparen']
    def isValid(self, token):
        if token.rep not in self.valid_after:
            raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))
class Case:
    def __init__(self, value, line_number):
        self.value = value
        self.line_number = line_number
        self.rep = self.__class__.__name__.lower()
        self.valid_after = ['dot']
    def isValid(self, token):
        if token.rep not in self.valid_after:
            raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))
class Default:
    def __init__(self, value, line_number):
        self.value = value
        self.line_number = line_number
        self.rep = self.__class__.__name__.lower()
        self.valid_after = []
    def isValid(self, token):
        raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))
class Modulo:
    def __init__(self, value, line_number):
        self.value = value
        self.line_number = line_number
        self.rep = self.__class__.__name__.lower()
        self.valid_after = ['variable', 'digit']
    def isValid(self, token):
        if token.rep not in self.valid_after:
            raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))
class For:
    def __init__(self, value, line_number):
        self.value = value
        self.line_number = line_number
        self.rep = self.__class__.__name__.lower()
        self.valid_after = ['variable', 'arraylist', 'digit', 'str']
    def isValid(self, token):
        if token.rep not in self.valid_after:
            raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))

class Print:
    def __init__(self, value, line_number):
        self.value = value
        self.line_number = line_number
        self.rep = self.__class__.__name__.lower()
        self.valid_after = ['digit', 'string', 'str', 'cbracket', 'variable']
    def isValid(self, token):
        if token.rep not in self.valid_after:
            raise mylang_errors.IllegialPrecedence('At line number {line_number}, near {value}'.format(**self.__dict__))
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, "value = '{}'".format(self.value))


class Tokenize:
    token = collections.namedtuple('token', 'type, value')
    grammar = r'\bprint\b|\bfor\b|\bdefault\b|\bswitch\b|\bcase\b|(?<!")ArrayList(?!")|\bimport\b|\bprivate\b|@|\breturn\b|\baccumulate\b|\btransmute\b|\bprocedure\b|\bglobal\b|\bscope\b|"[a-zA-Z0-9_\s]+"|\d+|\b[a-zA-Z0-9_]+\b|\=|\b[a-zA-Z0-9]+\b|\-\>|\+|\*|\-|\/|\{|\}|\>|\<|,|\.|\(|\)|\:|%'
    types = [("PRINT", r'\bprint\b'), ("FOR", r'\bfor\b'), ('DEFAULT', r'\bdefault\b'), ('SWITCH', r'\bswitch\b'), ('CASE', r'\bcase\b'), ('ARRAYLIST', r'(?<!")ArrayList(?!")'), ('IMPORT', r'\bimport\b'), ('PRIVATEPROCEDURE', r'\bprivate\b'), ('PRIVATE', r'@'), ('ACCUMULATE', r'\baccumulate\b'), ('TRANSMUTE', r'\btransmute\b'), ('TORETURN', r'\-\>'), ('INT', r'\bint\b'), ('STRING', r'\bstring\b'), ('BOOL', r'\bbool\b'), ('COLON', r':'), ('RETURN', r'\breturn\b'), ('PROCEDURE', r'\bprocedure\b'), ('GLOBAL', r'\bglobal\b'), ('SCOPE', r'\bscope\b'), ('STRING', r'"[a-zA-Z0-9_\s]+"'), ('DIGIT', r'\b\d+\b'), ('VARIABLE', r'\b[a-zA-Z0-9_]+\b'), ('ASSIGN', r'\='), ('PLUS', '\+'), ('STAR', r'\*'), ('BAR', r'\-'), ('FORWARDSLASH', '\/'), ('OBRACKET', r'\{'), ('CBRACKET', r'\}'), ('STARTARROW', '\<'), ('ENDARROW', '\>'), ('COMMA', ','), ('DOT', '\.'), ('OPAREN', '\('), ('CPAREN', '\)'), ('MODULO', '%')]
    class_reps = {'STRING':String, 'DIGIT':Digit, 'VARIABLE':Variable, 'ASSIGN':Assign, 'PLUS':Plus, 'STAR':Star, 'BAR':Bar, 'FORWARDSLASH':Forwardslash, 'SCOPE':Scope, 'OBRACKET':OBracket, 'CBRACKET':CBracket, 'STARTARROW':Startarrow, 'ENDARROW':Endarrow, 'COMMA':Comma, 'DOT':Dot, 'OPAREN':OParen, 'CPAREN':CParen, 'GLOBAL':Global, 'PROCEDURE':Procedure, 'RETURN':Return, 'COLON':Colon, 'INT':Int, 'STRING':String, 'TORETURN':Toreturn, 'TRANSMUTE':Transmute, 'ACCUMULATE':Accumulate, 'PRIVATE':Private, 'PRIVATEPROCEDURE':Privateprocedure, 'BOOL':Bool, 'IMPORT':Import, 'ARRAYLIST':ArrayList, 'SWITCH':Switch, 'CASE':Case, 'DEFAULT':Default, 'MODULO':Modulo, 'FOR':For, 'PRINT':Print}
    def __init__(self, filename):
        self.file_data = [i.strip('\n') for i in open(filename)]
        self.tokenized_data = filter(None, list(Tokenize.parse_tokens(self.file_data)))
        print self.tokenized_data
    @classmethod
    def parse_tokens(cls, file_data):
        for line_num, line in enumerate(file_data, start = 1):
            new_line = [cls.token([a for a, b in cls.types if re.findall(b, i)][0], i) for i in re.findall(cls.grammar, line)]
            yield [cls.token(i.type, cls.class_reps[i.type](i.value, line_num)) for i in new_line]

if __name__ == '__main__':
    Tokenize('mylang.txt')
