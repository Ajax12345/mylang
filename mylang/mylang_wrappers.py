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
