import collections
import os.path
import pickle
import functools
import itertools


class Table(collections.Sequence):
    @classmethod
    def from_list(cls, headers, data):
        return cls(List(headers, data))

    def __init__(self, dataset):
        self.__dataset = dataset

    @property
    def dataset(self):
        return self.__dataset

    @property
    def headers(self):
        return self.__dataset.headers

    def __iter__(self):
        return (Row(self, row) for row in self.__dataset)

    def __len__(self):
        return len(self.__dataset)

    def __getitem__(self, key):
        if isinstance(key, slice):
            return type(self)(Slice(self.__dataset, key))

        return Row(self.__dataset, self.__dataset[key])

    def __prepare_columns(self, columns):
        if isinstance(columns, str):
            return tuple(col for col in columns.split(' ') if col)

        return tuple(columns)

    def group_by(self, columns):
        columns = self.__prepare_columns(columns)
        groups = {}

        for row in self:
            key = tuple(row[col] for col in columns)
            if key not in groups:
                groups[key] = List(self.headers, [])

            groups[key].add_row(row)

        for key, rows in groups.items():
            yield key, Table(rows)

    def sort(self, key=None, desc=False):
        res = list(self)
        res.sort(key=key, reverse=desc)

        return type(self)(List(self.headers, res))

    def sort_by(self, columns, desc=False):
        columns = self.__prepare_columns(columns)

        def _key(row):
            return tuple(row[col] for col in columns)

        return self.sort(_key, desc)

    def select(self, condition):
        @view(*self.headers)
        def filter():
            for row in self:
                if condition(Row(self.__dataset, row)):
                    yield row

        return type(self)(filter())

    def uniq(self, columns):
        columns = self.__prepare_columns(columns)

        @view(*self.headers)
        def uniq():
            seen = set()

            for row in self:
                key = tuple(row[col] for col in columns)
                if key in seen:
                    continue

                yield row
                seen.add(key)

        return type(self)(uniq())

    def map(self, headers, function):
        @view(*headers)
        def mapper():
            for row in self:
                yield tuple(function(row))

        return Table(mapper())

    def map_column(self, column, function):
        col_index = self.headers.index(column)

        def _mapper(row):
            for index, item in enumerate(row):
                if index == col_index:
                    yield function(item)

                else:
                    yield item

        return self.map(self.headers, _mapper)

    def join(self, other, join_on_columns):
        join_on_columns = tuple(self.__prepare_columns(join_on_columns))

        headers_self = tuple(
            'self.{}'.format(h) for h in self.headers if h not in join_on_columns
        )
        headers_other = tuple(
            'other.{}'.format(h) for h in other.headers if h not in join_on_columns
        )

        def _filter_rows(row):
            return [row[key] for key in join_on_columns]

        def _get_selector(values):
            def _select(row):
                return _filter_rows(row) == values

            return _select

        @view(*(join_on_columns + headers_self + headers_other))
        def join_dataset():
            for row in self:
                key = _filter_rows(row)

                left_side = key + [row[key] for key in self.headers if key not in join_on_columns]
                for other_row in other.select(_get_selector(key)):
                    yield left_side + [other_row[key] for key in other.headers if key not in join_on_columns]


        return Table(join_dataset())


class Data(collections.Sequence):
    def __init__(self, headers):
        self.__headers = tuple(str(h) for h in headers)

    @property
    def headers(self):
        return self.__headers


class List(Data):
    def __init__(self, headers, data):
        super().__init__(headers)

        self.__data = [self.__normalize_row(row) for row in data]

    def add_row(self, row):
        self.__data.append(self.__normalize_row(row))

    def __normalize_row(self, row):
        if isinstance(row, (str, bytes)) or not isinstance(row, collections.Sequence):
            raise TypeError('Rows must be non-string and -bytes sequences')

        row = tuple(row)
        if len(row) != len(self.headers):
            raise ValueError('Row must have {} columns, not {}'.format(len(self.headers), len(row)))

        return row

    def __len__(self):
        return len(self.__data)

    def __getitem__(self, key):
        return self.__data[key]


class _View(Data):
    def __init__(self, headers, iterator):
        super().__init__(headers)

        self.__loaded = []
        self.__iterator = iterator

    def __iter__(self):
        for item in self.__loaded:
            yield item

        if self.__iterator is not None:
            for item in self.__iterator:
                self.__loaded.append(item)
                yield item

            self.__iterator = None

    def __len__(self):
        self.__load_full_iterator()
        return len(self.__loaded)

    def __getitem__(self, key):
        self.__load_partial_iterator(key)
        return self.__loaded[key]

    def __load_full_iterator(self):
        if self.__iterator is None:
            return

        for item in self.__iterator:
            self.__loaded.append(item)

        self.__iterator = None

    def __load_partial_iterator(self, key):
        if self.__iterator is None:
            return

        if isinstance(key, slice):
            length = key.stop

        else:
            length = key + 1

        if len(self.__loaded) >= length:
            return

        for item in self.__iterator:
            self.__loaded.append(item)
            if len(self.__loaded) >= length:
                return

        self.__iterator = None


class Slice(_View):
    def __init__(self, base, slice):
        super().__init__(
            base.headers,
            itertools.islice(base, slice.start, slice.stop, slice.step)
        )


def view(*headers):
    def _decorate(func):
        @functools.wraps(func)
        def _constructor(*args, **kwargs):
            return _View(headers, func(*args, **kwargs))

        return _constructor

    return _decorate


class Row(collections.Sequence):
    def __init__(self, dataset, row):
        self.__dataset = dataset
        self.__row = row

    def __len__(self):
        return len(self.__row)

    def __getitem__(self, key):
        if isinstance(key, str):
            return self.__row[self.__dataset.headers.index(key)]

        return self.__row[key]


def print_itemized_table(table):
    for row in table:
        for name, col in zip(table.headers, row):
            print('{}: {}'.format(name, col))

        print()


def print_fancy_table(table):
    widths = [len(h) for h in table.headers]
    rows = [tuple(table.headers)]
    for row in table:
        rows.append([str(v) for v in row])
        widths = [max(w, len(r)) for w, r in zip(widths, rows[-1])]

    rows.insert(1, ('=' * width for width in widths))

    for row in rows:
        for width, item in zip(widths, row):
            print(item + (' ' * (width - len(item))), end=' ')
        print()
