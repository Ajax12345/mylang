class IllegialPrecedence(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)

class VariableNotDeclared(Exception):
    pass

class IncompatableTypes(Exception):
    pass

class TooManyParamemters(Exception):
    pass

class ParameterSytnaxError(Exception):
    pass

class ReachedEndOfScopeBlock(Exception):
    pass

class InvalidScopeBlock(Exception):
    pass

class AttributeNotFound(Exception):
    pass

