import mylang_tokenizer
import collections
import mylang_errors
import string
from mylang_config import config
import mylang_warnings
import functools
import copy
import itertools
import trace_parser
import mylang_wrappers

tracing = trace_parser.Trace()

class Scope:
    def __init__(self, name, namespace, params):
        print 'tricky namespace', namespace
        self.__scope_name__ = name
        self.params = params
        self.token_list = iter(map(iter, namespace))
        self.scopes = {}
        self.variables = {'__params__':params, '__scope_name__':name}
        if not len(params):

            self.parse()

    def update_vals(self, path, target_val):

        if not path[1:]:
            self.variables[path[0]] = target_val
        else:
            self.scopes[path[0]].update_vals(path[1:], target_val)

    @mylang_wrappers.parse_header(param_num = config.MAX_PARAMS)
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

    def parse(self):
        current_line = next(self.token_list, None)

        if current_line:
            current_line, self.current_line_on = itertools.tee(current_line)
            tracing.add_top_level(self.current_line_on)
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
                brackets_seen = collections.deque(['{']) if not temp_flag else collections.deque()
                while True:
                    line = [c for c in next(self.token_list, None)]
                    print 'line here', line
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

                print "scope block here", scope_block
                self.scopes[name] = Scope(name, scope_block, params)
            self.parse()
    def __len__(self):
        return len(self.params)

    @mylang_wrappers.verify_parameter(max_number = config.MAX_SCOPE_PARAMS)
    def __call__(self, *args):
        if len(args) != len(self.params):
            raise mylang_errors.TooManyParamemters("scope '{}' expects {} parameters, but recieved {}".format(self.__scope_name__, len(self), len(args)))
        self.variables.update(dict(zip(self.params, args)))
        self.parse()
        return self
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
            if test_final.type == 'OPAREN':
                current_params = []
                while True:
                    check_param = next(line, None)
                    if not check_param:
                        break
                    if check_param.type == 'VARIABLE':
                        second_param = next(line, None)
                        if not second_param:
                            raise mylang_errors.ParameterSytnaxError("At line {}, near '{}'".format(check_param.value.line_number, check_param.value.value))
                        check_param.value.isValid(second_param.value)
                        if second_param.type == 'COMMA':
                            if check_param.value.value not in self.variables:
                                raise mylang_errors.VariableNotDeclared("At line {}, near {}: '{}' not declared".format(check_param.value.line_number, check_param.value.value, check_param.value.value))
                            current_params.append(self.variables[check_param.value.value])
                        if second_param.type == 'CPAREN':
                            current_params.append(check_param.value.value)
                            break
                    if check_param.type == 'DIGIT':
                        second_param = next(line, None)
                        if not second_param:
                            raise mylang_errors.ParameterSytnaxError("At line {}, near '{}'".format(check_param.value.line_number, check_param.value.value))
                        if second_param.type == 'COMMA':
                            if check_param.value.value not in self.variables:
                                raise mylang_errors.VariableNotDeclared("At line {}, near {}: '{}' not declared".format(check_param.value.line_number, check_param.value.value, check_param.value.value))
                            current_params.append(int(self.variables[check_param.value.value]))
                        if second_param.type == 'CPAREN':
                            current_params.append(int(check_param.value.value))
                            break
                    if check_param.type == 'STRING':
                        second_param = next(line, None)
                        if not second_param:
                            raise mylang_errors.ParameterSytnaxError("At line {}, near '{}'".format(check_param.value.line_number, check_param.value.value))
                        if second_param.type == 'COMMA':
                            current_params.append(check_param.value.value[1:-1])
                        if second_param.type == "CPAREN":
                            current_params.append(check_param.value.value[1:-1])
                            break
                final_check = next(line, None)
                if final_check:
                    check_param.value.isValid(final_check.value)
                    if final_check.type in operation_converters:
                        raise mylang_errors.NotYetSupportedError("At line {}, near '{}': feature not yet implemented".format(final_check.value.line_number, final_check.value.value))
                if current.value.value not in self.scopes:
                    raise mylang_errors.VariableNotDeclared("At line {}, scope '{}' not declared".format(current.value.line_number, current.value.value))

                return self.scopes[current.value.value](*current_params)
            if test_final.type == 'DOT':
                path = collections.deque([current.value.value])
                end_line = False
                last_seen = None
                while True:
                    temp_path = next(line, None)
                    if not temp_path:
                        end_line = True
                        break
                    check = next(line, None)
                    if not check:
                        path.append(temp_path.value.value)
                        break
                    temp_path.value.isValid(check.value)
                    if check.type in operation_converters:
                        last_seen = check
                        path.append(temp_path.value.value)
                        break
                    if temp_path.type == 'VARIABLE':
                        path.append(temp_path.value.value)
                    if temp_path.type in operation_converters:
                        last_seen = temp_path
                        break
                print 'self.scopes', self.scopes
                flag = False
                try:
                    temp = self.variables[path[0]][path[1]]
                except:
                    pass
                else:
                    flag = True
                scope_result = self.scopes if not flag else self.variables
                if path[0] not in scope_result:
                    raise mylang_errors.AttributeNotFound("At line {}, near {}: variable '{}' has no attribute '{}'".format(current.value.line_number, current.value.value, current.value.value, path[1]))
                while path:
                    val = path.popleft()
                    scope_result = scope_result[val]
                if last_seen:
                    try:
                        final_part = self.parse_assign(line)
                        print 'scope_result',scope_result, type(scope_result)
                        return operation_converters[last_seen.type](scope_result, final_part)
                    except:
                        raise mylang_errors.IncompatableTypes("Cannot {} value of type '{}' to type '{}'".format({'PLUS':'contactinate', 'BAR':'subtract', 'STAR':'multiply', 'FORWARDSLASH':'divide'}[last_seen.type], type(scope_result).__name__, type(final_part).__name__))
                print "scope_result", scope_result
                return scope_result
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
    def __getitem__(self, val_name):
        if val_name in self.__dict__:
            return self.__dict__[val_name]
        if val_name in self.variables:
            return self.variables[val_name]
        if val_name in self.scopes:
            return self.scopes[val_name]
        raise mylang_errors.AttributeNotFound("Attribute '{}' not found for scope '{}'".format(val_name, self.__scope_name__))
    def __setitem__(self, val_name, value):
        self.variables[val_name] = value
    def __repr__(self):
        return "{}<storing {} scope{}:({})({})".format(self.__class__.__name__, len(self.scopes), 's' if len(self.scopes) != 1 else '',', '.join(str(b) for a, b in self.scopes.items()), ', '.join('{} = {}'.format(a, b) for a, b in self.variables.items()))
    def __str__(self):
        return "{}<storing {} scope{}:({})({})".format(self.__class__.__name__, len(self.scopes), 's' if len(self.scopes) != 1 else '',', '.join(str(b) for a, b in self.scopes.items()), ', '.join('{} = {}'.format(a, b) for a, b in self.variables.items()))

