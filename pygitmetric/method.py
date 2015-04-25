import ast
import collections
import contextlib

from . import asthelper


class Methods(collections.Mapping):
    def __init__(self, dataset):
        self.__dataset = dataset
        self.__methods = self.__process_methods()

    def __len__(self):
        return len(self.__methods)

    def __iter__(self):
        return iter(self.__methods)

    def __getitem__(self, key):
        return self.__methods[key]

    def __process_methods(self):
        res = {}

        for name, changes in self.__collect_methods().items():
            prev_node = None
            res_change_list = []
            for info, node in changes:
                if prev_node is not None and asthelper.equal(prev_node, node):
                    continue

                res_change_list.append(ChangeInfo(info, node))
                prev_node = node

            res[name] = res_change_list

        return res

    def __collect_methods(self):
        methods = {}
        changes = {}

        for name, infos in self.__dataset.items():
            for info in infos:
                for method, node in self.__collect_change_methods(info):
                    fqdn = (name, method)
                    methods.setdefault(fqdn, [])
                    methods[fqdn].append((info, node))

        res = collections.OrderedDict()
        keyorder = sorted(methods.keys())
        for key in keyorder:
            res[key] = methods[key]

        return res

    def __collect_change_methods(self, info):
        method_collector = _CollectMethods()
        method_collector.visit(info.parsed)

        for name, node in method_collector.methods.items():
            yield name, node


ChangeInfo = collections.namedtuple('ChangeInfo', 'info node')


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
