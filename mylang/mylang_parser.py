import mylang_tokenizer
import collections
import mylang_errors
import string
from mylang_config import config, ImportAll, ObjectifyImport
import mylang_warnings
import functools
import copy
import datetime
import itertools
import trace_parser
import mylang_wrappers
import mylang_builtins
import re
import os
#IDEA: conda programming language!

class ArrayList:
    def __init__(self, line, **namespace):
        self.line = line
        self.contents = namespace.get('filled', [])
        self.rep = 'ArrayList'
        self.variables = namespace.get('variables', {})
        self.procedures = namespace.get('procedures', Procedures())
        self.scopes = namespace.get('scopes', Scopes())
        if not namespace.get('filled', []):
            self.parse()
    def __contains__(self, val):
        return all(i in self.contents for i in getattr(val, 'contents', [val]))
    def __len__(self):
        return len(self.contents)
    def __bool__(self):
        return len(self.contents) > 0
    def __iter__(self):
        for i in self.contents:
            yield i
    def add_to_back(self, val):
        self.contents.append(val)
    def add_to_front(self, val):
        self.contents = [val]+self.contents
    def extendBack(self, arraylist_object):
        self.contents.extend(arraylist_object.contents)
    def extendFront(self, arraylist_object):
        self.contents = arraylist_object.contents + self.contents
    def __delitem__(self, val):
        del self.contents[val]

    def remove_val_at(self, val):
        self.contents = [i for i in self.contents if i != val]
    @property
    def reverse_contents(self):
        return ArrayList([], filled=self.contents[::-1])
    def __getitem__(self, val):
        if not isinstance(val, int):
            return self.contents[val.start:val.stop]
        return self.contents[val]
    def __setitem__(self, val, target):
        if not isinstance(val, int):
            self.contents[val.start:val.stop] = target
        else:
            self.contents[val] = target
    def parse(self):
        current = next(self.line, None)
        if not current:
            raise mylang_errors.InvalidSyntax('Expecting closing bracket')
        self.line = iter([current]+[i for i in self.line])
        while True:
            check_current = next(self.line, None)
            print 'check_current 1', check_current
            #print 'check_current', check_current
            if not check_current or check_current.type == 'CBRACKET':
                break
            if check_current.type == 'OBRACKET':

                new_listing = ArrayList(self.line)
                self.contents.append(new_listing)
                self.line = new_listing.line


            else:
                self.line = iter([check_current]+[i for i in self.line]) if check_current and check_current.type != 'COMMA' else self.line
                check_final = next(self.line, None)
                if not check_final:
                    raise InvalidSyntax("Expecting a close bracket '}'")
                if check_final.type == 'OBRACKET':
                    new_listing = ArrayList(self.line)
                    self.contents.append(new_listing)
                    self.line = new_listing.line
                else:
                    self.line = iter([check_final]+[i for i in self.line])
                    val = self.parse_expression(self.line)

                    check_next_test = next(self.line, None)
                    if not check_next_test:
                        raise mylang_errors.InvalidSyntax('Expecting closing bracket')
                    if check_next_test.type != 'COMMA':
                        self.line = iter([check_next_test]+[i for i in self.line])

                    self.contents.append(val)

    @mylang_wrappers.check_existence()
    def variable_exists(self, var):
        if var.value.value not in self.variables:
            if var.value.value not in self.scopes:
                raise mylang_errors.VariableNotDeclared("At line {}, near '{}': variable '{}' not declared".format(var.value.line_number, var.value.value, var.value.value))
            return self.scopes[var.value.value]
        return self.variables[var.value.value]

    def parse_expression(self, line):
        operation_converters = {'PLUS':lambda x, y:x+y, 'BAR':lambda x,y:x-y, 'STAR':lambda x, y:x*y, 'FORWARDSLASH':lambda x, y:x/y}
        current = next(line, None)
        print 'current here', current
        #print 'current here', current
        if not current:
            return None
        if current.type == 'VARIABLE':
            next_val = next(line, None)
            if not next_val or next_val.type == 'COMMA' or next_val.type == 'CPAREN' or next_val.type == 'CBRACKET':
                self.line = iter([next_val]+[i for i in line])
                return self.variable_exists(current)
            current.value.isValid(next_val.value)

            if next_val.type == 'OPAREN':
                check_next_v = next(line, None)
                if not check_next_v:
                    raise mylang_errors.ParameterSytnaxError("At line {}, near '{}': reached unexpected end of procedure call".format(current.value.line_number, current.value.value))
                if check_next_v.type == 'CPAREN':
                    if current.value.value not in self.procedures:
                        raise mylang_errors.AttributeNotFound("At line {}, near '{}': procedure '{}' not found".format(current.value.line_number, current.value.value, current.value.value))
                    result, namespace = self.procedures[current.value.value]()
                    self.variables = namespace if namespace else self.variables
                    check_last_v = next(line, None)
                    if check_last_v.type in ['COMMA', 'CPAREN', 'CBRACKET']:
                        self.line = iter([check_last_v]+[i for i in line])
                        return result
                    if check_last_v.type in operation_converters:
                        final_result = self.parse_expression(line)
                        if type(result) != type(final_result):
                            raise mylang_errors.IncompatableTypes("At line {}, near '{}' cannot {} value of type '{}' to type '{}'".format(check_last_v.value.line_number, check_last_v.value.value, {'PLUS':'concatinate', 'BAR':'subtract', 'STAR':'multiply', 'FORWARDSLASH':'divide'}[check_last_v.type], type(result).__name__, type(final_result).__name__))
                        return operation_converters[check_last_v.type](result, final_result)
                if current.value.value not in self.procedures:
                    raise mylang_errors.VariableNotDeclared("At line {}: procedure '{}' not declared".format(current.value.line_number, current.value.value))
                self.line = iter([check_next_v]+[i for i in line])
                params = []
                while True:
                    current_param = self.parse_expression(line)
                    can_continue = next(line, None)
                    params.append(current_param)
                    if not can_continue or can_continue.type == 'CPAREN':
                        break
                    self.line = iter([can_continue]+[i for i in line])
                print 'PARAMS HERE', params
                result, namespace = self.procedures[current.value.value](*params)
                self.variables = namespace if namespace else self.variables
                checking_next_v = next(line, None)
                if not checking_next_v or checking_next_v.type in ['COMMA', 'CPAREN', 'CBRACKET']:
                    self.line = iter([checking_next_v]+[i for i in line])
                    return result
                if checking_next_v.type in operation_converters:
                    returned_result = self.parse_expression(line)
                    if type(result) != type(returned_result):
                        raise mylang_errors.IncompatableTypes("At line {}, near '{}' cannot {} value of type '{}' to type '{}'".format(checking_next_v.value.line_number, checking_next_v.value.value, {'PLUS':'concatinate', 'BAR':'subtract', 'STAR':'multiply', 'FORWARDSLASH':'divide'}[checking_next_v.type], type(result).__name__, type(returned_result).__name__))
                    return operation_converters[checking_next_v.type](result, returned_result)
            if next_val.type == 'DOT':
                path = [current.value.value]

                seen_operator = False
                while True:
                    current_attr = next(line, None)
                    if not current_attr:
                        raise mylang_errors.InvalidAttributeCall("At line {}, near '{}'".format(next_val.value.line_number, next_val.value.value))
                    if current_attr.type == 'VARIABLE':

                        checking_next = next(line, None)
                        if not checking_next:
                            path.append(current_attr.value.value)
                            break
                        current_attr.value.isValid(checking_next.value)
                        path.append(current_attr.value.value)
                        if checking_next.type == 'OPAREN':

                            method_params = []
                            while True:
                                current_param = self.parse_expression(line)
                                method_params.append(current_param)
                                check_next_final = next(line, None)

                                if not check_next_final or check_next_final.type == "CPAREN" or check_next_final.type == 'COMMA':

                                    break

                                self.line = iter([check_next_final]+[i for i in line])

                            current_scope_selection = self.scopes if path[0] not in self.variables else self.variables
                            path = list(path)
                            the_method = path[-1]
                            copy_path = list(copy.deepcopy(path))
                            start = path[0]
                            path = path[:-1]
                            while path:
                                current_scope_selection = current_scope_selection[path[0]]
                                path = path[1:]
                            Scope.private_procedure_check(current_scope_selection.procedures[the_method])
                            to_return, namespace = current_scope_selection.procedures[the_method](*method_params)
                            base = self.scopes if start not in self.variables else self.variables
                            base[start].update_namespace(copy_path, namespace, start=start, end=copy_path[-1])
                            return to_return
                        if checking_next.type in operation_converters or checking_next.type == 'CPAREN' or checking_next.type == 'COMMA' or checking_next.type == 'CBRACKET':
                            seen_operator = None if (checking_next.type == 'CPAREN' or checking_next.type == 'COMMA' or checking_next.type == 'CBRACKET') else checking_next.type
                            self.line = iter([checking_next]+[i for i in line])
                            break

                start_scope = path[0]
                flag = False
                if start_scope not in self.scopes:
                    if start_scope not in self.variables:
                        raise mylang_errors.VariableNotDeclared("Scope '{}' not declared".format(start_scope))
                    flag = True
                current_value_attr = self.scopes if not flag else self.variables
                while path:
                    try:
                        new_val = current_value_attr[path[0]]
                        print 'in try block', new_val
                    except:
                        if path[0] not in current_value_attr.scopes:
                            raise mylang_errors.AttributeNotFound("At line {}, near '{}':scope '{}' has no attribute '{}'".format(current_attr.value.line_number, current_attr.value.value, start_scope, path[0]))
                        current_value_attr = current_value_attr.scopes[path[0]]
                        path = path[1:]
                    else:
                        current_value_attr = new_val
                        path = path[1:]
                if seen_operator:
                    returned_val = self.parse_expression(line)
                    if type(current_value_attr) != type(returned_val):
                        raise mylang_errors.IncompatableTypes("At line {}, near '{}': cannot {} value of type '{}' to type '{}'".format(current_attr.value.line_number, current_attr.value.value, {'PLUS':'concatinate', 'BAR':'subtract', 'STAR':'multiply', 'FORWARDSLASH':'divide'}[seen_operator], type(current_value_attr).__name__, type(returned_val).__name__))
                    return operation_converters[seen_operator](current_value_attr, returned_val)

                return current_value_attr
            returned_val = self.parse_expression(line)
            if type(self.variables[current.value.value]) != type(returned_val):
                raise mylang_errors.IncompatableTypes("At line {}, near '{}': cannot {} variable of type '{}' to type '{}'".format(current.value.line_number, current.value.value, {'PLUS':'concatinate', 'BAR':'subtract', 'STAR':'multiply', 'FORWARDSLASH':'divide'}[next_val.type], type(self.variables[current.value.value]).__name__, type(returned_val).__name__))
            return operation_converters[next_val.type](self.variables[current.value.value], returned_val)
        if current.type == 'DIGIT':
            next_val = next(line, None)
            if not next_val or next_val.type == 'COMMA' or next_val.type == 'CPAREN' or next_val.type == 'CBRACKET':

                self.line = iter([next_val]+[i for i in line])
                return int(current.value.value)
            current.value.isValid(next_val.value)
            return_val = self.parse_expression(line)
            if not isinstance(return_val, int):
                raise mylang_errors.IncompatableTypes("At line {}, near '{}': cannot {} variable of type '{}' to type '{}'".format(current.value.line_number, current.value.value, {'PLUS':'concatinate', 'BAR':'subtract', 'STAR':'multiply', 'FORWARDSLASH':'divide'}[next_val.type], type(self.variables[current.value.value]).__name__, type(return_val).__name__))
            return operation_converters[next_val.type](int(current.value.value), return_val)
        if current.type == 'STRING':
            next_val = next(line, None)
            if not next_val or next_val.type == 'COMMA' or next_val.type == 'CPAREN' or next_val.type == 'CBRACKET':

                self.line = iter([next_val]+[i for i in self.line])
                return current.value.value[1:-1]
            return_val = self.parse_expression(line)
            if not isinstance(return_val, str):
                raise mylang_errors.IncompatableTypes("At line {}, near '{}': cannot {} variable of type '{}' to type '{}'".format(current.value.line_number, current.value.value, {'PLUS':'concatinate', 'BAR':'subtract', 'STAR':'multiply', 'FORWARDSLASH':'divide'}[next_val.type], type(current.value.value).__name__, type(return_val).__name__))
            if next_val.type == "PLUS":
                return current.value.value[1:-1] + return_val
        raise mylang_errors.NotYetSupportedError("Operation not yet supported")

    def __repr__(self):
        return str(self)
    def __str__(self):
        return '{}({})'.format(self.__class__.__name__, str(self.contents))
