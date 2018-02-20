import networkx as nx
import matplotlib.pyplot as plt
import datetime
import collections
import itertools
import abc

class AbstractSyntaxTree:
    '''
        traceparser is class by which a simple recursive descent compiler can be traced throughout all stages of parsing
        ex:
        import trace_parser
        t = trace_parser.Trace()
        def parse_expression():
            #main method
            t.add_top_level(current_line)
            parse_assign_statement(current_line[1:])
            parse_compute_statement(current_line[2:])
        @t.trace
        def parse_assign_statement(line):
            pass
        @t.trace
        def parse_compute_statement(line):
            pass
    '''
    __metaclass__ = abc.ABCMeta
    @abc.abstractmethod
    def add_top_level(self, line):
        pass
    @abc.abstractmethod
    def trace(self, header):
        pass
    @abc.abstractmethod
    def draw_graph(self, d):
        pass
    @abc.abstractmethod
    def show_graph(self, medium = 'on_screen', **kwargs):
        pass

class Trace(AbstractSyntaxTree):
    def __init__(self, name = None):
        current_time = datetime.datetime.now()
        self.graph = name if name else '<tracer graph {}/{}/{}>'.format(current_time.month, current_time.day, current_time.year)
        self.g = nx.DiGraph()
        self.tree = {}
        self.top_nodes = []
    def add_top_level(self, line):
        self.top_nodes = []
        current_line = ' '.join(i.value.value for i in line)
        self.tree[current_line] = None
        self.top_nodes.append(current_line)
    def trace(self, header):
        def wrapper(cls, *args):
            print args
            second, args1 = itertools.tee(args[0] if len(args) == 1 else args[1])
            current = ' '.join(i.value.value for i in args1)
            self.tree = self.__class__.update_structure(self.tree, self.top_nodes, self.top_nodes, current)
            print 'self.tree', self.tree
            self.top_nodes.append(current)
            return header(cls, *args)

        return wrapper
    def draw_graph(self, d):
        print 'got in here'
        print 'd is', d

        for a, b in d.items():
            self.g.add_node(a)

            yield a
            if b:
                for node in self.draw_graph(b):

                    self.g.add_edge(a, node)

    def show_graph(self, medium = 'on_screen', **kwargs):

        final_data= list(self.draw_graph(self.tree))
        print 'self.tree here', self.tree

        if medium == 'on_screen':
            nx.draw(self.g, with_labels = True)
            plt.show()
        else:
            plt.savefig(kwargs.get('filename', self.name))

    @staticmethod
    def update_structure(d, final_nodes, current, to_add):
        return {a:{to_add:None} if not b and a == current[0] else b if not isinstance(b, dict) or a not in final_nodes else Trace.update_structure(b, final_nodes, current[1:], to_add) for a, b in d.items()}
