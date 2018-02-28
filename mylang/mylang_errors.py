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

class ReachedEndOfProcedureBlock(Exception):
    pass

class InvalidStartOfProcedureBlock(Exception):
    pass

class InvalidScopeBlock(Exception):
    pass

class AttributeNotFound(Exception):
    pass

class NotYetSupportedError(Exception):
    pass

class InvalidEndOfDeclaration(Exception):
    pass

class InvalidProcedureReturnType(Exception):
    pass

class NoProcedureDeclared(Exception):
    pass

class InvalidParameterType(Exception):
    pass
