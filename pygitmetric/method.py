import ast
import collections
import contextlib

from .table import view
from . import asthelper


@view('modid', 'path', 'method', 'commit', 'time', 'node')
def methods(dataset):
    for row in dataset:
        collector = _CollectMethods()
        collector.visit(row['parsed'])

        for method, node in collector.methods.items():
            yield row['blob'], row['path'], method, row['commit'], row['time'], node


class _CollectMethods(ast.NodeVisitor):
    def __init__(self):
        super().__init__()

        self.methods = {}
        self.namespace = []

    def visit_ClassDef(self, node):
        with self._append_namespace(node.name):
            self.generic_visit(node)

    def visit_FunctionDef(self, node):
        with self._append_namespace(node.name):
            fullname = '.'.join(self.namespace)
            self.methods[fullname] = node

    @contextlib.contextmanager
    def _append_namespace(self, name):
        self.namespace.append(name)
        try:
            yield

        finally:
            self.namespace.pop()
