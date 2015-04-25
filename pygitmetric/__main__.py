import argparse
from . import Repo, print_itemized_table, print_fancy_table, run_metric


def main():
    parser = argparse.ArgumentParser(description='Python repo metrics')

    parser.add_argument(
        '-p', '--path', default='.',
        help='Path to the git repository (default: %(default)s)'
    )
    parser.add_argument(
        '-r', '--ref', default=None,
        help='Reference to check (default: HEAD)'
    )
    parser.add_argument(
        '-m', '--metric', default='complexity',
        help='Metric module to run (default: %(default)s)'
    )
    parser.add_argument(
        '-F', '--fancy', action='store_true',
        help='Print data in a fancy table'
    )

    options = parser.parse_args()
    repo = Repo.load(options.path, options.ref)
    res = run_metric(repo, options.metric)

    if options.fancy:
        print_fancy_table(res)

    else:
        print_itemized_table(res)


if __name__ == '__main__':
    main()
