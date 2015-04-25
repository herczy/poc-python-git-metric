import os.path
import collections
import ast
import pickle


class Dataset(collections.Mapping):
    DEFAULT_CACHE_PATH = os.path.join(os.getenv('HOME'), '.cache', 'pygitmetric')

    def __init__(self, ref, *, cache_path=None):
        if cache_path is None:
            cache_path = self.DEFAULT_CACHE_PATH

        if not os.path.isdir(cache_path):
            os.makedirs(cache_path)

        self.__ref = ref
        self.__files = {}
        self.__blobs = {}

        self._build(cache_path)

    def __len__(self):
        return len(self.__files)

    def __iter__(self):
        return iter(self.__files)

    def __getitem__(self, key):
        return self.__files[key]

    def _build(self, cache_path):
        item_path = os.path.join(cache_path, self.__ref.commit.hexsha)
        if not os.path.isfile(item_path):
            self._build_from_scratch()

            with open(item_path, 'wb') as cached:
                pickle.dump(
                    (self.__files, self.__blobs),
                    cached
                )

        else:
            with open(item_path, 'rb') as cached:
                self.__files, self.__blobs = pickle.load(cached)

    def _build_from_scratch(self):
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

    def _build_tree(self, commit, tree, path=()):
        for item in tree:
            item_path = path + (item.name,)
            self._build_object(commit, item, path=item_path)

    def _build_object(self, commit, item, path):
        if item.type == 'blob':
            self._build_blob(commit, item, path=path)

        elif item.type == 'tree':
            self._build_tree(commit, item, path=path)

    def _build_blob(self, commit, blob, path):
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

        commit_info = _CommitInfo(commit.hexsha, commit.authored_date)
        blob_info = _BlobInfo(blob.hexsha)
        self.__files[path].append(_FileInfo(commit_info, blob_info, parsed))


_FileInfo = collections.namedtuple('_FileInfo', 'commit blob parsed')
_CommitInfo = collections.namedtuple('_CommitInfo', 'hexsha authored_date')
_BlobInfo = collections.namedtuple('_BlobInfo', 'hexsha')
