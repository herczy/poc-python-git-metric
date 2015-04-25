import os.path
import git

from .dataset import dataset
from .method import methods
from .table import print_itemized_table, Table, List
from . import asthelper as ast


class Repo(Table):
    @classmethod
    def load(cls, path, ref=None):
        repo = git.Repo(path)
        if ref is not None:
            ref = repo.heads[ref]

        else:
            ref = repo.head

        return cls(dataset(ref))

    @property
    def methods(self):
        return Table(methods(self.dataset))

    def select_path(self, path):
        def cond(row):
            return os.path.relpath(row['path'], path)

        return self.select(cond)