class Procedure:
    def __init__(self, name, parameters, namespace, **kwargs):
        self.variables = kwargs.get('current_namespace') if kwargs.get('current_namespace') else {}
        self.is_global = bool(kwargs.get('current_namespace'))
        self.scopes = {}
        self.is_private = kwargs.get('is_private', False)
        self.return_type = kwargs.get('return_type')
        self.name = name
        #print 'in constructor for procedure {name} with visibility of {is_private}'.format(**self.__dict__)
        self.procedures = Procedures()
        if kwargs.get('current_namespace_procedures'):
            print 'IN HERE WITH NEW PROCEDURES', kwargs.get('current_namespace_procedures')
            self.procedures.update_procedures(kwargs.get('current_namespace_procedures'))
        #self.procedures[self.name] =
        self.to_return = []
        self.check_namespace_copy = copy.deepcopy(namespace)
        self.token_list = iter(map(iter, namespace))
        self.params = parameters
        #print 'parameters for {name}'.format(**self.__dict__), self.params
        self.can_mutate = kwargs.get('can_mutate', False)
        #print 'self.can_mutate', self.can_mutate
        if not self.params:
            self.parse()

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

            if next_val.type == 'OPAREN':
                check_next_v = next(line, None)
                if not check_next_v:
                    raise mylang_errors.ParameterSytnaxError("At line {}, near '{}': reached unexpected end of procedure call".format(current.value.line_number, current.value.value))
                if check_next_v.type == 'CPAREN':
                    if current.value.value not in self.procedures:
                        raise mylang_errors.AttributeNotFound("At line {}, near '{}': procedure '{}' not found".format(current.value.line_number, current.value.value, current.value.value))
                    result, namespace = self.procedures[current.value.value]()
                    self.variables = namespace if namespace else self.variables
                    check_last_v = next(line, None)
                    if check_last_v.type in ['COMMA', 'CPAREN']:
                        return result
                    if check_last_v.type in operation_converters:
                        final_result = self.parse_expression(line)
                        if type(result) != type(final_result):
                            raise mylang_errors.IncompatableTypes("At line {}, near '{}' cannot {} value of type '{}' to type '{}'".format(check_last_v.value.line_number, check_last_v.value.value, {'PLUS':'concatinate', 'BAR':'subtract', 'STAR':'multiply', 'FORWARDSLASH':'divide'}[check_last_v.type], type(result).__name__, type(final_result).__name__))
                        return operation_converters[check_last_v.type](result, final_result)
                if current.value.value not in self.procedures:
                    raise mylang_errors.VariableNotDeclared("At line {}: procedure '{}' not declared".format(current.value.line_number, current.value.value))
                line = iter([check_next_v]+[i for i in line])
                params = []
                while True:
                    current_param = self.parse_expression(line)
                    can_continue = next(line, None)
                    params.append(current_param)
                    if not can_continue or can_continue.type == 'CPAREN':
                        break
                    line = iter([can_continue]+[i for i in line])
                print 'PARAMS HERE', params
                result, namespace = self.procedures[current.value.value](*params)
                self.variables = namespace if namespace else self.variables
                checking_next_v = next(line, None)
                if not checking_next_v or checking_next_v.type in ['COMMA', 'CPAREN']:
                    return result
                if checking_next_v.type in operation_converters:
                    returned_result = self.parse_expression(line)
                    if type(result) != type(returned_result):
                        raise mylang_errors.IncompatableTypes("At line {}, near '{}' cannot {} value of type '{}' to type '{}'".format(checking_next_v.value.line_number, checking_next_v.value.value, {'PLUS':'concatinate', 'BAR':'subtract', 'STAR':'multiply', 'FORWARDSLASH':'divide'}[checking_next_v.type], type(result).__name__, type(returned_result).__name__))
                    return operation_converters[checking_next_v.type](result, returned_result)
            if next_val.type == 'DOT':
                path = [current.value.value]

                seen_operator = False
                while True:
                    current_attr = next(line, None)
                    if not current_attr:
                        raise mylang_errors.InvalidAttributeCall("At line {}, near '{}'".format(next_val.value.line_number, next_val.value.value))
                    if current_attr.type == 'VARIABLE':

                        checking_next = next(line, None)
                        if not checking_next:
                            path.append(current_attr.value.value)
                            break
                        current_attr.value.isValid(checking_next.value)
                        path.append(current_attr.value.value)
                        if checking_next.type == 'OPAREN':

                            method_params = []
                            while True:
                                current_param = self.parse_expression(line)
                                method_params.append(current_param)
                                check_next_final = next(line, None)

                                if not check_next_final or check_next_final.type == "CPAREN" or check_next_final.type == 'COMMA':

                                    break

                                line = iter([check_next_final]+[i for i in line])

                            current_scope_selection = self.scopes if path[0] not in self.variables else self.variables
                            path = list(path)
                            the_method = path[-1]
                            copy_path = list(copy.deepcopy(path))
                            start = path[0]
                            path = path[:-1]
                            while path:
                                current_scope_selection = current_scope_selection[path[0]]
                                path = path[1:]
                            Scope.private_procedure_check(current_scope_selection.procedures[the_method])
                            to_return, namespace = current_scope_selection.procedures[the_method](*method_params)
                            base = self.scopes if start not in self.variables else self.variables
                            base[start].update_namespace(copy_path, namespace, start=start, end=copy_path[-1])
                            return to_return
                        if checking_next.type in operation_converters or checking_next.type == 'CPAREN' or checking_next.type == 'COMMA':
                            seen_operator = None if (checking_next.type == 'CPAREN' or checking_next.type == 'COMMA') else checking_next.type
                            break

                start_scope = path[0]
                flag = False
                if start_scope not in self.scopes:
                    if start_scope not in self.variables:
                        raise mylang_errors.VariableNotDeclared("Scope '{}' not declared".format(start_scope))
                    flag = True
                current_value_attr = self.scopes if not flag else self.variables
                while path:
                    try:
                        new_val = current_value_attr[path[0]]
                        print 'in try block', new_val
                    except:
                        if path[0] not in current_value_attr.scopes:
                            raise mylang_errors.AttributeNotFound("At line {}, near '{}':scope '{}' has no attribute '{}'".format(current_attr.value.line_number, current_attr.value.value, start_scope, path[0]))
                        current_value_attr = current_value_attr.scopes[path[0]]
                        path = path[1:]
                    else:
                        current_value_attr = new_val
                        path = path[1:]
                if seen_operator:
                    returned_val = self.parse_expression(line)
                    if type(current_value_attr) != type(returned_val):
                        raise mylang_errors.IncompatableTypes("At line {}, near '{}': cannot {} value of type '{}' to type '{}'".format(current_attr.value.line_number, current_attr.value.value, {'PLUS':'concatinate', 'BAR':'subtract', 'STAR':'multiply', 'FORWARDSLASH':'divide'}[seen_operator], type(current_value_attr).__name__, type(returned_val).__name__))
                    return operation_converters[seen_operator](current_value_attr, returned_val)

                return current_value_attr
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

    @mylang_wrappers.verify_procedure_parameter(valid_return_types = config.ALLOWED_RETURN_TYPES, max_param_val = config.MAX_PARAMS)
    def parse_procedure_header(self, header_line, current = None):
        current = [] if not current else current
        current_t = next(header_line, None)

        if not current_t:
            raise mylang_errors.InvalidEndOfDeclaration("Reached invalid end of procedure declaration")
        if current_t.type == 'CPAREN':
            second = next(header_line, None)
            if not second:

                return current, mylang_warnings.NoHeaderSeen, None
            current_t.value.isValid(second.value)
            if second.type == 'OBRACKET':
                #print 'returning here'
                return current, None, None
            if second.type == 'TORETURN':
                final_check = next(header_line, None)
                if not final_check:
                    raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': a return type must be specified".format(second.value.line_number, second.value.value))
                last_check = next(header_line, None)
                if not last_check:
                    #print 'returning here'
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
                        if start.value.value == self.name:
                            print 'GOt TO HERE'
                            result, namespace = self()
                        else:
                            result, namespace = self.procedures[start.value.value]()
                        #check for truthiness of function __call__ returned values

                        if result:
                            raise mylang_errors.InvalidProcedureReturn("At line {}, near '{}': procedure '{}' is not void".format(start.value.line_number, start.value.value, start.value.value))
                        if namespace:
                            self.variables = namespace
                    else:
                        current_line = iter([current_param]+[i for i in current_line])
                        while True:
                            returned_expresssion = self.parse_expression(current_line)
                            full_params.append(returned_expresssion)
                            checking_last = next(current_line, None)
                            if not checking_last:
                                break
                            current_line = iter([checking_last]+[i for i in current_line])
                        if start.value.value == self.name:

                            result, namespace = self(*full_params)
                        else:

                            result, namespace = self.procedures[start.value.value](*full_params)
                        if result:
                            raise mylang_errors.InvalidProcedureReturn("At line {}, near '{}': procedure '{}' is not void".format(start.value.line_number, start.value.value, start.value.value))
                        if namespace:
                            self.variables = namespace

                if checking.type == 'ASSIGN':
                    to_store = self.parse_assign(current_line)
                    #print 'To store here,', to_store, start.value.value
                    self.variables[start.value.value] = to_store

                    self.scopes[start.value.value] = Scope(start.value.value, [], [], current_namespace = dict([(i, getattr(to_store, i)()) for i in ['upper', 'lower', 'capitalize', 'isupper', 'islower']]+[('type', type(to_store).__name__)]) if isinstance(to_store, str) else dict([('increment', to_store+1), ('squared', pow(to_store, 2))]+[('type', 'int')]) if isinstance(to_store, int) else {'type':getattr(to_store, 'rep', type(to_store).__name__)}, builtins = mylang_builtins.builtin_methods[getattr(to_store, 'rep', type(to_store).__name__)])


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
                        self.procedures[possible_name.value.value] = Procedure(possible_name.value.value, function_params, procedure_namespace, can_mutate = True, current_namespace = self.variables, return_type = return_type, current_namespace_procedures = self.procedures)
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
                    temp_current_line = [i for i in current_line]

                    current_line = iter(temp_current_line)
                    function_params, warnings, return_type = self.parse_procedure_header(current_line)


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
                    self.procedures[possible_name.value.value] = Procedure(possible_name.value.value, function_params, procedure_namespace, current_namespace = self.variables, return_type = return_type, current_namespace_procedures = self.procedures)
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
                ##print 'CURRENT LINE FOR function {}'.format(possible_name.value.value), current_line

                function_params, warnings, return_type = self.parse_procedure_header(current_line)
                ##print 'CHECKING FUNCTION_PARAMS here for function {}'.format(possible_name.value.value), function_params
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
                self.procedures[possible_name.value.value] = Procedure(possible_name.value.value, function_params, procedure_namespace, return_type = return_type, current_namespace_procedures = self.procedures)
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

    def parse_scope_params(self, first, line, found = None):
        found = [] if not found else found
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
        if current.type == 'OBRACKET':

            return ArrayList(line, variables = self.variables, scopes = self.scopes, procedures = self.procedures)
        if current.type == 'VARIABLE':
            test_final = next(line, None)
            if not test_final or test_final.type == 'COMMA' or test_final.type == 'CPAREN':
                if current.value.value not in self.variables:
                    raise mylang_errors.VariableNotDeclared("At line {}, '{}' not declared".format(current.value.line_number, current.value.value))
                return self.variables[current.value.value]
            current.value.isValid(test_final.value)
            if test_final.type == 'OPAREN':
                test_second_line = next(line, None)
                if not test_second_line:
                    raise mylang_errors.InvalidSyntax("At line {}, near '{}': expecting a variable type or a close parenthesis ')'".format(test_final.value.line_number, test_final.value.value))
                test_final.value.isValid(test_second_line.value)
                if test_second_line.type == 'CPAREN':
                    if current.value.value == self.name:
                        to_return, namespace = self()
                    else:
                        to_return, namespace = self.procedures[current.value.value]()
                    if namespace:
                        self.variables.update(namespace)
                    return to_return
                line = iter([test_second_line]+[i for i in line])
                #currently, here
                if current.value.value in self.procedures or current.value.value == self.name:
                    print 'IN HEREQQQQ with procedure name ', current.value.value
                    testing_next = next(line, None)
                    if not testing_next:
                        raise mylang_errors.InvalidParameterType("At line {}: invalid syntax".format(current.value.line_number))
                    line = iter([testing_next]+[i for i in line])
                    function_params = []
                    while True:
                        current_param = self.parse_expression(line)
                        function_params.append(current_param)
                        checking_next_val = next(line, None)
                        if not checking_next_val:
                            break
                        line = iter([checking_next_val]+[i for i in line])
                    if current.value.value == self.name:
                        self.recursive_flag = True
                        result, namespace = self(*function_params)

                    else:
                        result, namespace = self.procedures[current.value.value](*function_params)

                    return result
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
                        if check.type == 'OPAREN':
                            check_next_val = next(line, None)
                            if not check_next_val:
                                raise mylang_errors.InvalidParameterType("At line {}, near '{}': expecting ')'".format(check.value.line_number, check.value.value))
                            if check_next_val.type == 'CPAREN':
                                current_scope_1 = self.scopes if path[0] not in self.variables else self.variables
                                path_copy = copy.deepcopy(list(path))
                                path = list(path)
                                while path:
                                    current_scope_1 = current_scope_1[path[0]]
                                    path = path[1:]

                                try:
                                    test = current_scope_1.procedures[temp_path.value.value]
                                except:
                                    if len(path_copy) == 1:
                                        print (path_copy, temp_path.value.value, current_scope_1)
                                        return self.scopes[path_copy[-1]].builtins[temp_path.value.value](path_copy[-1], current_scope_1)
                                    scope_object = self.scopes if path_copy[0] not in self.variables else self.variables

                                    while path_copy[:-1]:
                                        scope_object = scope_object[path_copy[0]]
                                        path_copy = path_copy[1:]

                                    return scope_object.scopes[path_copy[-1]].builtins[temp_path.value.value](path_copy[-1], current_scope_1)

                                Scope.private_procedure_check(current_scope_1.procedures[temp_path.value.value])
                                to_return, new_scope_namespace = current_scope_1.procedures[temp_path.value.value]()
                                self.scopes[path_copy[0]].update_namespace(path_copy, new_scope_namespace, start=path_copy[0], end=path_copy[-1])
                                return to_return
                            line = iter([check_next_val]+[i for i in line])
                            current_params_check = []
                            while True:
                                result_here_1 = self.parse_expression(line)

                                current_params_check.append(result_here_1)
                                check_next_4 = next(line, None)
                                if not check_next_4:
                                    break
                                line = iter([check_next_4]+[i for i in line])

                            #print 'current_params_check here for {}'.format(path[-1]), current_params_check

                            current_scope_1 = self.scopes if path[0] not in self.variables else self.variables
                            path_copy = copy.deepcopy(list(path))
                            path = list(path)
                            while path:
                                current_scope_1 = current_scope_1[path[0]]
                                path = path[1:]

                            try:
                                test = current_scope_1.procedures[temp_path.value.value]
                            except:
                                if len(path_copy) == 1:
                                    print (path_copy, temp_path.value.value, current_scope_1)
                                    return self.scopes[path_copy[-1]].builtins[temp_path.value.value](path_copy[-1], current_scope_1, *current_params_check)
                                scope_object = self.scopes if path_copy[0] not in self.variables else self.variables

                                while path_copy[:-1]:
                                    scope_object = scope_object[path_copy[0]]
                                    path_copy = path_copy[1:]

                                return scope_object.scopes[path_copy[-1]].builtins[temp_path.value.value](path_copy[-1], current_scope_1)
                            Scope.private_procedure_check(current_scope_1.procedures[temp_path.value.value])
                            to_return, new_scope_namespace = current_scope_1.procedures[temp_path.value.value](*current_params_check)
                            if to_return == []:
                                raise mylang_errors.InvalidProcedureReturnType("Procedure '{}' is void".format(temp_path.value.value))
                            self.scopes[path_copy[0]].update_namespace(path_copy, new_scope_namespace, start=path_copy[0], end=path_copy[-1])

                            return to_return
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
                start_scope = path[0]
                last_path_val = None
                if path[0] not in scope_result:
                    raise mylang_errors.AttributeNotFound("At line {}, near {}: variable '{}' has no attribute '{}'".format(current.value.line_number, current.value.value, current.value.value, path[1]))
                store_last = []
                string_last = []
                while path:
                    val = path.popleft()

                    try:
                        if val in scope_result:
                            scope_result = scope_result[val]
                            print 'scope_result for testing', scope_result
                        else:
                            if not path:
                                if val in store_last[-2].scopes[string_last[-1]]:
                                    print 'in here'
                                    print 'val', val

                                    scope_result = store_last[-2].scopes[string_last[-1]][val]
                                else:
                                    raise mylang_errors.AttributeNotFound("scope '{}' has no attribute '{}'".format(string_last[-1], val))
                            else:
                                scope_result = scope_result.scopes[val]
                        store_last.append(scope_result)
                        string_last.append(val)
                    except (IndexError, KeyError, TypeError, mylang_errors.AttributeNotFound):

                        pass
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
        return '{}({})'.format(self.__class__.__name__, 'name: {}, params: {}, global: {}, transmute:{} '.format(self.name, len(self.params), ['No', 'Yes'][self.is_global], ['No', 'Yes'][self.can_mutate]))
    def __str__(self):
        return repr(self)


    @mylang_wrappers.verify_parameter_arg_length(max_procedure_params=config.MAX_PROCEDURE_PARAMS)
    @mylang_wrappers.verify_passed_types
    def __call__(self, *args):
        self.check_namespace_copy = copy.deepcopy(self.check_namespace_copy)
        self.token_list = iter(map(iter, self.check_namespace_copy))
        #print self.check_namespace_copy if hasattr(self, 'recursive_flag') else 'no recursion yet'
        if args:

            self.variables.update(dict(zip([i if not isinstance(i, list) else i[0] for i in self.params], args)))
            for a, b in zip([i if not isinstance(i, list) else i[0] for i in self.params], args):
                #Scope(start.value.value, [], [], current_namespace = dict([(i, getattr(b, i)()) for i in ['upper', 'lower', 'capitalize', 'isupper', 'islower']]+[('type', type(b).__name__)]) if isinstance(b, str) else dict([('increment', b+1), ('squared', pow(b, 2)), ('type', type(b).__name__)]) if isinstance(b, int) else {'type':getattr(b, 'rep', type(b).__name__)}, builtins = mylang_builtins.builtin_methods[getattr(b, 'rep', type(b).__name__)])
                self.scopes[a] = Scope(a, [], [], current_namespace = dict([(i, getattr(b, i)()) for i in ['upper', 'lower', 'capitalize', 'isupper', 'islower']]+[('type', type(b).__name__)]) if isinstance(b, str) else dict([('increment', b+1), ('squared', pow(b, 2)), ('type', type(b).__name__)]) if isinstance(b, int) else {'type':getattr(b, 'rep', type(b).__name__)}, builtins = mylang_builtins.builtin_methods[getattr(b, 'rep', type(b).__name__)])
            self.parse()
        print 'self.to_return is storing', self.to_return
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
    def update_procedures(self, new_procedures):
        self.procedure_list.update(new_procedures.procedure_list)
    def __contains__(self, name):
        return name in self.procedure_list
    def __len__(self):
        return len(self.procedure_list)
    def __repr__(self):
        return "{}(<{} procedure{}>{})".format(self.__class__.__name__, len(self), 's' if len(self) != 1 else '', ', '.join('{}:{}'.format(a, str(b)) for a, b in self.procedure_list.items()))
