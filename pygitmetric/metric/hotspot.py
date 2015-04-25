from .. import Table


def metric(dataset):
    res = []
    for (path,), values in dataset.sort_by('time', desc=True).group_by('path'):
        if len(values) <= 1:
            continue

        times = [row['time'] for row in values]
        res.append((path, (max(times) - min(times)) / len(times)))

    return (
        Table.from_list(('path', 'avgtime'), res)
            .sort_by('avgtime')
            .map_column('avgtime', '{:.1f}'.format)
    )
