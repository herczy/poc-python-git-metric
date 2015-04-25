from .. import ast, Table


def metric(dataset):
    res = []
    for key, values in dataset.methods.uniq('path method modid').group_by('path method'):
        complexities = [ast.complexity(row['node']) for row in values]
        res.append(key + (complexities,))

    return Table.from_list(('path', 'method', 'complexity'), res) \
        .sort_by('complexity', desc=True) \
        .map_column('complexity', lambda cl: ' <- '.join(str(c) for c in cl))
