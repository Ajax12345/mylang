import mylang_errors
import functools
import re
import os
import mylang_wrappers
import mylang_config
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
        return all(i in self.contents for i in [getattr(val, 'contents', val)])
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

builtin_checker = {'reverse':[0, [None], [None], False], 'sub':[2, [str, str], ['to_replace', 'target'], True], 'exp':[1, [int], ['pow'], True], 'toFloat':[1, [int], ['denominator'], True], 'splice':[1, [str], ['split_at'], True], 'occurs':[1, [], ['character'], False], 'itemAt':[1, [int], ['index'], False], 'indexOf':[1, [], ['target'], False], 'contains':[1, [], ['target'], False], 'run':[2, [int, int], ['start', 'end'], True], 'length':[0, [None], [None], False], 'updateAt':[2, [int], ['index', 'target'], True], 'addBack':[1, [None], ['to_add'], False], 'addFront':[1, [None], ['to_add'], False], 'extendBack':[1, ['ArrayList'], ['to_add'], True], 'extendFront':[1, ['ArrayList'], ['to_add'], True], 'removeAt':[1, [int], ['target'], True], 'removeItem':[1, [None], ['target'], False], 'join':[1, [str], ['spacer'], True]}

type_checker = {'reverse':[str, list, 'ArrayList'], 'sub':[str], 'exp':[int, float], 'toFloat':[int], 'splice':[str], 'occurs':[str, list, 'ArrayList'], 'itemAt':[str, list, 'ArrayList'], 'indexOf':[str, list, 'ArrayList'], 'contains':[str, list, 'ArrayList'], 'run':[str, list, 'ArrayList'], 'length':[list, str, 'ArrayList'], 'updateAt':[str, 'ArrayList'], 'addBack':['ArrayList'], 'addFront':['ArrayList'], 'extendBack':['ArrayList'], 'extendFront':['ArrayList'], 'removeAt':['ArrayList'], 'removeItem':['ArrayList'], 'join':['ArrayList']}

def check_param_num(f):
    @functools.wraps(f)
    def wrapper(name, val, *args):
        if builtin_checker[f.__name__][0] != len(args):
            raise mylang_errors.TooManyParamemters("procedure '{}' expects {} parameters, but recieved {}".format(f.__name__, builtin_checker[f.__name__][0], len(args)))
        if args and builtin_checker[f.__name__][-1]:
            print 'args here', args
            print 'results', builtin_checker[f.__name__][1]
            for i, [a, b] in enumerate(zip(args, builtin_checker[f.__name__][1])):
                if getattr(a, 'rep', type(a).__name__) != (b if isinstance(b, str) else getattr(b, '__name__', type(b).__name__)):
                    raise mylang_errors.InvalidParameterType("procedure '{}' parameter '{}' expects value of type '{}', but recieved value of type '{}'".format(f.__name__, builtin_checker[f.__name__][2][i], (b if isinstance(b, str) else getattr(b, '__name__', type(b).__name__)) , getattr(a, 'rep', type(a).__name__)))
        return f(name, val, *args)
    return wrapper

def check_type(f):
    @functools.wraps(f)
    def wrapper(name, val, *args):
        if getattr(val, 'rep', type(val)) not in type_checker[f.__name__]:
            raise Exception
        return f(name, val, *args)

    return wrapper

@check_param_num
@check_type
def reverse(name, val):
    return getattr(val, 'reverse_contents', val[::-1])

@check_param_num
@check_type
def updateAt(name, val, index, target):

    if index >= len(val):
        raise mylang_errors.IndexOutOfBoundsError("variable '{}' has length ({}), but recieved index of value ({})".format(name, len(val), index))
    val[index] = target

@check_param_num
@check_type
def addBack(name, val, to_add):
    val.add_to_back(to_add)

@check_param_num
@check_type
def extendBack(name, val, to_add):
    val.extendBack(to_add)

@check_param_num
@check_type
def extendFront(name, val, to_add):
    val.extendFront(to_add)

@check_param_num
@check_type
def addFront(name, val, to_add):
    val.add_to_front(to_add)

@check_param_num
@check_type
def sub(name, val, to_replace, target):
    return re.sub(to_replace, target, val)

