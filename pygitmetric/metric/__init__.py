import sys


def get_metric(name):
    try:
        return _get_metric('pygitmetric.metric.{}'.format(name))

    except:
        return _get_metric(name)


def run_metric(repo, name):
    return get_metric(name)(repo)


def _get_metric(name):
    module = __import_module(name)
    return getattr(module, 'metric')


def __import_module(name):
    try:
        __import__(name)
        return sys.modules[name]

    except ImportError as exc:
        raise ImportError('Could not load metric module {!r}'.format(name))
