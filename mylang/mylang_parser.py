import mylang_tokenizer
import collections
import mylang_errors
import string
from mylang_config import config
import mylang_warnings
import functools
import copy
import datetime
import itertools
import trace_parser
import mylang_wrappers

tracing = trace_parser.Trace()
class Procedure:
    def __init__(self, name, parameters, namespace, **kwargs):
        self.variables = kwargs.get('current_namespace') if kwargs.get('current_namespace') else {}
        self.is_global = bool(kwargs.get('current_namespace'))
        self.scopes = {}
        self.procedures = {}
        self.name = name
        self.to_return = []
        self.token_list = iter(map(iter, namespace))
        self.params = parameters
        self.can_mutate = kwargs.get('can_mutate', False)
        print 'self.can_mutate', self.can_mutate
        if not self.params:
            self.parse()
        print 'to_return', self.to_return

    @mylang_wrappers.verify_procedure_parameter(valid_return_types = config.ALLOWED_RETURN_TYPES, max_param_val = config.MAX_PARAMS)
    def parse_procedure_header(self, header_line, current = []):

        current_t = next(header_line, None)

        if not current_t:
            raise mylang_errors.InvalidEndOfDeclaration("Reached invalid end of procedure declaration")
        if current_t.type == 'CPAREN':
            second = next(header_line, None)
            if not second:

                return current, mylang_warnings.NoHeaderSeen, None
            current_t.value.isValid(second.value)
            if second.type == 'OBRACKET':
                print 'returning here'
                return current, None, None
            if second.type == 'TORETURN':
                final_check = next(header_line, None)
                if not final_check:
                    raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': a return type must be specified".format(second.value.line_number, second.value.value))
                last_check = next(header_line, None)
                if not last_check:
                    print 'returning here'
                    return current, mylang_warnings.NoHeaderSeen, final_check.value.value
                final_check.value.isValid(last_check.value)
                print 'returning here'
                return current, None, final_check.value.value
        if current_t.type == 'VARIABLE':
            check_next = next(header_line, None)
            if not check_next:
                raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}', rearched invalid end of procedure declaration".format(current_t.value.line_number, current_t.value.value))
            current_t.value.isValid(check_next.value)
            if check_next.type == 'PLUS':
                raise mylang_errors.NotYetSupportedError("At line {}, near '{}': feature not yet supported".format(check_next.value.line_number, check_next.value.value))
                '''
                checking_next_val = next(header_line, None)
                if not checking_next_val:
                    raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': expecting close paren or parameter specification type".format(final_check.value.line_number, final_check.value.value))
                if checking_next_val.type == 'COLON':
                    testing_third = next(header_line, None)
                    if not testing_third:
                        raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': expecting close paren or parameter specification type".format(checking_next_val.line_number, checking_next_val.value.value))
                    testing_second_last = next(header_line, None)
                    if not testing_second:
                        raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': expecting close paren or parameter specification type".format(testing_third.line_number, testing_third.value.value))
                    if testing_second_last.type == 'CPAREN':
                        '''
            if check_next.type == 'CPAREN':
                current.append(current_t.value.value)
                final_check = next(header_line, None)
                if not final_check:
                    return current, mylang_warnings.NoHeaderSeen, None
                check_next.value.isValid(final_check.value)
                if final_check.type == 'OBRACKET':
                    return current, None, None

                if final_check.type == 'TORETURN':
                    return_type = next(header_line, None)
                    if not return_type:
                        raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '->': expecting a return type".format(final_check.value.line_number))
                    final_bracket = next(header_line, None)
                    if not final_bracket:
                        return current, mylang_warnings.NoHeaderSeen, return_type.value.value
                    return current, None, return_type.value.value
            if check_next.type == 'COMMA':
                return self.parse_procedure_header(header_line, current+[current_t.value.value])
            if check_next.type == 'COLON':
                testing_second = next(header_line, None)
                if not testing_second:
                    raise mylang_errors.InvalidEndOfDeclaration("At line {}, near {}: reached invalid end of procedure declaration".format(check_next.value.line_number, check_next.value.value))
                check_next.value.isValid(testing_second.value)
                final_check = next(header_line, None)
                if not final_check:
                    raise mylang_errors.InvalidEndOfDeclaration("At line {}, near {}: reached invalid end of procedure declaration".format(check_next.value.line_number, check_next.value.value))

                testing_second.value.isValid(final_check.value)
                #print 'last here', testing_second.value, final_check.value

                if final_check.type == 'COMMA':
                    return self.parse_procedure_header(header_line, current+[[current_t.value.value, testing_second.value.value]])
                if final_check.type == 'CPAREN':
                    checking_final_val = next(header_line, None)
                    if not checking_final_val:
                        current.append([current_t.value.value, testing_second.value.value])
                        return current, mylang_warnings.NoHeaderSeen, None
                    final_check.value.isValid(checking_final_val.value)
                    if checking_final_val.type == 'OBRACKET':
                        current.append([current_t.value.value, testing_second.value.value])
                        return current, None, None
                    if checking_final_val.type == 'TORETURN':
                        last_final_check = next(header_line, None)
                        if not last_final_check:
                            raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '->': must specify a return type".format(checking_final_val.value.line_number))
                        last_check_1 = next(header_line, None)
                        current.append([current_t.value.value, testing_second.value.value])
                        if not last_check_1:
                            return current, mylang_warnings.NoHeaderSeen, last_final_check.value.value

                        return current, None, last_final_check.value.value
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


                    self.scopes[path[0]].update_vals(list(path)[1:], to_assign)


            if start.type == 'RETURN':
                self.to_return = self.parse_assign(current_line)
                return
            if start.type == 'ACCUMULATE':
                self.to_return.append(self.parse_assign(current_line))

            if start.type == 'GLOBAL':
                next_start = next(current_line, None)

                if not next_start:
                    raise mylang_errors.InvalidEndOfDeclaration("At line {}, near 'global', expecting scope or procedure declaration".format(start.value.line_number))
                start.value.isValid(next_start.value)
                if next_start.type == 'TRANSMUTE':
                    next_start_1 = next(current_line, None)
                    if not next_start_1:
                        raise mylang_errors.InvalidEndOfDeclaration("At line {}, near 'global', expecting scope or procedure declaration".format(next_start.value.line_number))
                    if next_start_1.type == 'PROCEDURE':
                        possible_name = next(current_line, None)
                        self.possible_name = possible_name
                        if not possible_name:
                            raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': expecting a scope or procedure declaration".format(next_start_1.value.line_number, next_start_1.value.value))
                        next_start_1.value.isValid(possible_name.value)
                        possible_start = next(current_line, None)
                        if not possible_start:
                            raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': expecting a scope or procedure declaration".format(next_start_1.value.line_number, possible_name.value.value))
                        possible_name.value.isValid(possible_start.value)
                        function_params, warnings, return_type = self.parse_procedure_header(current_line)
                        print "procedure name is: {}, params are: {}, warnings include: {}, return_type is {}".format(possible_name.value.value, function_params, warnings, return_type)
                if next_start.type == 'PROCEDURE':
                    possible_name = next(current_line, None)
                    self.possible_name = possible_name
                    if not possible_name:
                        raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': expecting a scope or procedure declaration".format(next_start.value.line_number, next_start.value.value))
                    next_start.value.isValid(possible_name.value)
                    possible_start = next(current_line, None)
                    if not possible_start:
                        raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': expecting a scope or procedure declaration".format(next_start.value.line_number, possible_name.value.value))
                    possible_name.value.isValid(possible_start.value)
                    function_params, warnings, return_type = self.parse_procedure_header(current_line)
                    print "procedure name is: {}, params are: {}, warnings include: {}, return_type is {}".format(possible_name.value.value, function_params, warnings, return_type)
                if next_start.type == 'SCOPE':
                    params, name, flags = self.parse_scope(next_start, current_line, self.token_list)

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
                    self.scopes[name] = Scope(name, scope_block, params, current_namespace = self.variables)
            if start.type == 'PROCEDURE':
                possible_name = next(current_line, None)
                self.possible_name = possible_name
                if not possible_name:
                    raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': expecting a scope or procedure declaration".format(start.value.line_number, start.value.value))
                start.value.isValid(possible_name.value)
                possible_start = next(current_line, None)
                if not possible_start:
                    raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': expecting a scope or procedure declaration".format(start.value.line_number, possible_name.value.value))
                possible_name.value.isValid(possible_start.value)
                function_params, warnings, return_type = self.parse_procedure_header(current_line)
                print "procedure name is: {}, params are: {}, warnings include: {}, return_type is {}".format(possible_name.value.value, function_params, warnings, return_type)
                current_stack = collections.deque(['{']) if not warnings else collections.deque()
                procedure_namespace = []
                while True:
                    current_namespace_line = next(self.token_list, None)

                    if not current_namespace_line:
                        raise mylang_errors.ReachedEndOfProcedureBlock("Expecting a close bracket for procedure '{}'".format(possible_name.value.value))
                    new_namespace_line = [i for i in current_namespace_line]


                    if any(i.type == 'OBRACKET' for i in new_namespace_line):
                        current_stack.append('{')
                        procedure_namespace.append(new_namespace_line)
                    if any(i.type == 'CBRACKET' for i in new_namespace_line):
                        if not current_stack:
                            raise mylang_errors.InvalidStartOfProcedureBlock("Missing '{' for start of scope of procedure '{}'".format(possible_name.value.value))
                        val = current_stack.pop()
                        if not current_stack:
                            break
                    else:
                        procedure_namespace.append(new_namespace_line)


                self.scopes[possible_name.value.value] = Scope(possible_name.value.value, [], [], current_namespace = {'param_num':len(function_params)})
                self.scopes[possible_name.value.value].scopes['signature'] = Scope('Signature', [], [], current_namespace = {'parameters':', '.join(i if not isinstance(i, list) else i[0] for i in function_params), 'types':', '.join('{}:{}'.format(i, None) if not isinstance(i, list) else "{}:{}".format(i[0], i[1]) for i in function_params)})
                self.procedures[possible_name.value.value] = Procedure(possible_name.value.value, function_params, procedure_namespace, )
            if start.type == 'SCOPE':
                params, name, flags = self.parse_scope(start, current_line, self.token_list)

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

                self.scopes[name] = Scope(name, scope_block, params)

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

                        return operation_converters[last_seen.type](scope_result, final_part)
                    except:
                        raise mylang_errors.IncompatableTypes("Cannot {} value of type '{}' to type '{}'".format({'PLUS':'contactinate', 'BAR':'subtract', 'STAR':'multiply', 'FORWARDSLASH':'divide'}[last_seen.type], type(scope_result).__name__, type(final_part).__name__))

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
    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, 'name: {}, params: {}, global: {}, transmute: '.format(self.name, len(self.params), ['Yes', 'No'][self.is_global], ['Yes', 'No'][self.can_mutate]))
    def __str__(self):
        return repr(self)

    @mylang_wrappers.verify_passed_types
    def __call__(self, *args):
        if args:
            self.variables.update(dict(zip([i if not isinstance(i, list) else i[0] for i in self.params], args)))
            self.parse()
        return self.to_return, self.variables if self.can_mutate else None