@check_param_num
@check_type
def exp(name, val, raise_to):
    return pow(val, raise_to)

@check_param_num
@check_type
def toFloat(name, val, denominator):
    return val/float(denominator)

@check_param_num
@check_type
def removeItem(name, val, target):
    if target not in val:
        raise mylang_errors.CollectionDoesNotContainItem("ArrayList '{}' does not contain '{}'".format(name, target))
    val.remove_val_at(target)

@check_param_num
@check_type
def removeAt(name, val, target):
    if target >= len(val):
        raise mylang_errors.IndexOutOfBoundsError("length of variable '{}' is ({}), because ({})".format(name, len(val), target))
    first_val = val[target]
    del val[target]
    return first_val

@check_param_num
@check_type
def splice(name, val, split_at):
    return ArrayList([], filled=val.split(split_at))

@check_param_num
@check_type
def occurs(name, val, character):
    return val.count(character)

@check_param_num
@check_type
def itemAt(name, val, index):
    if index >= len(val):
        raise mylang_errors.IndexOutOfBoundsError("index passed ({}) is greater than length of value '{}' ({})".format(index, name, len(val)))
    return val[index]

@check_param_num
@check_type
def indexOf(name, val, target):
    indices = [i for i, a in enumerate(val) if a == target]
    if not indices:
        raise mylang_errors.CollectionDoesNotContainItem("value '{}' does not contain '{}'".format(name, target))
    return indices[0]

@check_param_num
@check_type
def contains(name, val, target):
    return target in val

@check_param_num
@check_type
def run(name, val, start, end):
    if max([start, end]) >= len(val):
        raise mylang_errors.IndexOutOfBoundsError("index passed ({}) is greater than the length of '{}' ({})".format(max([start, end]), name, len(val)))
    if isinstance(val, str):
        return val[start:end]
    return ArrayList([], filled = val[start:end])

@check_param_num
@check_type
def length(name, val):
    return len(val)

@check_param_num
@check_type
def join(name, val, spacer):
    for i in val:
        if not isinstance(i, str):
            raise mylang_errors.CastingError("Cannot convert type '{}' to type '{}'".format(getattr(i, 'rep', type(i).__name__), str.__name__))
    return spacer.join(val.contents)

builtin_methods = {'str':{'run':run, 'contains':contains, 'indexOf':indexOf, 'itemAt':itemAt, 'occurs':occurs, 'splice':splice, 'sub':sub, 'reverse':reverse, 'length':length, 'updateAt':updateAt}, 'int':{'toFloat':toFloat, 'exp':exp}, 'ArrayList':{'run':run, 'contains':contains, 'indexOf':indexOf, 'itemAt':itemAt, 'occurs':occurs, 'reverse':reverse, 'length':length, 'updateAt':updateAt, 'addBack':addBack, 'addFront':addFront, 'extendFront':extendFront, 'extendBack':extendBack, 'removeAt':removeAt, 'removeItem':removeItem, 'join':join}, 'float':{'exp':exp}, 'bool':{'exp':exp}}


def get_file_path(path, current = os.getcwd().split('/')[1:]):
    check_next = next(path, None)
    if not check_next:
        return '/{}'.format('/'.join(current)), mylang_config.ImportAll
    if check_next.type == 'DOT':
        check_test = next(path, None)
        if not check_test:
            raise mylang_errors.InvalidSyntax("At line {}, near '{}': expecting directory or filename".format(check_test.value.line_number, check_next.value.value))
        if check_test.type == 'DOT':
            return get_file_path(path, current = current[:-1])
        if check_test.type == 'VARIABLE':
            return get_file_path(path, current = current+[check_test.value.value])
    if check_next.type == 'VARIABLE':
        check_test = next(path, None)
        if not check_test:
            return '/{}'.format('/'.join(current+["{}.txt".format(check_next.value.value)])), mylang_config.ObjectifyImport
        if check_test.type == 'STAR':
            return '/{}'.format('/'.join(current+["{}.txt".format(check_next.value.value)])), mylang_config.ImportAll
        return get_file_path(path, current = current+[check_next.value.value])
    if check_next.type == 'STAR':
        return '/{}'.format('/'.join(current+["{}.txt".format(check_next.value.value)])), mylang_config.ImportAll
