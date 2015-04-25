import os.path
import collections
import ast
import pickle

from .table import Table, Data, view


def dataset(ref):
    return _DatasetCollector(ref).dataset()


class _DatasetCollector:
    def __init__(self, ref):
        self.__dataset = []
        self.__ref = ref
        self.__blobs = {}
        self.__last_index = 0

    @view('index', 'path', 'blob', 'commit', 'time', 'parsed')
    def dataset(self):
        return self._build_commit(self.__ref.commit)

    def _build_commit(self, commit):
        yield from self._build_commit_tree(commit)
        if commit.parents:
            yield from self._build_commit(commit.parents[0])

    def _build_commit_tree(self, commit):
        for item in commit.tree:
            yield from self._build_object(commit, item, path=(item.name,))

    def _build_tree(self, commit, tree, path=()):
        for item in tree:
            item_path = path + (item.name,)
            yield from self._build_object(commit, item, path=item_path)

    def _build_object(self, commit, item, path):
        if item.type == 'blob':
            yield from self._build_blob(commit, item, path=path)

        elif item.type == 'tree':
            yield from self._build_tree(commit, item, path=path)

    def _build_blob(self, commit, blob, path):
        if blob.mime_type == 'text/x-python':
            if blob.hexsha not in self.__blobs:
                try:
                    self.__blobs[blob.hexsha] = ast.parse(blob.data_stream.read())

                except:
                    self.__blobs[blob.hexsha] = None

            parsed = self.__blobs[blob.hexsha]
            if parsed is not None:
                path = '/'.join(path)
                yield (
                    self.__last_index,
                    path,
                    blob.hexsha,
                    commit.hexsha,
                    commit.authored_date,
                    parsed
                )
                self.__last_index += 1