class Scope:
    def __init__(self, name, namespace, params, **kwargs):
        self.procedures = Procedures()
        self.__scope_name__ = name
        self.params = params
        self.builtins = kwargs.get('builtins', {})
        #print 'builtins here for name {}'.format(name), self.builtins
        self.private_variables = []
        self.token_list = iter(map(iter, namespace))
        self.private_procedures = []
        self.scopes = {}
        self.seen_procedure_private = False
        self.date_created = datetime.datetime.now()
        self.variables = {'__params__':params, '__scope_name__':name, '__receipt__':"<object '{}' created on {} at {}(hh:mm:s)".format(self.__class__.__name__, '{}/{}/{}'.format(self.date_created.month, self.date_created.day, self.date_created.year), '{}:{}:{}'.format(self.date_created.hour, self.date_created.minute, self.date_created.second))}
        if kwargs.get('current_namespace', None):
            self.variables.update(kwargs.get('current_namespace'))
        if not len(params):

            self.parse()
    def __contains__(self, val):
        return val in self.variables

    @classmethod
    @mylang_wrappers.verify_private_procedure(suppress = config.PRIVATE_PROCEDURE_LEVEL)
    def private_procedure_check(cls, name):
        raise Exception("Something went wrong")

    def parse_expression(self, line):
        operation_converters = {'PLUS':lambda x, y:x+y, 'BAR':lambda x,y:x-y, 'STAR':lambda x, y:x*y, 'FORWARDSLASH':lambda x, y:x/y}
        current = next(line, None)
        print 'current last', current
        if not current:
            return None
        if current.type == 'VARIABLE':
            next_val = next(line, None)
            if not next_val or next_val.type == 'COMMA' or next_val.type == 'CPAREN':
                return self.variable_exists(current)
            current.value.isValid(next_val.value)

            if next_val.type == 'OPAREN':
                check_next_v = next(line, None)
                if not check_next_v:
                    raise mylang_errors.ParameterSytnaxError("At line {}, near '{}': reached unexpected end of procedure call".format(current.value.line_number, current.value.value))
                if check_next_v.type == 'CPAREN':
                    if current.value.value not in self.procedures:
                        raise mylang_errors.AttributeNotFound("At line {}, near '{}': procedure '{}' not found".format(current.value.line_number, current.value.value, current.value.value))
                    result, namespace = self.procedures[current.value.value]()
                    self.variables = namespace if namespace else self.variables
                    check_last_v = next(line, None)
                    if check_last_v.type in ['COMMA', 'CPAREN']:
                        return result
                    if check_last_v.type in operation_converters:
                        final_result = self.parse_expression(line)
                        if type(result) != type(final_result):
                            raise mylang_errors.IncompatableTypes("At line {}, near '{}' cannot {} value of type '{}' to type '{}'".format(check_last_v.value.line_number, check_last_v.value.value, {'PLUS':'concatinate', 'BAR':'subtract', 'STAR':'multiply', 'FORWARDSLASH':'divide'}[check_last_v.type], type(result).__name__, type(final_result).__name__))
                        return operation_converters[check_last_v.type](result, final_result)
                if current.value.value not in self.procedures:
                    raise mylang_errors.VariableNotDeclared("At line {}: procedure '{}' not declared".format(current.value.line_number, current.value.value))
                line = iter([check_next_v]+[i for i in line])
                params = []
                while True:
                    current_param = self.parse_expression(line)
                    can_continue = next(line, None)
                    params.append(current_param)
                    if not can_continue or can_continue.type == 'CPAREN':
                        break
                    line = iter([can_continue]+[i for i in line])
                print 'PARAMS HERE', params
                result, namespace = self.procedures[current.value.value](*params)
                self.variables = namespace if namespace else self.variables
                checking_next_v = next(line, None)
                if not checking_next_v or checking_next_v.type in ['COMMA', 'CPAREN']:
                    return result
                if checking_next_v.type in operation_converters:
                    returned_result = self.parse_expression(line)
                    if type(result) != type(returned_result):
                        raise mylang_errors.IncompatableTypes("At line {}, near '{}' cannot {} value of type '{}' to type '{}'".format(checking_next_v.value.line_number, checking_next_v.value.value, {'PLUS':'concatinate', 'BAR':'subtract', 'STAR':'multiply', 'FORWARDSLASH':'divide'}[checking_next_v.type], type(result).__name__, type(returned_result).__name__))
                    return operation_converters[checking_next_v.type](result, returned_result)
            if next_val.type == 'DOT':
                path = [current.value.value]

                seen_operator = False
                while True:
                    current_attr = next(line, None)
                    if not current_attr:
                        raise mylang_errors.InvalidAttributeCall("At line {}, near '{}'".format(next_val.value.line_number, next_val.value.value))
                    if current_attr.type == 'VARIABLE':

                        checking_next = next(line, None)
                        if not checking_next:
                            path.append(current_attr.value.value)
                            break
                        current_attr.value.isValid(checking_next.value)
                        path.append(current_attr.value.value)
                        if checking_next.type == 'OPAREN':

                            method_params = []
                            while True:
                                current_param = self.parse_expression(line)
                                method_params.append(current_param)
                                check_next_final = next(line, None)

                                if not check_next_final or check_next_final.type == "CPAREN" or check_next_final.type == 'COMMA':

                                    break

                                line = iter([check_next_final]+[i for i in line])

                            current_scope_selection = self.scopes if path[0] not in self.variables else self.variables
                            path = list(path)
                            the_method = path[-1]
                            copy_path = list(copy.deepcopy(path))
                            start = path[0]
                            path = path[:-1]
                            while path:
                                current_scope_selection = current_scope_selection[path[0]]
                                path = path[1:]
                            Scope.private_procedure_check(current_scope_selection.procedures[the_method])
                            to_return, namespace = current_scope_selection.procedures[the_method](*method_params)
                            base = self.scopes if start not in self.variables else self.variables
                            base[start].update_namespace(copy_path, namespace, start=start, end=copy_path[-1])
                            return to_return
                        if checking_next.type in operation_converters or checking_next.type == 'CPAREN' or checking_next.type == 'COMMA':
                            seen_operator = None if (checking_next.type == 'CPAREN' or checking_next.type == 'COMMA') else checking_next.type
                            break

                start_scope = path[0]
                flag = False
                if start_scope not in self.scopes:
                    if start_scope not in self.variables:
                        raise mylang_errors.VariableNotDeclared("Scope '{}' not declared".format(start_scope))
                    flag = True
                current_value_attr = self.scopes if not flag else self.variables
                while path:
                    try:
                        new_val = current_value_attr[path[0]]
                        print 'in try block', new_val
                    except:
                        if path[0] not in current_value_attr.scopes:
                            raise mylang_errors.AttributeNotFound("At line {}, near '{}':scope '{}' has no attribute '{}'".format(current_attr.value.line_number, current_attr.value.value, start_scope, path[0]))
                        current_value_attr = current_value_attr.scopes[path[0]]
                        path = path[1:]
                    else:
                        current_value_attr = new_val
                        path = path[1:]
                if seen_operator:
                    returned_val = self.parse_expression(line)
                    if type(current_value_attr) != type(returned_val):
                        raise mylang_errors.IncompatableTypes("At line {}, near '{}': cannot {} value of type '{}' to type '{}'".format(current_attr.value.line_number, current_attr.value.value, {'PLUS':'concatinate', 'BAR':'subtract', 'STAR':'multiply', 'FORWARDSLASH':'divide'}[seen_operator], type(current_value_attr).__name__, type(returned_val).__name__))
                    return operation_converters[seen_operator](current_value_attr, returned_val)

                return current_value_attr
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

    def update_vals(self, path, target_val):

        if not path[1:]:
            self.variables[path[0]] = target_val
        else:
            self.scopes[path[0]].update_vals(path[1:], target_val)
    def update_namespace(self, path, new_namespace, **kwargs):
        if not path:
            raise mylang_errors.InternalError("Scope {start} has no attribute {end}".format(**kwargs))
        if self.__scope_name__ == path[0]:
            self.variables = new_namespace
        else:
            self.scopes[path[0]].update_namespace(path[1:], new_namespace, **kwargs)
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
    def parse_procedure_header(self, header_line, current = None):
        current = [] if not current else current
        current_t = next(header_line, None)

        if not current_t:
            raise mylang_errors.InvalidEndOfDeclaration("Reached invalid end of procedure declaration")
        if current_t.type == 'CPAREN':
            second = next(header_line, None)
            if not second:

                return current, mylang_warnings.NoHeaderSeen, None
            current_t.value.isValid(second.value)
            if second.type == 'OBRACKET':
                #print 'returning here'
                return current, None, None
            if second.type == 'TORETURN':
                final_check = next(header_line, None)
                if not final_check:
                    raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': a return type must be specified".format(second.value.line_number, second.value.value))
                last_check = next(header_line, None)
                if not last_check:
                    #print 'returning here'
                    return current, mylang_warnings.NoHeaderSeen, final_check.value.value
                final_check.value.isValid(last_check.value)
                #print 'returning here'
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

                        if result:
                            raise mylang_errors.InvalidProcedureReturn("At line {}, near '{}': procedure '{}' is not void".format(start.value.line_number, start.value.value, start.value.value))
                        if namespace:
                            self.variables = namespace
                    else:
                        current_line = iter([current_param]+[i for i in current_line])
                        while True:
                            returned_expresssion = self.parse_expression(current_line)
                            full_params.append(returned_expresssion)
                            checking_last = next(current_line, None)
                            if not checking_last:
                                break
                            current_line = iter([checking_last]+[i for i in current_line])
                        #print "final params here", full_params
                        result, namespace = self.procedures[start.value.value](*full_params)
                        if result:
                            raise mylang_errors.InvalidProcedureReturn("At line {}, near '{}': procedure '{}' is not void".format(start.value.line_number, start.value.value, start.value.value))
                        if namespace:
                            self.variables = namespace

                if checking.type == 'ASSIGN':
                    to_store = self.parse_assign(current_line)
                    print 'storing string?', to_store, start.value.value
                    self.variables[start.value.value] = to_store

                    self.scopes[start.value.value] = Scope(start.value.value, [], [], current_namespace = dict([(i, getattr(to_store, i)()) for i in ['upper', 'lower', 'capitalize', 'isupper', 'islower']]+[('type', 'str')]) if isinstance(to_store, str) else dict([('increment', to_store+1), ('squared', pow(to_store, 2))]) if isinstance(to_store, int) else {'type':getattr(to_store, 'rep', type(to_store).__name__)}, builtins = mylang_builtins.builtin_methods[getattr(to_store, 'rep', type(to_store).__name__)])

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


            if start.type == 'PRIVATE':

                checking_next = next(current_line, None)
                print 'IN HERE 111', checking_next
                if not checking_next:
                    raise mylang_errors.InvalidSyntax("At line {}, near '{}': expecting a variable name".format(start.value.line_number, start.value.value))
                if checking_next.type == 'PRIVATEPROCEDURE':
                    checking_temp_line = [i for i in next(self.token_list, None)]
                    if not any(i.type == 'PROCEDURE' for i in checking_temp_line):
                        raise mylang_errors.InvalidSyntax("At line {}, near '@':invalid use of 'private'".format(checking_next.value.line_number))
                    self.token_list = iter([iter(checking_temp_line)]+[i for i in self.token_list])
                    self.seen_procedure_private = True

                else:

                    start.value.isValid(checking_next.value)
                    checking_next_op = next(current_line, None)
                    if not checking_next_op:
                        raise mylang_errors.InvalidSyntax("At line {}, near '{}': expecting private variable assignment".format(start.value.line_number, start.value.value))
                    if checking_next_op.type != 'ASSIGN':
                        raise mylang_errors.InvalidSyntax("At line {}, near '{}': private variable declaration syntax can only be used in the context of assignment".format(start.value.line_number, start.value.value))
                    self.private_variables.append(checking_next.value.value)
                    return_result = self.parse_assign(current_line)
                    self.variables[checking_next.value.value] = return_result
                    self.scopes[start.value.value] = Scope(start.value.value, [], [], current_namespace = dict([(i, getattr(return_result, i)()) for i in ['upper', 'lower', 'capitalize', 'isupper', 'islower']]+[('type', 'str')]) if isinstance(return_result, str) else dict([('increment', return_result+1), ('squared', pow(return_result, 2)), ('type', 'int')]) if isinstance(return_result, int) else {'type':type(return_result).__name__}, builtins = mylang_builtins.builtin_methods[type(return_result).__name__] if type(return_result).__name__ in mylang_builtins.builtin_methods else {})
                    print 'self.variables here', self.variables
                    print 'private variable name: {}'.format(checking_next.value.value)
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
                        #print "procedure name is: {}, params are: {}, warnings include: {}, return_type is {}".format(possible_name.value.value, function_params, warnings, return_type)
                        #print "procedure name is: {}, params are: {}, warnings include: {}, return_type is {}".format(possible_name.value.value, function_params, warnings, return_type)
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
                        self.procedures[possible_name.value.value] = Procedure(possible_name.value.value, function_params, procedure_namespace, can_mutate = True, current_namespace = self.variables, return_type = return_type, is_private = self.seen_procedure_private, current_namespace_procedures = self.procedures)
                        self.seen_procedure_private = False
                if next_start.type == 'PROCEDURE':
                    print 'in scope procedure declaration'
                    possible_name = next(current_line, None)

                    self.possible_name = possible_name
                    if not possible_name:
                        raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': expecting a scope or procedure declaration".format(next_start.value.line_number, next_start.value.value))
                    next_start.value.isValid(possible_name.value)
                    possible_start = next(current_line, None)
                    if not possible_start:
                        raise mylang_errors.InvalidEndOfDeclaration("At line {}, near '{}': expecting a scope or procedure declaration".format(next_start.value.line_number, possible_name.value.value))
                    possible_name.value.isValid(possible_start.value)
                    temp_current_line = [i for i in current_line]
                    #print 'CURRENT LINE FOR function {}'.format(possible_name.value.value), temp_current_line
                    current_line = iter(temp_current_line)
                    function_params, warnings, return_type = self.parse_procedure_header(current_line)
                    #print 'CHECKING FUNCTION_PARAMS here for function {}'.format(possible_name.value.value), function_params

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
                    self.procedures[possible_name.value.value] = Procedure(possible_name.value.value, function_params, procedure_namespace, current_namespace = self.variables, return_type = return_type, is_private = self.seen_procedure_private, current_namespace_procedures = self.procedures)
                    self.seen_procedure_private = False
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
                #print 'CURRENT LINE FOR function {}'.format(possible_name.value.value), current_line

                function_params, warnings, return_type = self.parse_procedure_header(current_line)
                #print 'CHECKING FUNCTION_PARAMS here for function {}'.format(possible_name.value.value), function_params
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
                self.procedures[possible_name.value.value] = Procedure(possible_name.value.value, function_params, procedure_namespace, return_type = return_type, is_private = self.seen_procedure_private, current_namespace_procedures = self.procedures)
                self.seen_procedure_private = False
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
    def parse_scope_params(self, first, line, found = None):
        found = [] if not found else found
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
        if current.type == 'OBRACKET':

            return ArrayList(line, variables = self.variables, scopes = self.scopes, procedures = self.procedures)
        if current.type == 'VARIABLE':
            test_final = next(line, None)
            if not test_final:
                if current.value.value not in self.variables:
                    raise mylang_errors.VariableNotDeclared("At line {}, '{}' not declared".format(current.value.line_number, current.value.value))
                return self.variables[current.value.value]
            current.value.isValid(test_final.value)
            if test_final.type == 'OPAREN':
                check_next_val = next(line, None)
                if not check_next_val:
                    raise mylang_errors.InvalidSyntax("At line {}, near '{}': expecting passed value or ')'".format(test_final.value.line_number, test_final.value.value))
                test_final.value.isValid(check_next_val.value)
                if check_next_val.type == 'CPAREN':
                    if current.value.value not in self.scopes and current.value.value not in self.procedures:
                        raise mylang_errors.ObjectNotDeclared("At line {}, near '{}': '{}' is neither a scope nor a procedure".format(current.value.line_number, current.value.value, current.value.value))
                    return self.scopes[current.value.value]() if current.value.value in self.scopes else self.procedures[current.value.value]()
                line = iter([check_next_val]+[i for i in line])
                full_params_for_object = []
                while True:
                    current_result = self.parse_expression(line)
                    full_params_for_object.append(current_result)
                    check_here = next(line, None)
                    print 'checking here', check_here
                    if not check_here or check_here.type == 'CPAREN':
                        break
                    line = iter([check_here]+[i for i in line])
                if current.value.value in self.procedures:
                    to_return, namespace = self.procedures[current.value.value](*full_params_for_object)
                    if namespace:
                        self.variables.update(namespace)
                    if to_return == []:
                        raise mylang_errors.InvalidProcedureReturn("procedure '{}' is void".format(current.value.value))
                    return to_return
                return self.scopes[current.value.value](*full_params_for_object)
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
                        if check.type == 'OPAREN':
                            check_next_val = next(line, None)
                            if not check_next_val:
                                raise mylang_errors.InvalidParameterType("At line {}, near '{}': expecting ')'".format(check.value.line_number, check.value.value))
                            if check_next_val.type == 'CPAREN':
                                current_scope_1 = self.scopes if path[0] not in self.variables else self.variables
                                path_copy = copy.deepcopy(list(path))
                                path = list(path)
                                while path:
                                    current_scope_1 = current_scope_1[path[0]]
                                    path = path[1:]

                                try:
                                    test = current_scope_1.procedures[temp_path.value.value]
                                except:
                                    if len(path_copy) == 1:
                                        print (path_copy, temp_path.value.value, current_scope_1)
                                        return self.scopes[path_copy[-1]].builtins[temp_path.value.value](path_copy[-1], current_scope_1)
                                    scope_object = self.scopes if path_copy[0] not in self.variables else self.variables

                                    while path_copy[:-1]:
                                        scope_object = scope_object[path_copy[0]]
                                        path_copy = path_copy[1:]

                                    return scope_object.scopes[path_copy[-1]].builtins[temp_path.value.value](path_copy[-1], current_scope_1)

                                Scope.private_procedure_check(current_scope_1.procedures[temp_path.value.value])
                                to_return, new_scope_namespace = current_scope_1.procedures[temp_path.value.value]()
                                self.scopes[path_copy[0]].update_namespace(path_copy, new_scope_namespace, start=path_copy[0], end=path_copy[-1])
                                return to_return
                            line = iter([check_next_val]+[i for i in line])
                            current_params_check = []
                            while True:
                                result_here_1 = self.parse_expression(line)
                                print 'result_here_1', result_here_1
                                current_params_check.append(result_here_1)
                                check_next_4 = next(line, None)
                                if not check_next_4:
                                    break
                                line = iter([check_next_4]+[i for i in line])
                            #print 'current_params_check', current_params_check
                            #print 'current_params_check here for {}'.format(path[-1]), current_params_check
                            current_scope_1 = self.scopes if path[0] not in self.variables else self.variables
                            path_copy = copy.deepcopy(list(path))
                            path = list(path)
                            while path:
                                current_scope_1 = current_scope_1[path[0]]
                                path = path[1:]
                            try:
                                test = current_scope_1.procedures[temp_path.value.value]
                            except:
                                #print 'path_copy[0]', path_copy
                                scope_object = self.scopes

                                while path_copy[:-1]:
                                    scope_object = scope_object[path_copy[0]]
                                    path_copy = path_copy[1:]
                                #print 'scope_object here', scope_object

                                return scope_object[path_copy[-1]].builtins[temp_path.value.value](path_copy[-1], current_scope_1, *current_params_check)
                            Scope.private_procedure_check(current_scope_1.procedures[temp_path.value.value])
                            to_return, new_scope_namespace = current_scope_1.procedures[temp_path.value.value](*current_params_check)
                            if to_return == []:
                                raise mylang_errors.InvalidProcedureReturnType("Procedure '{}' is void".format(temp_path.value.value))
                            self.scopes[path_copy[0]].update_namespace(path_copy, new_scope_namespace, start=path_copy[0], end=path_copy[-1])

                            return to_return
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
                if type(returned_val) in [int, float] and type(self.variables[current.value.value]) in [int, float]:
                    return operation_converters[test_final.type](self.variables[current.value.value], returned_val)
                if type(returned_val) != type(self.variables[current.value.value]):
                    raise mylang_errors.IncompatableTypes("At line {}, near {}, cannot {} variable of type '{}' to type '{}'".format(current.value.line_number, current.value.value, {'PLUS':'concatinate', 'BAR':'subtract', 'STAR':'multiply', 'FORWARDSLASH':'divide'}[test_final.type], type(self.variables[current.value.value]).__name__, type(returned_val).__name__))

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
                    print 'SECOND HERE', second
                    if second.type != 'DIGIT' and second.type != 'VARIABLE':

                        raise mylang_errors.IncompatableTypes("At line {}, cannot multiply type 'INT' to type {}".format(second.value.line_number, type(second.value.value).__name__))
                    operator = next(line, None)
                    if not operator:
                        if second.type == 'VARIABLE':
                            return self.variables[second.value.value]*int(current.value.value)
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
    @mylang_wrappers.check_private(suppress=config.PRIVATE_VARIABLE_LEVEL)
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
        return "{}<storing {} scope{}:({})({}), builtins:{}".format(self.__class__.__name__, len(self.scopes), 's' if len(self.scopes) != 1 else '',', '.join(str(b) for a, b in self.scopes.items()), ', '.join('{} = {}'.format(a, b) for a, b in self.variables.items()), ', '.join(self.builtins.keys()))
    def __str__(self):
        return "{}<storing {} scope{}:({})({}), builtins: {}".format(self.__class__.__name__, len(self.scopes), 's' if len(self.scopes) != 1 else '',', '.join(str(b) for a, b in self.scopes.items()), ', '.join('{} = {}'.format(a, b) for a, b in self.variables.items()), ', '.join(self.builtins.keys()))

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
    def __add__(self, new_scopes):
        self.scopes.update(new_scopes.scopes)
        final_scope = Scopes()
        final_scope.scopes = self.scopes
        return final_scope
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
    def parse_procedure_header(self, header_line, current = None):
        current = [] if not current else current
        checking_header_line = [i for i in header_line]
        header_line = iter(checking_header_line)
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
            if var.value.value not in self.scopes:
                raise mylang_errors.VariableNotDeclared("At line {}, near '{}': variable '{}' not declared".format(var.value.line_number, var.value.value, var.value.value))
            return self.scopes[var.value.value]
        return self.variables[var.value.value]

    def parse_expression(self, line):
        operation_converters = {'PLUS':lambda x, y:x+y, 'BAR':lambda x,y:x-y, 'STAR':lambda x, y:x*y, 'FORWARDSLASH':lambda x, y:x/y}
        current = next(line, None)
        print 'current last', current
        if not current:
            return None
        if current.type == 'VARIABLE':
            next_val = next(line, None)
            if not next_val or next_val.type == 'COMMA' or next_val.type == 'CPAREN':
                return self.variable_exists(current)
            current.value.isValid(next_val.value)

            if next_val.type == 'OPAREN':
                check_next_v = next(line, None)
                if not check_next_v:
                    raise mylang_errors.ParameterSytnaxError("At line {}, near '{}': reached unexpected end of procedure call".format(current.value.line_number, current.value.value))
                if check_next_v.type == 'CPAREN':
                    if current.value.value not in self.procedures:
                        raise mylang_errors.AttributeNotFound("At line {}, near '{}': procedure '{}' not found".format(current.value.line_number, current.value.value, current.value.value))
                    result, namespace = self.procedures[current.value.value]()
                    self.variables = namespace if namespace else self.variables
                    check_last_v = next(line, None)
                    if check_last_v.type in ['COMMA', 'CPAREN']:
                        return result
                    if check_last_v.type in operation_converters:
                        final_result = self.parse_expression(line)
                        if type(result) != type(final_result):
                            raise mylang_errors.IncompatableTypes("At line {}, near '{}' cannot {} value of type '{}' to type '{}'".format(check_last_v.value.line_number, check_last_v.value.value, {'PLUS':'concatinate', 'BAR':'subtract', 'STAR':'multiply', 'FORWARDSLASH':'divide'}[check_last_v.type], type(result).__name__, type(final_result).__name__))
                        return operation_converters[check_last_v.type](result, final_result)
                if current.value.value not in self.procedures:
                    raise mylang_errors.VariableNotDeclared("At line {}: procedure '{}' not declared".format(current.value.line_number, current.value.value))
                line = iter([check_next_v]+[i for i in line])
                params = []
                while True:
                    current_param = self.parse_expression(line)
                    can_continue = next(line, None)
                    params.append(current_param)
                    if not can_continue or can_continue.type == 'CPAREN':
                        break
                    line = iter([can_continue]+[i for i in line])
                print 'PARAMS HERE', params
                result, namespace = self.procedures[current.value.value](*params)
                self.variables = namespace if namespace else self.variables
                checking_next_v = next(line, None)
                if not checking_next_v or checking_next_v.type in ['COMMA', 'CPAREN']:
                    return result
                if checking_next_v.type in operation_converters:
                    returned_result = self.parse_expression(line)
                    if type(result) != type(returned_result):
                        raise mylang_errors.IncompatableTypes("At line {}, near '{}' cannot {} value of type '{}' to type '{}'".format(checking_next_v.value.line_number, checking_next_v.value.value, {'PLUS':'concatinate', 'BAR':'subtract', 'STAR':'multiply', 'FORWARDSLASH':'divide'}[checking_next_v.type], type(result).__name__, type(returned_result).__name__))
                    return operation_converters[checking_next_v.type](result, returned_result)
            if next_val.type == 'DOT':
                path = [current.value.value]

                seen_operator = False
                while True:
                    current_attr = next(line, None)
                    if not current_attr:
                        raise mylang_errors.InvalidAttributeCall("At line {}, near '{}'".format(next_val.value.line_number, next_val.value.value))
                    if current_attr.type == 'VARIABLE':

                        checking_next = next(line, None)
                        if not checking_next:
                            path.append(current_attr.value.value)
                            break
                        current_attr.value.isValid(checking_next.value)
                        path.append(current_attr.value.value)
                        if checking_next.type == 'OPAREN':

                            method_params = []
                            while True:
                                current_param = self.parse_expression(line)
                                method_params.append(current_param)
                                check_next_final = next(line, None)

                                if not check_next_final or check_next_final.type == "CPAREN" or check_next_final.type == 'COMMA':

                                    break

                                line = iter([check_next_final]+[i for i in line])

                            current_scope_selection = self.scopes if path[0] not in self.variables else self.variables
                            path = list(path)
                            the_method = path[-1]
                            copy_path = list(copy.deepcopy(path))
                            start = path[0]
                            path = path[:-1]
                            while path:
                                current_scope_selection = current_scope_selection[path[0]]
                                path = path[1:]
                            Scope.private_procedure_check(current_scope_selection.procedures[the_method])
                            to_return, namespace = current_scope_selection.procedures[the_method](*method_params)
                            base = self.scopes if start not in self.variables else self.variables
                            base[start].update_namespace(copy_path, namespace, start=start, end=copy_path[-1])
                            return to_return
                        if checking_next.type in operation_converters or checking_next.type == 'CPAREN' or checking_next.type == 'COMMA':
                            seen_operator = None if (checking_next.type == 'CPAREN' or checking_next.type == 'COMMA') else checking_next.type
                            break

                start_scope = path[0]
                flag = False
                if start_scope not in self.scopes:
                    if start_scope not in self.variables:
                        raise mylang_errors.VariableNotDeclared("Scope '{}' not declared".format(start_scope))
                    flag = True
                current_value_attr = self.scopes if not flag else self.variables
                while path:
                    try:
                        new_val = current_value_attr[path[0]]
                        print 'in try block', new_val
                    except:
                        if path[0] not in current_value_attr.scopes:
                            raise mylang_errors.AttributeNotFound("At line {}, near '{}':scope '{}' has no attribute '{}'".format(current_attr.value.line_number, current_attr.value.value, start_scope, path[0]))
                        current_value_attr = current_value_attr.scopes[path[0]]
                        path = path[1:]
                    else:
                        current_value_attr = new_val
                        path = path[1:]
                if seen_operator:
                    returned_val = self.parse_expression(line)
                    if type(current_value_attr) != type(returned_val):
                        raise mylang_errors.IncompatableTypes("At line {}, near '{}': cannot {} value of type '{}' to type '{}'".format(current_attr.value.line_number, current_attr.value.value, {'PLUS':'concatinate', 'BAR':'subtract', 'STAR':'multiply', 'FORWARDSLASH':'divide'}[seen_operator], type(current_value_attr).__name__, type(returned_val).__name__))
                    return operation_converters[seen_operator](current_value_attr, returned_val)

                return current_value_attr
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

            start = next(current_line)
            if start.type == 'IMPORT':
                file_path, flag = mylang_builtins.get_file_path(current_line)
                parsed_file = Parser(mylang_tokenizer.Tokenize(file_path).tokenized_data)
                if flag == ImportAll:

                    self.variables.update(parsed_file.variables)
                    self.scopes = self.scopes+parsed_file.scopes
                    self.procedures.update_procedures(parsed_file.procedures)
                else:

                    self.scopes[re.split('[/\.]', file_path)[-2]] = Scope(re.split('[/\.]', file_path)[-2], [], [], current_namespace = parsed_file.variables)
                    self.scopes[re.split('[/\.]', file_path)[-2]].scopes = parsed_file.scopes
                    self.scopes[re.split('[/\.]', file_path)[-2]].procedures.update_procedures(parsed_file.procedures)
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
                        print 'IN HERE WITH procedure ', start.value.value
                        result, namespace = self.procedures[start.value.value]()
                        #check for truthiness of function __call__ returned values

                        if result:
                            raise mylang_errors.InvalidProcedureReturn("At line {}, near '{}': procedure '{}' is not void".format(start.value.line_number, start.value.value, start.value.value))
                        if namespace:
                            self.variables = namespace
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
                        result, namespace = self.procedures[start.value.value](*full_params)
                        if result:
                            raise mylang_errors.InvalidProcedureReturn("At line {}, near '{}': procedure '{}' is not void".format(start.value.line_number, start.value.value, start.value.value))
                        if namespace:
                            self.variables = namespace

                if checking.type == 'ASSIGN':
                    to_store = self.parse_assign(current_line)
                    self.variables[start.value.value] = to_store

                    self.scopes[start.value.value] = Scope(start.value.value, [], [], current_namespace = dict([(i, getattr(to_store, i)()) for i in ['upper', 'lower', 'capitalize', 'isupper', 'islower']]+[('type', type(to_store).__name__)]) if isinstance(to_store, str) else dict([('increment', to_store+1), ('squared', pow(to_store, 2)), ('type', type(to_store).__name__)]) if isinstance(to_store, int) else {'type':getattr(to_store, 'rep', type(to_store).__name__)}, builtins = mylang_builtins.builtin_methods[getattr(to_store, 'rep', type(to_store).__name__)])

                if checking.type == 'DOT':
                    path = collections.deque([start.value.value])
                    to_assign = None
                    seen_method_call = False
                    while True:
                        current = next(current_line, None)
                        if not current:
                            raise mylang_errors.IllegialPrecedence("At line {}, near '{}', reached abrupt end of statement".format(checking.value.line_number, checking.value.value))

                        if current.type == 'VARIABLE':
                            check_next = next(current_line, None)
                            current.value.isValid(check_next.value)
                            if check_next.type == 'OPAREN':
                                checking_next_val = next(current_line, None)
                                if not checking_next_val:
                                    raise mylang_errors.InvalidParameterType("At line {}, near '{}'. Expecting variable or ')'".format(check_next.value.line_number, check_next.value.value))
                                check_next.value.isValid(checking_next_val.value)
                                if checking_next_val.type == 'CPAREN':
                                    starting_base = self.scopes if path[0] not in self.variables else self.variables

                                    path = list(path)
                                    while path:
                                        starting_base = starting_base[path[0]]
                                        path = path[1:]
                                    starting_base.procedures[current.value.value]()

                                    seen_method_call = True
                                    current_line = iter([checking_next_val]+[i for i in current_line])
                                    break
                                current_line = iter([checking_next_val]+[i for i in current_line])
                                current_method_params = []
                                while True:
                                    current_method_param = self.parse_expression(current_line)
                                    current_method_params.append(current_method_param)
                                    checking_to_continue = next(current_line, None)
                                    if not checking_to_continue:
                                        break
                                    current_line = iter([checking_to_continue]+[i for i in current_line])
                                starting_base = self.scopes if path[0] not in self.variables else self.variables

                                path = list(path)
                                path_copy = copy.deepcopy(path)
                                while path:
                                    starting_base = starting_base[path[0]]
                                    path = path[1:]
                                try:

                                    builtin_procedure = mylang_builtins.builtin_methods[getattr(starting_base, 'rep', type(starting_base).__name__)]
                                    print 'builtin_procedure here', builtin_procedure
                                except (KeyError, IndexError):
                                    pass

                                else:
                                    builtin_procedure[current.value.value]
                                    builtin_procedure[current.value.value](path_copy[-1], starting_base, *current_method_params)
                                    seen_method_call = True
                                    break
                                Scope.private_procedure_check(starting_base.procedures[current.value.value])
                                starting_base.procedures[current.value.value](*current_method_params)
                                seen_method_call = True
                                break
                            if check_next.type == "DOT":
                                path.append(current.value.value)
                            if check_next.type == 'ASSIGN':
                                path.append(current.value.value)
                                to_assign = self.parse_assign(current_line)
                                break

                    if not seen_method_call:
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
                        self.procedures[possible_name.value.value] = Procedure(possible_name.value.value, function_params, procedure_namespace, can_mutate = True, current_namespace = self.variables, return_type = return_type, current_namespace_procedures = self.procedures)
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
                    temp_current_line = [i for i in current_line]
                    print 'CURRENT LINE FOR function {}'.format(possible_name.value.value), temp_current_line
                    current_line = iter(temp_current_line)
                    function_params, warnings, return_type = self.parse_procedure_header(current_line)
                    print 'CHECKING FUNCTION_PARAMS here for function {}'.format(possible_name.value.value), function_params

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
                    self.procedures[possible_name.value.value] = Procedure(possible_name.value.value, function_params, procedure_namespace, current_namespace = self.variables, return_type = return_type, current_namespace_procedures = self.procedures)
                if next_start.type == 'SCOPE':
                    params, name, flags = self.parse_scope(next_start, current_line, self.token_list)

                    temp_flag = bool(flags)
                    scope_block = []
                    brackets_seen = collections.deque(['{']) if not temp_flag else collections.deque()
                    while True:
                        '''
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
                        '''
                        current_line_on = next(self.token_list, None)
                        if not current_line_on:
                            raise mylang_errors.ReachedEndOfScopeBlock("missing block terminating character '}'")
                        testing_line = [i for i in current_line_on]
                        if any(i.type == "OBRACKET" for i in testing_line):
                            brackets_seen.append('{')
                        if any(i.type == 'CBRACKET' for i in testing_line):
                            if not brackets_seen:
                                raise mylang_errors.ReachedEndOfScopeBlock("missing block initialization character '{'")
                            val = brackets_seen.pop()
                            if not brackets_seen:
                                break
                        scope_block.append(testing_line)
                    print 'SCOPE BLOCK HERE FOR scope {}'.format(name), scope_block
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
                print 'CURRENT LINE FOR function {}'.format(possible_name.value.value), current_line

                function_params, warnings, return_type = self.parse_procedure_header(current_line)
                print 'CHECKING FUNCTION_PARAMS here for function {}'.format(possible_name.value.value), function_params
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
                self.procedures[possible_name.value.value] = Procedure(possible_name.value.value, function_params, procedure_namespace, return_type= return_type, current_namespace_procedures = self.procedures)
            if start.type == 'SCOPE':
                params, name, flags = self.parse_scope(start, current_line, self.token_list)

                temp_flag = bool(flags)
                scope_block = []
                brackets_seen = collections.deque(['{']) if not temp_flag else collections.deque()
                while True:
                    '''
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
                    '''
                    current_check_on = next(self.token_list, None)
                    if not current_check_on:
                        raise mylang_errors.ReachedEndOfScopeBlock("missing block terminating character '}'")
                    current_content_check_on = [i for i in current_check_on]
                    if any(i.type == 'OBRACKET' for i in current_content_check_on):
                        brackets_seen.append('{')
                    if any(i.type == 'CBRACKET' for i in current_content_check_on):
                        if not brackets_seen:
                            raise mylang_errors.ReachedEndOfScopeBlock("missing block initialization character '{'")
                        val = brackets_seen.pop()
                        if not brackets_seen:
                            break

                    scope_block.append(current_content_check_on)
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

    def parse_scope_params(self, first, line, found = None):
        found = [] if not found else found
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
        if current.type == 'OBRACKET':

            return ArrayList(line, variables = self.variables, scopes = self.scopes, procedures = self.procedures)
        if current.type == 'VARIABLE':
            test_final = next(line, None)
            if not test_final or test_final.type == 'COMMA' or test_final.type == 'CPAREN':
                if current.value.value not in self.variables:
                    raise mylang_errors.VariableNotDeclared("At line {}, '{}' not declared".format(current.value.line_number, current.value.value))
                return self.variables[current.value.value]
            current.value.isValid(test_final.value)
            if test_final.type == 'OPAREN':
                test_second_line = next(line, None)
                if not test_second_line:
                    raise mylang_errors.InvalidSyntax("At line {}, near '{}': expecting a variable type or a close parenthesis ')'".format(test_final.value.line_number, test_final.value.value))
                test_final.value.isValid(test_second_line.value)
                if test_second_line.type == 'CPAREN':
                    to_return, namespace = self.procedures[current.value.value]()
                    if namespace:
                        self.variables.update(namespace)
                    return to_return
                line = iter([test_second_line]+[i for i in line])
                #currently, here
                if current.value.value in self.procedures:
                    testing_next = next(line, None)
                    if not testing_next:
                        raise mylang_errors.InvalidParameterType("At line {}: invalid syntax".format(current.value.line_number))
                    line = iter([testing_next]+[i for i in line])
                    function_params = []
                    while True:
                        current_param = self.parse_expression(line)
                        function_params.append(current_param)
                        checking_next_val = next(line, None)
                        if not checking_next_val:
                            break
                        line = iter([checking_next_val]+[i for i in line])
                    result, namespace = self.procedures[current.value.value](*function_params)

                    return result
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
                        if check.type == 'OPAREN':
                            check_next_val = next(line, None)
                            if not check_next_val:
                                raise mylang_errors.InvalidParameterType("At line {}, near '{}': expecting ')'".format(check.value.line_number, check.value.value))
                            if check_next_val.type == 'CPAREN':
                                current_scope_1 = self.scopes if path[0] not in self.variables else self.variables
                                path_copy = copy.deepcopy(list(path))
                                path = list(path)
                                while path:
                                    current_scope_1 = current_scope_1[path[0]]
                                    path = path[1:]

                                try:
                                    test = current_scope_1.procedures[temp_path.value.value]
                                except:
                                    if len(path_copy) == 1:
                                        print (path_copy, temp_path.value.value, current_scope_1)
                                        return self.scopes[path_copy[-1]].builtins[temp_path.value.value](path_copy[-1], current_scope_1)
                                    scope_object = self.scopes if path_copy[0] not in self.variables else self.variables

                                    while path_copy[:-1]:
                                        scope_object = scope_object[path_copy[0]]
                                        path_copy = path_copy[1:]

                                    return scope_object.scopes[path_copy[-1]].builtins[temp_path.value.value](path_copy[-1], current_scope_1)

                                Scope.private_procedure_check(current_scope_1.procedures[temp_path.value.value])
                                to_return, new_scope_namespace = current_scope_1.procedures[temp_path.value.value]()
                                self.scopes[path_copy[0]].update_namespace(path_copy, new_scope_namespace, start=path_copy[0], end=path_copy[-1])
                                return to_return
                            line = iter([check_next_val]+[i for i in line])
                            current_params_check = []
                            while True:
                                result_here_1 = self.parse_expression(line)
                                print 'result_here_1', result_here_1
                                current_params_check.append(result_here_1)
                                check_next_4 = next(line, None)
                                if not check_next_4:
                                    break
                                line = iter([check_next_4]+[i for i in line])
                            #print 'current_params_check here for {}'.format(path[-1]), current_params_check
                            current_scope_1 = self.scopes if path[0] not in self.variables else self.variables
                            path_copy = copy.deepcopy(list(path))
                            path = list(path)
                            while path:
                                current_scope_1 = current_scope_1[path[0]]
                                path = path[1:]
                            try:
                                test = current_scope_1.procedures[temp_path.value.value]
                            except:
                                #print 'path_copy[0]', path_copy
                                scope_object = self.scopes

                                while path_copy[:-1]:
                                    scope_object = scope_object[path_copy[0]]
                                    path_copy = path_copy[1:]
                                #print 'scope_object here', scope_object
                                return scope_object.scopes[path_copy[-1]].builtins[temp_path.value.value](path_copy[-1], current_scope_1, *current_params_check)
                            Scope.private_procedure_check(current_scope_1.procedures[temp_path.value.value])
                            to_return, new_scope_namespace = current_scope_1.procedures[temp_path.value.value](*current_params_check)
                            if to_return == []:
                                raise mylang_errors.InvalidProcedureReturnType("Procedure '{}' is void".format(temp_path.value.value))
                            self.scopes[path_copy[0]].update_namespace(path_copy, new_scope_namespace, start=path_copy[0], end=path_copy[-1])

                            return to_return
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
                start_scope = path[0]
                last_path_val = None
                if path[0] not in scope_result:
                    raise mylang_errors.AttributeNotFound("At line {}, near {}: variable '{}' has no attribute '{}'".format(current.value.line_number, current.value.value, current.value.value, path[1]))
                store_last = []
                string_last = []
                while path:
                    val = path.popleft()
                    try:
                        if val in scope_result:

                            scope_result = scope_result[val]
                        else:
                            if not path:
                                print 'V', val
                                if val in store_last[-2].scopes[string_last[-1]]:
                                    print 'all is well here'

                                    scope_result = store_last[-2].scopes[string_last[-1]][val]
                                else:
                                    print 'in this level'
                                    raise mylang_errors.AttributeNotFound("scope '{}' has no attribute '{}'".format(string_last[-1], val))
                            else:
                                print 'strange result'
                                scope_result = scope_result.scopes[val]
                        store_last.append(scope_result)
                        string_last.append(val)
                    except (IndexError, KeyError, TypeError):
                        raise mylang_errors.AttributeNotFound("scope '{}' has no attribute '{}'".format(string_last[-1], val))
                        pass
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
                if type(returned_val) in [int, float] and type(self.variables[current.value.value]) in [int, float]:
                    return operation_converters[test_final.type](self.variables[current.value.value], returned_val)
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


                if type(returned_val) not in [int, float]:
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
