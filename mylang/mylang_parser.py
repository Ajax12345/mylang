import mylang_tokenizer
import collections
import mylang_errors
import string

class Parser:
    def __init__(self, token_list):
        print(token_list)
        self.token_list = iter(map(iter, token_list))
        self.vals = []
        self.variables = {}
        self.parse()
        print(self.variables)
    def parse(self):
        current_line = next(self.token_list, None)
        if current_line:
            start = next(current_line)
            if start.type == 'VARIABLE':
                checking = next(current_line)
                start.value.isValid(checking.value)
                if checking.type == 'ASSIGN':
                    to_store = self.parse_assign(current_line)
                    self.variables[start.value.value] = to_store
            self.parse()
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
