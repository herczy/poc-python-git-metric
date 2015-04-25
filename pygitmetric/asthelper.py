import ast


def equal(a0, a1):
    if type(a0) != type(a1):
        return False

    if isinstance(a0, list):
        if len(a0) != len(a1):
            return False

        return all(equal(item0, item1) for item0, item1 in zip(a0, a1))

    elif isinstance(a0, ast.AST):
        for field in a0._fields:
            if not equal(getattr(a0, field), getattr(a1, field)):
                return False

        return True

    else:
        return a0 == a1


def complexity(node):
    if isinstance(node, list):
        return sum(complexity(item) for item in node)

    if isinstance(node, ast.AST):
        return sum(complexity(getattr(node, field)) for field in node._fields)

    return 1
