import functools
def verify_parameter(**kwargs):
    def overriding_method(f):
        def wrapper(cls, *args):
            if len(args) > kwargs.get('max_number', 5):
                raise mylang_errors.ParameterSytnaxError("scope '{}' can only take a maximum of {} parameters, but recieved {}. To fix these, please update the mylang_settings.txt file".format(cls.__scope_name__, kwargs.get('max_number', 5), len(args)))
            return f(cls, *args)
        return wrapper
    return overriding_method
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
