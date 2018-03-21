import functools
import mylang_errors

def verify_parameter(**kwargs):
    def overriding_method(f):
        def wrapper(cls, *args):
            if len(args) > kwargs.get('max_number', 5):
                raise mylang_errors.ParameterSytnaxError("scope '{}' can only take a maximum of {} parameters, but recieved {}. To fix these, please update the mylang_settings.txt file".format(cls.__scope_name__, kwargs.get('max_number', 5), len(args)))
            return f(cls, *args)
        return wrapper
    return overriding_method

def verify_procedure_parameter(**kwargs):
    def parser_wrapper(f):
        def wrapper(cls, *args):

            parameters, warnings, return_types = f(cls, *args)
            if len(parameters) > kwargs.get('max_param_val', 5):
                raise mylang_errors.TooManyParamemters("At line {}, near '{}'. Procedure '{}' takes {} parameters, but configure to take {}".format(cls.possible_name.value.line_number, 'procedure', cls.possible_name.value.value, kwargs.get('max_param_val', 5), len(function_params)))
            if return_types and return_types not in kwargs.get('valid_return_types'):
                raise mylang_errors.InvalidProcedureReturnType("At line {}, near '{}': invalid return type".format(cls.possible_name.value.line_number, cls.possible_name.value.value))
            return parameters, warnings, return_types


        return wrapper
    return parser_wrapper

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


def verify_passed_types(f):
    def wrapper(cls, *args):
        print 'ARGS', args
        print 'CLS', cls.params
        if len(args) != len(cls.params):
            raise mylang_errors.TooManyParamemters("Procedure '{}' expected {} parameters, but was passed {}".format(cls.name, len(cls.params), len(args)))
        if args:
            for a, b in zip(args, cls.params):
                if isinstance(b, list):
                    if getattr(a, 'rep', type(a).__name__) != b[-1]:
                        raise mylang_errors.InvalidParameterType("In procedure '{}': parameter '{}' requires a value of type '{}', recieved '{}'".format(cls.name, b[0], {'int':int, 'string':str, 'bool':bool}[b[-1]].__name__, type(a).__name__))
        a, b = f(cls, *args)
        if a and cls.return_type and getattr(a, 'rep', type(a).__name__) != cls.return_type:
            raise mylang_errors.InvalidProcedureReturnType("Procedure '{}' can only return type '{}', but caught '{}'".format(cls.name, cls.return_type, getattr(a, 'rep', type(a).__name__)))
        return a, b
    return wrapper


def check_existence(**kwargs):
    '''simple wrapper to check for different types of variables existing in the current namespace'''
    def the_method(f):
        def wrapper(cls, val):
            return f(cls, val)
        return wrapper
    return the_method


def check_private(**kwargs):
    def pass_method(f):
        def wrapper(cls, val_name):
            print 'val_name here', val_name
            if val_name in cls.private_variables:
                if kwargs.get('suppress'):
                    raise mylang_errors.VariableNotDeclared("Scope value '{}' not declared".format(val_name))
                raise mylang_errors.PrivateVariableDeclaration("Scope value '{}' is a private member variable".format(val_name))
            return f(cls, val_name)
        return wrapper
    return pass_method

def verify_private_procedure(**kwargs):
    def pass_name_method(f):
        def wrapper(cls, name):
            print 'in verify_private_procedure for checking {}, for {}'.format(name.is_private, name.name)
            if name.is_private:
                if kwargs.get('suppress'):
                    raise mylang_errors.VariableNotDeclared("procedure '{}' not declared".format(name.name))
                raise mylang_errors.PrivateVariableDeclaration("procedure '{}' is private".format(name.name))
        return wrapper
    return pass_name_method

def verify_parameter_arg_length(**kwargs):
    def the_method(f):
        @functools.wraps(f)
        def wrapper(cls, *args):
            if len(args) > kwargs.get('max_procedure_params'):
                raise mylang_errors.TooManyParamemters("Procedure '{}' recieved {} paramters, but expected at least {}".format(cls.name, len(args), kwargs.get('max_procedure_params')))
            return f(cls, *args)
        return wrapper
    return the_method

def verify_switch_param_num(f):
    def wrapper(cls, params):
        if len(params) > 1:
            raise mylang_errors.TooManyParamemters("procedure 'switch' takes 1 paramter, but recieved {}".format(len(params)))
        return f(cls, params[0])
    return wrapper