class Scopes:
    def __init__(self):
        self.__scope_count__ = 0
        self.scopes = {}
    def __contains__(self, name):
        return name in self.scopes
    def __setitem__(self, name, value):
        self.scopes[name] = value
        self.__scope_count__ += 1
    def __getitem__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        if name in self.scopes:
            return self.scopes[name]
        raise mylang_errors.AttributeNotFound("Scope '{}' not found".format(name))
    def __repr__(self):
        return "{}<{}>({})".format(self.__class__.__name__, "{} scope{}".format(self.__scope_count__, 's' if self.__scope_count__ != 1 else ''), ', '.join('{} => {}'.format(a, str(b)) for a, b in self.scopes.items()))
class Parser:
    def __init__(self, token_list):
        self.token_list = iter(map(iter, token_list))
        self.vals = []
        self.variables = {}
        self.scopes = Scopes()
        self.parse()
        print(self.variables)

    def parse(self):
        current_line = next(self.token_list, None)

        if current_line:
            current_line, self.current_line_on = itertools.tee(current_line)
            tracing.add_top_level(self.current_line_on)
            start = next(current_line)
            if start.type == 'VARIABLE':
                checking = next(current_line)
                start.value.isValid(checking.value)
                if checking.type == 'ASSIGN':
                    to_store = self.parse_assign(current_line)
                    self.variables[start.value.value] = to_store

                if checking.type == 'DOT':
                    path = collections.deque([start.value.value])
                    to_assign = None
                    while True:
                        current = next(current_line, None)
                        if not current:
                            raise mylang_errors.IllegialPrecedence("At line {}, near '{}', reached abrupt end of statement".format(checking.value.line_number, checking.value.value))
                        if current.type == 'VARIABLE':
                            check_next = next(current_line, None)
                            current.value.isValid(check_next.value)
                            if check_next.type == "DOT":
                                path.append(current.value.value)
                            if check_next.type == 'ASSIGN':
                                path.append(current.value.value)
                                to_assign = self.parse_assign(current_line)
                                break
                    print 'path', list(path)[1:]

                    self.scopes[path[0]].update_vals(list(path)[1:], to_assign)




            if start.type == 'SCOPE':
                params, name, flags = self.parse_scope(start, current_line, self.token_list)
                print("params: {}, name: {}, flags: {}".format(*[params, name, flags]))
                temp_flag = bool(flags)
                scope_block = []
                brackets_seen = collections.deque(['{']) if not temp_flag else collections.deque()
                while True:
                    line = [c for c in next(self.token_list, None)]
                    if len(line) == 1 and line[0].value.value == '{':
                        brackets_seen.append('{')
                    if len(line) == 1 and line[0].value.value == '}':
                        try:
                            val = brackets_seen.pop()
                            scope_block.append(line)
                        except:
                            raise mylang_errors.ReachedEndOfScopeBlock("missing block initiating character '{'")
                        if not brackets_seen:
                            break
                    if line is None:
                        raise mylang_errors.ReachedEndOfScopeBlock("missing block terminating character '}'")

                    scope_block.append(line)
                print 'scope_block', scope_block
                self.scopes[name] = Scope(name, scope_block, params)
                print "self.scopes, ", self.scopes
            self.parse()

    @mylang_wrappers.parse_header(param_num = config.MAX_PARAMS)
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
            if test_final.type == 'OPAREN':
                current_params = []
                while True:
                    check_param = next(line, None)
                    if not check_param:
                        break
                    if check_param.type == 'VARIABLE':
                        second_param = next(line, None)
                        if not second_param:
                            raise mylang_errors.ParameterSytnaxError("At line {}, near '{}'".format(check_param.value.line_number, check_param.value.value))
                        check_param.value.isValid(second_param.value)
                        if second_param.type == 'COMMA':
                            if check_param.value.value not in self.variables:
                                raise mylang_errors.VariableNotDeclared("At line {}, near {}: '{}' not declared".format(check_param.value.line_number, check_param.value.value, check_param.value.value))
                            current_params.append(self.variables[check_param.value.value])
                        if second_param.type == 'CPAREN':
                            current_params.append(check_param.value.value)
                            break
                    if check_param.type == 'DIGIT':
                        second_param = next(line, None)
                        if not second_param:
                            raise mylang_errors.ParameterSytnaxError("At line {}, near '{}'".format(check_param.value.line_number, check_param.value.value))
                        if second_param.type == 'COMMA':
                            current_params.append(int(check_param.value.value))
                        if second_param.type == 'CPAREN':
                            current_params.append(int(check_param.value.value))
                            break
                    if check_param.type == 'STRING':
                        second_param = next(line, None)
                        if not second_param:
                            raise mylang_errors.ParameterSytnaxError("At line {}, near '{}'".format(check_param.value.line_number, check_param.value.value))
                        if second_param.type == 'COMMA':
                            current_params.append(check_param.value.value[1:-1])
                        if second_param.type == "CPAREN":
                            current_params.append(check_param.value.value[1:-1])
                            break
                final_check = next(line, None)
                if final_check:
                    check_param.value.isValid(final_check.value)
                    if final_check.type in operation_converters:
                        raise mylang_errors.NotYetSupportedError("At line {}, near '{}': feature not yet implemented".format(final_check.value.line_number, final_check.value.value))
                if current.value.value not in self.scopes:
                    raise mylang_errors.VariableNotDeclared("At line {}, scope '{}' not declared".format(current.value.line_number, current.value.value))

                return self.scopes[current.value.value](*current_params)
            if test_final.type == 'DOT':
                path = collections.deque([current.value.value])
                end_line = False
                last_seen = None
                while True:
                    temp_path = next(line, None)
                    if not temp_path:
                        end_line = True
                        break
                    check = next(line, None)
                    if not check:
                        path.append(temp_path.value.value)
                        break
                    temp_path.value.isValid(check.value)
                    if check.type in operation_converters:
                        last_seen = check
                        path.append(temp_path.value.value)
                        break
                    if temp_path.type == 'VARIABLE':
                        path.append(temp_path.value.value)
                    if temp_path.type in operation_converters:
                        last_seen = temp_path
                        break
                print 'self.scopes', self.scopes
                flag = False
                try:
                    temp = self.variables[path[0]][path[1]]
                except:
                    pass
                else:
                    flag = True
                scope_result = self.scopes if not flag else self.variables
                if path[0] not in scope_result:
                    raise mylang_errors.AttributeNotFound("At line {}, near {}: variable '{}' has no attribute '{}'".format(current.value.line_number, current.value.value, current.value.value, path[1]))
                while path:
                    val = path.popleft()
                    scope_result = scope_result[val]
                if last_seen:
                    try:
                        final_part = self.parse_assign(line)
                        print 'scope_result',scope_result, type(scope_result)
                        return operation_converters[last_seen.type](scope_result, final_part)
                    except:
                        raise mylang_errors.IncompatableTypes("Cannot {} value of type '{}' to type '{}'".format({'PLUS':'contactinate', 'BAR':'subtract', 'STAR':'multiply', 'FORWARDSLASH':'divide'}[last_seen.type], type(scope_result).__name__, type(final_part).__name__))
                print "scope_result", scope_result
                return scope_result
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
