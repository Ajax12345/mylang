import mylang_tokenizer
import collections
import mylang_errors
import string
from mylang_config import config
import mylang_warnings
import functools


def parse_header(**kwargs):
    def parser_method(f):
        @functools.wraps(f)
        def wrapper(cls, original, line):
            params, name, warnings = f(cls, line)
            if len(params) > kwargs.get('param_num', 10):
                raise mylang_errors.TooManyParamemters("At line {}, near 'scope', found {}, expected {}".format(original.value.line_number, len(params),  kwargs.get('param_num', 10)))
            try:
                del cls.__dict__['param_variables']
            except KeyError:
                pass
            try:
                del cls.__dict__['seen_header']
            except KeyError:
                pass
            return params, name, warnings
        return wrapper
    return parser_method
class Scope:
    def __init__(self, name, namespace, params):
        self.__scope_name__ = name
        self.namespace = iter(map(iter, namespace))
        self.vals = {}
        self.__params__ = params
    def __getitem__(self, val_name):
        if val_name in self.__dict__:
            return self.__dict__[val_name]
        if val_name in self.vals:
            return self.vals[val_name]
        raise mylang_errors.AttributeNotFound("Attribute '{}' not found for scope '{}'".format(val_name, self.__scope_name__))
    def __setitem__(self, val_name, value):
        self.vals[val_name] = value
    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, ', '.join('{} = {}'.format(a, b)) for a, b in self.vals.items())

class Scopes:
    def __init__(self):
        self.__scope_count__ = 0
        self.scopes = {}
    def __setitem__(self, name, value):
        self.scopes[name] = value
        self.__scope_count__ += 1
    def __getitem__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        raise mylang_errors.AttributeNotFound("Scope '{}' not found".format(name))