class Procedures:
    def __init__(self):
        self.procedure_list = {}
    def __getitem__(self, name):
        if name not in self.procedure_list:
            raise mylang_errors.NoProcedureDeclared("Procedure '{}' not declared".format(name))
        return self.procedure_list[name]
    def __setitem__(self, name, procedure_object):
        self.procedure_list[name] = procedure_object
    def __contains__(self, name):
        return name in self.procedure_list
    def __len__(self):
        return len(self.procedure_list)
    def __repr__(self):
        return "{}(<{} procedure{}>{})".format(self.__class__.__name__, len(self), 's' if len(self) != 1 else '', ', '.join('{}:{}'.format(a, str(b)) for i in self.procedure_list.items()))
class Scope:
    def __init__(self, name, namespace, params, **kwargs):
        self.procedures = Procedures()
        self.__scope_name__ = name
        self.params = params
        self.token_list = iter(map(iter, namespace))
        self.scopes = {}
        self.date_created = datetime.datetime.now()
        self.variables = {'__params__':params, '__scope_name__':name, '__receipt__':"<object '{}' created on {} at {}(hh:mm:s)".format(self.__class__.__name__, '{}/{}/{}'.format(self.date_created.month, self.date_created.day, self.date_created.year), '{}:{}:{}'.format(self.date_created.hour, self.date_created.minute, self.date_created.second))}
        if kwargs.get('current_namespace', None):
            self.variables.update(kwargs.get('current_namespace'))
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

    @mylang_wrappers.verify_procedure_parameter(valid_return_types = config.ALLOWED_RETURN_TYPES, max_param_val = config.MAX_PARAMS)
    def parse_procedure_header(self, header_line, current = []):

        current_t = next(header_line, None)

        if not current_t:
            raise mylang_errors.InvalidEndOfDeclaration("Reached invalid end of procedure declaration")
        if current_t.type == 'CPAREN':
            second = next(header_line, None)
            if not second:

                return current, mylang_warnings.NoHeaderSeen, None
            current_t.value.isValid(second.value)
            if second.type == 'OBRACKET':
                print 'returning here'
                return current, None, None
            if second.type == 'TORETURN':
                final_check = next(header_line, None)
                if not final_check:
                    raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': a return type must be specified".format(second.value.line_number, second.value.value))
                last_check = next(header_line, None)
                if not last_check:
                    print 'returning here'
                    return current, mylang_warnings.NoHeaderSeen, final_check.value.value
                final_check.value.isValid(last_check.value)
                print 'returning here'
                return current, None, final_check.value.value
        if current_t.type == 'VARIABLE':
            check_next = next(header_line, None)
            if not check_next:
                raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}', rearched invalid end of procedure declaration".format(current_t.value.line_number, current_t.value.value))
            current_t.value.isValid(check_next.value)
            if check_next.type == 'PLUS':
                raise mylang_errors.NotYetSupportedError("At line {}, near '{}': feature not yet supported".format(check_next.value.line_number, check_next.value.value))
                '''
                checking_next_val = next(header_line, None)
                if not checking_next_val:
                    raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': expecting close paren or parameter specification type".format(final_check.value.line_number, final_check.value.value))
                if checking_next_val.type == 'COLON':
                    testing_third = next(header_line, None)
                    if not testing_third:
                        raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': expecting close paren or parameter specification type".format(checking_next_val.line_number, checking_next_val.value.value))
                    testing_second_last = next(header_line, None)
                    if not testing_second:
                        raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': expecting close paren or parameter specification type".format(testing_third.line_number, testing_third.value.value))
                    if testing_second_last.type == 'CPAREN':
                        '''
            if check_next.type == 'CPAREN':
                current.append(current_t.value.value)
                final_check = next(header_line, None)
                if not final_check:
                    return current, mylang_warnings.NoHeaderSeen, None
                check_next.value.isValid(final_check.value)
                if final_check.type == 'OBRACKET':
                    return current, None, None

                if final_check.type == 'TORETURN':
                    return_type = next(header_line, None)
                    if not return_type:
                        raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '->': expecting a return type".format(final_check.value.line_number))
                    final_bracket = next(header_line, None)
                    if not final_bracket:
                        return current, mylang_warnings.NoHeaderSeen, return_type.value.value
                    return current, None, return_type.value.value
            if check_next.type == 'COMMA':
                return self.parse_procedure_header(header_line, current+[current_t.value.value])
            if check_next.type == 'COLON':
                testing_second = next(header_line, None)
                if not testing_second:
                    raise mylang_errors.InvalidEndOfDeclaration("At line {}, near {}: reached invalid end of procedure declaration".format(check_next.value.line_number, check_next.value.value))
                check_next.value.isValid(testing_second.value)
                final_check = next(header_line, None)
                if not final_check:
                    raise mylang_errors.InvalidEndOfDeclaration("At line {}, near {}: reached invalid end of procedure declaration".format(check_next.value.line_number, check_next.value.value))

                testing_second.value.isValid(final_check.value)
                #print 'last here', testing_second.value, final_check.value

                if final_check.type == 'COMMA':
                    return self.parse_procedure_header(header_line, current+[[current_t.value.value, testing_second.value.value]])
                if final_check.type == 'CPAREN':
                    checking_final_val = next(header_line, None)
                    if not checking_final_val:
                        current.append([current_t.value.value, testing_second.value.value])
                        return current, mylang_warnings.NoHeaderSeen, None
                    final_check.value.isValid(checking_final_val.value)
                    if checking_final_val.type == 'OBRACKET':
                        current.append([current_t.value.value, testing_second.value.value])
                        return current, None, None
                    if checking_final_val.type == 'TORETURN':
                        last_final_check = next(header_line, None)
                        if not last_final_check:
                            raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '->': must specify a return type".format(checking_final_val.value.line_number))
                        last_check_1 = next(header_line, None)
                        current.append([current_t.value.value, testing_second.value.value])
                        if not last_check_1:
                            return current, mylang_warnings.NoHeaderSeen, last_final_check.value.value

                        return current, None, last_final_check.value.value
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


                    self.scopes[path[0]].update_vals(list(path)[1:], to_assign)



            if start.type == 'GLOBAL':
                next_start = next(current_line, None)

                if not next_start:
                    raise mylang_errors.InvalidEndOfDeclaration("At line {}, near 'global', expecting scope or procedure declaration".format(start.value.line_number))
                start.value.isValid(next_start.value)
                print 'IN HERE TESTING GLOBAL'
                if next_start.type == 'TRANSMUTE':
                    next_start_1 = next(current_line, None)
                    if not next_start_1:
                        raise mylang_errors.InvalidEndOfDeclaration("At line {}, near 'global', expecting scope or procedure declaration".format(next_start.value.line_number))
                    if next_start_1.type == 'PROCEDURE':
                        possible_name = next(current_line, None)
                        self.possible_name = possible_name
                        if not possible_name:
                            raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': expecting a scope or procedure declaration".format(next_start_1.value.line_number, next_start_1.value.value))
                        next_start_1.value.isValid(possible_name.value)
                        possible_start = next(current_line, None)
                        if not possible_start:
                            raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': expecting a scope or procedure declaration".format(next_start_1.value.line_number, possible_name.value.value))
                        possible_name.value.isValid(possible_start.value)
                        function_params, warnings, return_type = self.parse_procedure_header(current_line)
                        print "procedure name is: {}, params are: {}, warnings include: {}, return_type is {}".format(possible_name.value.value, function_params, warnings, return_type)
                        print "procedure name is: {}, params are: {}, warnings include: {}, return_type is {}".format(possible_name.value.value, function_params, warnings, return_type)
                        current_stack = collections.deque(['{']) if not warnings else collections.deque()
                        procedure_namespace = []
                        while True:
                            current_namespace_line = next(self.token_list, None)

                            if not current_namespace_line:
                                raise mylang_errors.ReachedEndOfProcedureBlock("Expecting a close bracket for procedure '{}'".format(possible_name.value.value))
                            new_namespace_line = [i for i in current_namespace_line]


                            if any(i.type == 'OBRACKET' for i in new_namespace_line):
                                current_stack.append('{')
                                procedure_namespace.append(new_namespace_line)
                            if any(i.type == 'CBRACKET' for i in new_namespace_line):
                                if not current_stack:
                                    raise mylang_errors.InvalidStartOfProcedureBlock("Missing '{' for start of scope of procedure '{}'".format(possible_name.value.value))
                                val = current_stack.pop()
                                if not current_stack:
                                    break
                            else:
                                procedure_namespace.append(new_namespace_line)


                        self.scopes[possible_name.value.value] = Scope(possible_name.value.value, [], [], current_namespace = {'param_num':len(function_params)})
                        self.scopes[possible_name.value.value].scopes['signature'] = Scope('Signature', [], [], current_namespace = {'parameters':', '.join(i if not isinstance(i, list) else i[0] for i in function_params), 'types':', '.join('{}:{}'.format(i, None) if not isinstance(i, list) else "{}:{}".format(i[0], i[1]) for i in function_params)})

                        self.procedures[possible_name.value.value] = Procedure(possible_name.value.value, function_params, procedure_namespace, can_mutate = True, current_namespace = self.variables)
                if next_start.type == 'PROCEDURE':
                    possible_name = next(current_line, None)
                    self.possible_name = possible_name
                    if not possible_name:
                        raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': expecting a scope or procedure declaration".format(next_start.value.line_number, next_start.value.value))
                    next_start.value.isValid(possible_name.value)
                    possible_start = next(current_line, None)
                    if not possible_start:
                        raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': expecting a scope or procedure declaration".format(next_start.value.line_number, possible_name.value.value))
                    possible_name.value.isValid(possible_start.value)
                    function_params, warnings, return_type = self.parse_procedure_header(current_line)
                    print "procedure name is: {}, params are: {}, warnings include: {}, return_type is {}".format(possible_name.value.value, function_params, warnings, return_type)
                    current_stack = collections.deque(['{']) if not warnings else collections.deque()
                    procedure_namespace = []
                    while True:
                        current_namespace_line = next(self.token_list, None)

                        if not current_namespace_line:
                            raise mylang_errors.ReachedEndOfProcedureBlock("Expecting a close bracket for procedure '{}'".format(possible_name.value.value))
                        new_namespace_line = [i for i in current_namespace_line]


                        if any(i.type == 'OBRACKET' for i in new_namespace_line):
                            current_stack.append('{')
                            procedure_namespace.append(new_namespace_line)
                        if any(i.type == 'CBRACKET' for i in new_namespace_line):
                            if not current_stack:
                                raise mylang_errors.InvalidStartOfProcedureBlock("Missing '{' for start of scope of procedure '{}'".format(possible_name.value.value))
                            val = current_stack.pop()
                            if not current_stack:
                                break
                        else:
                            procedure_namespace.append(new_namespace_line)


                    self.scopes[possible_name.value.value] = Scope(possible_name.value.value, [], [], current_namespace = {'param_num':len(function_params)})
                    self.scopes[possible_name.value.value].scopes['signature'] = Scope('Signature', [], [], current_namespace = {'parameters':', '.join(i if not isinstance(i, list) else i[0] for i in function_params), 'types':', '.join('{}:{}'.format(i, None) if not isinstance(i, list) else "{}:{}".format(i[0], i[1]) for i in function_params)})
                    self.procedures[possible_name.value.value] = Procedure(possible_name.value.value, function_params, procedure_namespace, current_namespace = self.variables)
                if next_start.type == 'SCOPE':
                    params, name, flags = self.parse_scope(next_start, current_line, self.token_list)

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
                    self.scopes[name] = Scope(name, scope_block, params, current_namespace = self.variables)
            if start.type == 'PROCEDURE':
                possible_name = next(current_line, None)
                self.possible_name = possible_name
                if not possible_name:
                    raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': expecting a scope or procedure declaration".format(start.value.line_number, start.value.value))
                start.value.isValid(possible_name.value)
                possible_start = next(current_line, None)
                if not possible_start:
                    raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': expecting a scope or procedure declaration".format(start.value.line_number, possible_name.value.value))
                possible_name.value.isValid(possible_start.value)
                function_params, warnings, return_type = self.parse_procedure_header(current_line)
                print "procedure name is: {}, params are: {}, warnings include: {}, return_type is {}".format(possible_name.value.value, function_params, warnings, return_type)
                current_stack = collections.deque(['{']) if not warnings else collections.deque()
                procedure_namespace = []
                while True:
                    current_namespace_line = next(self.token_list, None)

                    if not current_namespace_line:
                        raise mylang_errors.ReachedEndOfProcedureBlock("Expecting a close bracket for procedure '{}'".format(possible_name.value.value))
                    new_namespace_line = [i for i in current_namespace_line]


                    if any(i.type == 'OBRACKET' for i in new_namespace_line):
                        current_stack.append('{')
                        procedure_namespace.append(new_namespace_line)
                    if any(i.type == 'CBRACKET' for i in new_namespace_line):
                        if not current_stack:
                            raise mylang_errors.InvalidStartOfProcedureBlock("Missing '{' for start of scope of procedure '{}'".format(possible_name.value.value))
                        val = current_stack.pop()
                        if not current_stack:
                            break
                    else:
                        procedure_namespace.append(new_namespace_line)


                self.scopes[possible_name.value.value] = Scope(possible_name.value.value, [], [], current_namespace = {'param_num':len(function_params)})
                self.scopes[possible_name.value.value].scopes['signature'] = Scope('Signature', [], [], current_namespace = {'parameters':', '.join(i if not isinstance(i, list) else i[0] for i in function_params), 'types':', '.join('{}:{}'.format(i, None) if not isinstance(i, list) else "{}:{}".format(i[0], i[1]) for i in function_params)})
                self.procedures[possible_name.value.value] = Procedure(possible_name.value.value, function_params, procedure_namespace)
            if start.type == 'SCOPE':
                params, name, flags = self.parse_scope(start, current_line, self.token_list)

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

                        return operation_converters[last_seen.type](scope_result, final_part)
                    except:
                        raise mylang_errors.IncompatableTypes("Cannot {} value of type '{}' to type '{}'".format({'PLUS':'contactinate', 'BAR':'subtract', 'STAR':'multiply', 'FORWARDSLASH':'divide'}[last_seen.type], type(scope_result).__name__, type(final_part).__name__))

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
        self.procedures = Procedures()
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
        self.procedures = Procedures()
        self.scopes = Scopes()
        self.parse()
        print(self.variables)

    @mylang_wrappers.verify_procedure_parameter(valid_return_types = config.ALLOWED_RETURN_TYPES, max_param_val = config.MAX_PARAMS)
    def parse_procedure_header(self, header_line, current = []):

        current_t = next(header_line, None)

        if not current_t:
            raise mylang_errors.InvalidEndOfDeclaration("Reached invalid end of procedure declaration")
        if current_t.type == 'CPAREN':
            second = next(header_line, None)
            if not second:

                return current, mylang_warnings.NoHeaderSeen, None
            current_t.value.isValid(second.value)
            if second.type == 'OBRACKET':
                print 'returning here'
                return current, None, None
            if second.type == 'TORETURN':
                final_check = next(header_line, None)
                if not final_check:
                    raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': a return type must be specified".format(second.value.line_number, second.value.value))
                last_check = next(header_line, None)
                if not last_check:
                    print 'returning here'
                    return current, mylang_warnings.NoHeaderSeen, final_check.value.value
                final_check.value.isValid(last_check.value)
                print 'returning here'
                return current, None, final_check.value.value
        if current_t.type == 'VARIABLE':
            check_next = next(header_line, None)
            if not check_next:
                raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}', rearched invalid end of procedure declaration".format(current_t.value.line_number, current_t.value.value))
            current_t.value.isValid(check_next.value)
            if check_next.type == 'PLUS':
                raise mylang_errors.NotYetSupportedError("At line {}, near '{}': feature not yet supported".format(check_next.value.line_number, check_next.value.value))
                '''
                checking_next_val = next(header_line, None)
                if not checking_next_val:
                    raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': expecting close paren or parameter specification type".format(final_check.value.line_number, final_check.value.value))
                if checking_next_val.type == 'COLON':
                    testing_third = next(header_line, None)
                    if not testing_third:
                        raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': expecting close paren or parameter specification type".format(checking_next_val.line_number, checking_next_val.value.value))
                    testing_second_last = next(header_line, None)
                    if not testing_second:
                        raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': expecting close paren or parameter specification type".format(testing_third.line_number, testing_third.value.value))
                    if testing_second_last.type == 'CPAREN':
                        '''
            if check_next.type == 'CPAREN':
                current.append(current_t.value.value)
                final_check = next(header_line, None)
                if not final_check:
                    return current, mylang_warnings.NoHeaderSeen, None
                check_next.value.isValid(final_check.value)
                if final_check.type == 'OBRACKET':
                    return current, None, None

                if final_check.type == 'TORETURN':
                    return_type = next(header_line, None)
                    if not return_type:
                        raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '->': expecting a return type".format(final_check.value.line_number))
                    final_bracket = next(header_line, None)
                    if not final_bracket:
                        return current, mylang_warnings.NoHeaderSeen, return_type.value.value
                    return current, None, return_type.value.value
            if check_next.type == 'COMMA':
                return self.parse_procedure_header(header_line, current+[current_t.value.value])
            if check_next.type == 'COLON':
                testing_second = next(header_line, None)
                if not testing_second:
                    raise mylang_errors.InvalidEndOfDeclaration("At line {}, near {}: reached invalid end of procedure declaration".format(check_next.value.line_number, check_next.value.value))
                check_next.value.isValid(testing_second.value)
                final_check = next(header_line, None)
                if not final_check:
                    raise mylang_errors.InvalidEndOfDeclaration("At line {}, near {}: reached invalid end of procedure declaration".format(check_next.value.line_number, check_next.value.value))

                testing_second.value.isValid(final_check.value)
                #print 'last here', testing_second.value, final_check.value

                if final_check.type == 'COMMA':
                    return self.parse_procedure_header(header_line, current+[[current_t.value.value, testing_second.value.value]])
                if final_check.type == 'CPAREN':
                    checking_final_val = next(header_line, None)
                    if not checking_final_val:
                        current.append([current_t.value.value, testing_second.value.value])
                        return current, mylang_warnings.NoHeaderSeen, None
                    final_check.value.isValid(checking_final_val.value)
                    if checking_final_val.type == 'OBRACKET':
                        current.append([current_t.value.value, testing_second.value.value])
                        return current, None, None
                    if checking_final_val.type == 'TORETURN':
                        last_final_check = next(header_line, None)
                        if not last_final_check:
                            raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '->': must specify a return type".format(checking_final_val.value.line_number))
                        last_check_1 = next(header_line, None)
                        current.append([current_t.value.value, testing_second.value.value])
                        if not last_check_1:
                            return current, mylang_warnings.NoHeaderSeen, last_final_check.value.value

                        return current, None, last_final_check.value.value

    @mylang_wrappers.check_existence()
    def variable_exists(self, var):
        if var.value.value not in self.variables:
            raise mylang_errors.VariableNotDeclared("At line {}, near '{}': variable '{}' not declared".format(var.value.line_number, var.value.value, var.value.value))
        return self.variables[var.value.value]
    def parse_expression(self, line):
        operation_converters = {'PLUS':lambda x, y:x+y, 'BAR':lambda x,y:x-y, 'STAR':lambda x, y:x*y, 'FORWARDSLASH':lambda x, y:x/y}
        current = next(line, None)
        if not current:
            return None
        if current.type == 'VARIABLE':
            next_val = next(line, None)
            if not next_val or next_val.type == 'COMMA' or next_val.type == 'CPAREN':
                return self.variable_exists(current)
            current.value.isValid(next_val.value)
            if next_val.type not in operation_converters:
                raise mylang_errors.IllegialPrecedence("At line {}, near '{}': expecting a mutating operator (+|-|/|*|%)".format(next_val.value.line_number, next_val.value.value))
            returned_val = self.parse_expression(line)
            if type(self.variables[current.value.value]) != type(returned_val):
                raise mylang_errors.IncompatableTypes("At line {}, near '{}': cannot {} variable of type '{}' to type '{}'".format(current.value.line_number, current.value.value, {'PLUS':'concatinate', 'BAR':'subtract', 'STAR':'multiply', 'FORWARDSLASH':'divide'}[next_val.type], type(self.variables[current.value.value]).__name__, type(returned_val).__name__))
            return operation_converters[next_val.type](self.variables[current.value.value], returned_val)
        if current.type == 'DIGIT':
            next_val = next(line, None)
            if not next_val or next_val.type == 'COMMA' or next_val.type == 'CPAREN':
                return int(current.value.value)
            current.value.isValid(next_val.value)
            return_val = self.parse_expression(line)
            if not isinstance(return_val, int):
                raise mylang_errors.IncompatableTypes("At line {}, near '{}': cannot {} variable of type '{}' to type '{}'".format(current.value.line_number, current.value.value, {'PLUS':'concatinate', 'BAR':'subtract', 'STAR':'multiply', 'FORWARDSLASH':'divide'}[next_val.type], type(self.variables[current.value.value]).__name__, type(return_val).__name__))
            return operation_converters[next_val.type](int(current.value.value), return_val)
        if current.type == 'STRING':
            next_val = next(line, None)
            if not next_val or next_val.type == 'COMMA' or next_val.type == 'CPAREN':
                return current.value.value[1:-1]
            return_val = self.parse_expression(line)
            if not isinstance(return_val, str):
                raise mylang_errors.IncompatableTypes("At line {}, near '{}': cannot {} variable of type '{}' to type '{}'".format(current.value.line_number, current.value.value, {'PLUS':'concatinate', 'BAR':'subtract', 'STAR':'multiply', 'FORWARDSLASH':'divide'}[next_val.type], type(self.variables[current.value.value]).__name__, type(return_val).__name__))
            if next_val.type == "PLUS":
                return current.value.value[1:-1] + return_val
        raise mylang_errors.NotYetSupportedError("Operation not yet supported")

    def parse(self):
        current_line = next(self.token_list, None)

        if current_line:
            current_line, self.current_line_on = itertools.tee(current_line)
            tracing.add_top_level(self.current_line_on)
            start = next(current_line)
            if start.type == 'VARIABLE':
                checking = next(current_line)
                start.value.isValid(checking.value)
                if checking.type == 'OPAREN':
                    full_params = []
                    current_param = next(current_line, None)
                    if not current_param:
                        raise mylang_errors.ParameterSytnaxError("At line {}, near '{}': invalid parameter syntax".format(checking.value.line_number, checking.value.value))
                    checking.value.isValid(current_param.value)
                    if current_param.type == 'CPAREN':
                        result, namespace = self.procedures[start.value.value]()
                        #check for truthiness of function __call__ returned values
                        print 'result is', result, 'namespace is', namespace
                    else:
                        current_line = iter([current_param]+[i for i in current_line])
                        while True:
                            returned_expresssion = self.parse_expression(current_line)
                            full_params.append(returned_expresssion)
                            checking_last = next(current_line, None)
                            if not checking_last:
                                break
                            current_line = iter([checking_last]+[i for i in current_line])
                        print "final params here", full_params

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


                    self.scopes[path[0]].update_vals(list(path)[1:], to_assign)



            if start.type == 'GLOBAL':
                next_start = next(current_line, None)

                if not next_start:
                    raise mylang_errors.InvalidEndOfDeclaration("At line {}, near 'global', expecting scope or procedure declaration".format(start.value.line_number))
                start.value.isValid(next_start.value)
                if next_start.type == 'TRANSMUTE':
                    next_start_1 = next(current_line, None)
                    if not next_start_1:
                        raise mylang_errors.InvalidEndOfDeclaration("At line {}, near 'global', expecting scope or procedure declaration".format(next_start.value.line_number))
                    if next_start_1.type == 'PROCEDURE':
                        possible_name = next(current_line, None)
                        self.possible_name = possible_name
                        if not possible_name:
                            raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': expecting a scope or procedure declaration".format(next_start_1.value.line_number, next_start_1.value.value))
                        next_start_1.value.isValid(possible_name.value)
                        possible_start = next(current_line, None)
                        if not possible_start:
                            raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': expecting a scope or procedure declaration".format(next_start_1.value.line_number, possible_name.value.value))
                        possible_name.value.isValid(possible_start.value)
                        function_params, warnings, return_type = self.parse_procedure_header(current_line)
                        print "procedure name is: {}, params are: {}, warnings include: {}, return_type is {}".format(possible_name.value.value, function_params, warnings, return_type)
                        print "procedure name is: {}, params are: {}, warnings include: {}, return_type is {}".format(possible_name.value.value, function_params, warnings, return_type)
                        current_stack = collections.deque(['{']) if not warnings else collections.deque()
                        procedure_namespace = []
                        while True:
                            current_namespace_line = next(self.token_list, None)

                            if not current_namespace_line:
                                raise mylang_errors.ReachedEndOfProcedureBlock("Expecting a close bracket for procedure '{}'".format(possible_name.value.value))
                            new_namespace_line = [i for i in current_namespace_line]


                            if any(i.type == 'OBRACKET' for i in new_namespace_line):
                                current_stack.append('{')
                                procedure_namespace.append(new_namespace_line)
                            if any(i.type == 'CBRACKET' for i in new_namespace_line):
                                if not current_stack:
                                    raise mylang_errors.InvalidStartOfProcedureBlock("Missing '{' for start of scope of procedure '{}'".format(possible_name.value.value))
                                val = current_stack.pop()
                                if not current_stack:
                                    break
                            else:
                                procedure_namespace.append(new_namespace_line)


                        self.scopes[possible_name.value.value] = Scope(possible_name.value.value, [], [], current_namespace = {'param_num':len(function_params)})
                        self.scopes[possible_name.value.value].scopes['signature'] = Scope('Signature', [], [], current_namespace = {'parameters':', '.join(i if not isinstance(i, list) else i[0] for i in function_params), 'types':', '.join('{}:{}'.format(i, None) if not isinstance(i, list) else "{}:{}".format(i[0], i[1]) for i in function_params)})
                        self.procedures[possible_name.value.value] = Procedure(possible_name.value.value, function_params, procedure_namespace, can_mutate = True, current_namespace = self.variables)
                if next_start.type == 'PROCEDURE':
                    possible_name = next(current_line, None)
                    self.possible_name = possible_name
                    if not possible_name:
                        raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': expecting a scope or procedure declaration".format(next_start.value.line_number, next_start.value.value))
                    next_start.value.isValid(possible_name.value)
                    possible_start = next(current_line, None)
                    if not possible_start:
                        raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': expecting a scope or procedure declaration".format(next_start.value.line_number, possible_name.value.value))
                    possible_name.value.isValid(possible_start.value)
                    function_params, warnings, return_type = self.parse_procedure_header(current_line)
                    print "procedure name is: {}, params are: {}, warnings include: {}, return_type is {}".format(possible_name.value.value, function_params, warnings, return_type)
                    current_stack = collections.deque(['{']) if not warnings else collections.deque()
                    procedure_namespace = []
                    while True:
                        current_namespace_line = next(self.token_list, None)

                        if not current_namespace_line:
                            raise mylang_errors.ReachedEndOfProcedureBlock("Expecting a close bracket for procedure '{}'".format(possible_name.value.value))
                        new_namespace_line = [i for i in current_namespace_line]


                        if any(i.type == 'OBRACKET' for i in new_namespace_line):
                            current_stack.append('{')
                            procedure_namespace.append(new_namespace_line)
                        if any(i.type == 'CBRACKET' for i in new_namespace_line):
                            if not current_stack:
                                raise mylang_errors.InvalidStartOfProcedureBlock("Missing '{' for start of scope of procedure '{}'".format(possible_name.value.value))
                            val = current_stack.pop()
                            if not current_stack:
                                break
                        else:
                            procedure_namespace.append(new_namespace_line)


                    self.scopes[possible_name.value.value] = Scope(possible_name.value.value, [], [], current_namespace = {'param_num':len(function_params)})
                    self.scopes[possible_name.value.value].scopes['signature'] = Scope('Signature', [], [], current_namespace = {'parameters':', '.join(i if not isinstance(i, list) else i[0] for i in function_params), 'types':', '.join('{}:{}'.format(i, None) if not isinstance(i, list) else "{}:{}".format(i[0], i[1]) for i in function_params)})
                    self.procedures[possible_name.value.value] = Procedure(possible_name.value.value, function_params, procedure_namespace, current_namespace = self.variables)
                if next_start.type == 'SCOPE':
                    params, name, flags = self.parse_scope(next_start, current_line, self.token_list)

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
                    self.scopes[name] = Scope(name, scope_block, params, current_namespace = self.variables)
            if start.type == 'PROCEDURE':
                possible_name = next(current_line, None)
                self.possible_name = possible_name
                if not possible_name:
                    raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': expecting a scope or procedure declaration".format(start.value.line_number, start.value.value))
                start.value.isValid(possible_name.value)
                possible_start = next(current_line, None)
                if not possible_start:
                    raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': expecting a scope or procedure declaration".format(start.value.line_number, possible_name.value.value))
                possible_name.value.isValid(possible_start.value)
                function_params, warnings, return_type = self.parse_procedure_header(current_line)
                print "procedure name is: {}, params are: {}, warnings include: {}, return_type is {}".format(possible_name.value.value, function_params, warnings, return_type)
                current_stack = collections.deque(['{']) if not warnings else collections.deque()
                procedure_namespace = []
                while True:
                    current_namespace_line = next(self.token_list, None)

                    if not current_namespace_line:
                        raise mylang_errors.ReachedEndOfProcedureBlock("Expecting a close bracket for procedure '{}'".format(possible_name.value.value))
                    new_namespace_line = [i for i in current_namespace_line]


                    if any(i.type == 'OBRACKET' for i in new_namespace_line):
                        current_stack.append('{')
                        procedure_namespace.append(new_namespace_line)
                    if any(i.type == 'CBRACKET' for i in new_namespace_line):
                        if not current_stack:
                            raise mylang_errors.InvalidStartOfProcedureBlock("Missing '{' for start of scope of procedure '{}'".format(possible_name.value.value))
                        val = current_stack.pop()
                        if not current_stack:
                            break
                    else:
                        procedure_namespace.append(new_namespace_line)


                self.scopes[possible_name.value.value] = Scope(possible_name.value.value, [], [], current_namespace = {'param_num':len(function_params)})
                self.scopes[possible_name.value.value].scopes['signature'] = Scope('Signature', [], [], current_namespace = {'parameters':', '.join(i if not isinstance(i, list) else i[0] for i in function_params), 'types':', '.join('{}:{}'.format(i, None) if not isinstance(i, list) else "{}:{}".format(i[0], i[1]) for i in function_params)})
                self.procedures[possible_name.value.value] = Procedure(possible_name.value.value, function_params, procedure_namespace)
            if start.type == 'SCOPE':
                params, name, flags = self.parse_scope(start, current_line, self.token_list)

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

                self.scopes[name] = Scope(name, scope_block, params)

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
            if not test_final or test_final.type == 'COMMA' or test_final.type == 'CPAREN':
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

                        return operation_converters[last_seen.type](scope_result, final_part)
                    except:
                        raise mylang_errors.IncompatableTypes("Cannot {} value of type '{}' to type '{}'".format({'PLUS':'contactinate', 'BAR':'subtract', 'STAR':'multiply', 'FORWARDSLASH':'divide'}[last_seen.type], type(scope_result).__name__, type(final_part).__name__))

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



Parser(mylang_tokenizer.Tokenize('mylang1.txt').tokenized_data)
