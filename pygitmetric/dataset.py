import collections
import ast


class Dataset(collections.Mapping):
    def __init__(self, ref):
        self.__ref = ref
        self.__files = {}
        self.__blobs = {}

        self._build()

    def __len__(self):
        return len(self.__files)

    def __iter__(self):
        return iter(self.__files)

    def __getitem__(self, key):
        return self.__files[key]

    def _build(self):
        self._build_commit(self.__ref.commit)
        unprocessed = self.__files
        self.__files = {}

        for name, changes in unprocessed.items():
            self.__files[name] = self._filter_unchanged(reversed(changes))

    def _filter_unchanged(self, changes):
        prev_blob_hex = None
        res = []
        for change in changes:
            if prev_blob_hex == change.blob.hexsha:
                continue

            res.append(change)
            prev_blob_hex = change.blob.hexsha

        return res

    def _build_commit(self, commit):
        self._build_commit_tree(commit)
        if commit.parents:
            self._build_commit(commit.parents[0])

    def _build_commit_tree(self, commit):
        for item in commit.tree:
            self._build_object(commit, item, path=(item.name,))

    def _build_tree(self, commit, tree, *, path=()):
        for item in tree:
            item_path = path + (item.name,)
            self._build_object(commit, item, path=item_path)

    def _build_object(self, commit, item, *, path):
        if item.type == 'blob':
            self._build_blob(commit, item, path=path)

        elif item.type == 'tree':
            self._build_tree(commit, item, path=path)

    def _build_blob(self, commit, blob, *, path):
        if blob.mime_type != 'text/x-python':
            return

        if blob.hexsha not in self.__blobs:
            try:
                self.__blobs[blob.hexsha] = ast.parse(blob.data_stream.read())

            except:
                self.__blobs[blob.hexsha] = None

        parsed = self.__blobs[blob.hexsha]
        if parsed is None:
            return

        path = '/'.join(path)
        if path not in self.__files:
            self.__files[path] = []

        self.__files[path].append(_FileInfo(commit, blob, parsed))


_FileInfo = collections.namedtuple('_FileInfo', 'commit blob parsed')