class Parser:
    def __init__(self, token_list):
        print(token_list)
        self.token_list = iter(map(iter, token_list))
        self.vals = []
        self.variables = {}
        self.scopes = Scopes()
        self.parse()
        print(self.variables)
    def parse(self):
        current_line = next(self.token_list, None)
        if current_line:
            start = next(current_line)
            if start.type == 'VARIABLE':
                checking = next(current_line)
                start.value.isValid(checking.value)
                if checking.type == 'ASSIGN':
                    to_store = self.parse_assign(current_line)
                    self.variables[start.value.value] = to_store
            if start.type == 'SCOPE':
                params, name, flags = self.parse_scope(start, current_line, self.token_list)
                print("params: {}, name: {}, flags: {}".format(*[params, name, flags]))
                temp_flag = bool(flags)
                scope_block = []
                while True:
                    line = [c for c in next(self.token_list, None)]
                    if len(line) == 1 and line[0].value.value == '{':
                        if temp_flag:
                            temp_flag = False
                        else:
                            raise mylang_errors.InvalidScopeBlock('At line {}, near {}'.format(line[0].value.line_number, line[0].value.value))
                    if len(line) == 1 and line[0].value.value == '}':
                        break

                    if line is None:
                        raise mylang_errors.ReachedEndOfScopeBlock("missing block terminating character '}'")
                    if temp_flag:
                        raise mylang_errors.ReachedEndOfScopeBlock("missing block initiating character '{'")
                    scope_block.append(line)
                self.scopes[name] = Scope(name, scope_block, params)
            self.parse()

    @parse_header(param_num = config.MAX_PARAMS)
    def parse_scope_header(self, header):
        if 'seen_header' not in self.__dict__:
            scope_name = next(header)
            check_val = next(header, None)
            if not check_val:
                return [], scope_name.value.value, mylang_warnings.NoHeaderSeen
            scope_name.value.isValid(check_val.value)
            if check_val.type == 'OBRACKET':
                return [], scope_name.value.value, None
            if check_val.type == 'STARTARROW':
                params, warnings = self.parse_scope_params(check_val, header)
                return params, scope_name.value.value, warnings
            self.seen_header = scope_name.value.value
            self.parse_scope_header(scope_name.value, header)

    def parse_scope_params(self, first, line, found = []):
        start = next(line, None)
        print 'found here', found
        if not start:
            if not found:
                raise mylang_errors.ParameterSytnaxError('At line {}, near {}, illegal paramter declaration'.format(first.value.line_number, first.value.value))
        checking_val = next(line, None)
        if checking_val:
            start.value.isValid(checking_val.value)
        if start.type == 'VARIABLE':
            if checking_val.type == 'COMMA':

                return self.parse_scope_params(start, line, found+[start.value.value])
            if checking_val.type == 'ENDARROW':

                final_check = next(line, None)

                if not final_check:
                    return found+[start.value.value], mylang_warnings.NoHeaderSeen
                checking_val.value.isValid(final_check.value)
                if final_check.type == 'OBRACKET':
                    return found+[start.value.value], None
                raise mylang_errors.ParameterSytnaxError('At line {}, near {}, invalid syntax'.format(final_check.value.line_number, final_check.value.value))


            raise mylang_errors.ParameterSytnaxError('At line {}, near {}, expected a comma'.format(start.value.line_number, start.value.value))
        raise mylang_errors.ParameterSytnaxError('At line {}, near {}, invalid syntax'.format(start.value.line_number, start.value.value))


    def parse_scope(self, original, current_line, lines):
        params, results, flags = self.parse_scope_header(original, current_line)
        return params, results, flags
    def parse_assign(self, line):

        operation_converters = {'PLUS':lambda x, y:x+y, 'BAR':lambda x,y:x-y, 'STAR':lambda x, y:x*y, 'FORWARDSLASH':lambda x, y:x/y}
        current = next(line, None)
        if current.type == 'VARIABLE':
            test_final = next(line, None)
            if not test_final:
                if current.value.value not in self.variables:
                    raise mylang_errors.VariableNotDeclared("At line {}, '{}' not declared".format(current.value.line_number, current.value.value))
                return self.variables[current.value.value]
            current.value.isValid(test_final.value)
            '''
            if test_final.type == 'PLUS':
                returned_val = self.parse_assign(line)
                return self.variables[current.value.value]+(string.ascii_lowercase+string.ascii_uppercase)[52%returned_val] if isinstance(returned_val, int) and isinstance(self.variables[current.value.value], str) else self.variables[current.value.value]+returned_val
            '''
            if test_final.type in operation_converters:
                returned_val = self.parse_assign(line)
                if type(returned_val) != type(self.variables[current.value.value]):
                    raise mylang_errors.IncompatableTypes("At line {}, near {}, cannot {} variable of type '{}' to type '{}'".format(current.value.line_number, current.value.value, {'PLUS':'concatinate', 'BAR':'subtract', 'STAR':'multiply', 'FORWARDSLASH':'divide'}[test_final.type], type(self.variables[current.value.value]).__name__, type(returned_val).__name__))
                return operation_converters[test_final.type](self.variables[current.value.value], returned_val)
        if current.type == 'DIGIT':
            test_final = next(line, None)
            if not test_final:
                return int(current.value.value)
            current.value.isValid(test_final.value)
            '''
            if test_final.type == 'PLUS':
                returned_val = self.parse_assign(line)
                if not isinstance(returned_val, int):
                    raise mylang_errors.IncompatableTypes("At line {}, cannot concatinate type 'INT' to type {}".format(test_final.value.line_number, type(returned_val)))
                return int(current.value.value) + self.parse_assign(line)
            '''
            if test_final.type in operation_converters:
                if test_final.type == 'STAR':
                    second = next(line, None)
                    print('second', second.value.value, current.value.value)
                    if second.type != 'DIGIT':

                        raise mylang_errors.IncompatableTypes("At line {}, cannot multiply type 'INT' to type {}".format(second.value.line_number, type(second.value.value).__name__))
                    operator = next(line, None)
                    if not operator:
                        return int(second.value.value)*int(current.value.value)
                    returned_val = self.parse_assign(line)

                    return operation_converters[operator.type](int(current.value.value)*int(second.value.value), returned_val)
                returned_val = self.parse_assign(line)

                if type(returned_val) != type(int(current.value.value)):
                    raise mylang_errors.IncompatableTypes("At line {}, near {}, cannot {} variable of type 'INT' to type '{}'".format(current.value.line_number, current.value.value, {'PLUS':'concatinate', 'BAR':'subtract', 'STAR':'multiply', 'FORWARDSLASH':'divide'}[test_final.type], type(returned_val).__name__))
                return operation_converters[test_final.type](int(current.value.value), returned_val)
        if current.type == 'STRING':
            test_final = next(line, None)
            if not test_final:
                return current.value.value[1:-1]
            current_line.value.isValid(test_final.value)
            if test_final.type == 'PLUS':
                returned_val = self.parse_assign(line)
                if not isinstance(returned_val, str) or not isinstance(returned_val, int):
                    raise mylang_errors.IncompatableTypes("At line {}, cannot concatinate type 'STRING' to type {}".format(test_final.value.line_number, type(returned_val)))
                return current.value.value[1:-1] + (string.ascii_lowercase+string.ascii_uppercase)[52%returned_val] if isinstance(returned_val, int) else current.value.value[1:-1]+returned_val
            if test_final.type in operation_converters:
                raise mylang_errors.IncompatableTypes("At line {}, cannot {} type 'string' to type '{}'".format(current.value.line_number, {'PLUS':'concatinate', 'BAR':'subtract', 'STAR':'multiply', 'FORWARDSLASH':'divide'}[test_final.type], type(returned_val).__name__))



Parser(mylang_tokenizer.Tokenize('mylang.txt').tokenized_data)
