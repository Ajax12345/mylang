import mylang_errors
import re
builtin_checker = {'reverse':[0, [None], [None], False], 'sub':[2, [str, str], ['to_replace', 'target'], True], 'exp':[1, [int], ['pow'], True], 'toFloat':[1, [int], ['denominator'], True], 'splice':[1, [str], ['split_at'], True], 'occurs':[1, [], ['character'], False], 'itemAt':[1, [int], ['index'], False], 'indexOf':[1, [], ['target'], False], 'contains':[1, [], ['target'], False], 'run':[2, [int, int], ['start', 'end'], True]}

def check_param_num(f):
    def wrapper(name, val, *args):
        if builtin_checker[f.__name__][0] != len(args):
            raise mylang_errors.TooManyParamemters("procedure '{}' expects {} parameters, but recieved {}".format(f.__name__, builtin_checker[f.__name__][0], len(args)))
        if args and builtin_checker[f.__name__][-1]:
            for i, [a, b] in enumerate(zip(args, builtin_checker[f.__name__][1])):
                if type(a) != b:
                    raise mylang_errors.InvalidParameterType("procedure '{}' parameter '{}' expects value of type '{}', but recieved value of type '{}'".format(f.__name__, builtin_checker[f.__name__][2][i], b.__name__, a.__name__))
        return f(name, val, *args)
    return wrapper


@check_param_num
def reverse(name, val):
    return val[::-1]

@check_param_num
def sub(name, val, to_replace, target):
    return re.sub(to_replace, target, val)

@check_param_num
def exp(name, val, raise_to):
    return pow(val, raise_to)

@check_param_num
def toFloat(name, val, denominator):
    return val/float(denominator)

@check_param_num
def splice(name, val, split_at):
    return val.split(split_at)

@check_param_num
def occurs(name, val, character):
    return val.count(character)

@check_param_num
def itemAt(name, val, index):
    if index >= len(val):
        raise mylang_errors.IndexOutOfBoundsError("index passed ({}) is greater than length of value '{}' ({})".format(index, name, len(val)))
    return val[index]

@check_param_num
def indexOf(name, val, target):
    indices = [i for i, a in enumerate(val) if a == target]
    if not indices:
        raise mylang_errors.CollectionDoesNotContainItem("value '{}' does not contain '{}'".format(name, target))
    return indices[0]

@check_param_num
def contains(name, val, target):
    return target in val

@check_param_num
def run(name, val, start, end):
    if max([start, end]) >= len(val):
        raise mylang_errors.IndexOutOfBoundsError("index passed ({}) is greater than the length of '{}' ({})".format(max([start, end]), name, len(val)))
    return val[start:end]


builtin_methods = {'str':{'run':run, 'contains':contains, 'indexOf':indexOf, 'itemAt':itemAt, 'occurs':occurs, 'splice':splice, 'sub':sub, 'reverse':reverse}, 'int':{'toFloat':toFloat, 'exp':exp}, 'list':{'run':run, 'contains':contains, 'indexOf':indexOf, 'itemAt':itemAt, 'occurs':occurs, 'reverse':reverse}}
