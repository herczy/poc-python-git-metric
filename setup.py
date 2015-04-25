#!/usr/bin/env python3

import sys

try:
    from setuptools import setup

except ImportError:
    from distutils.core import setup

setup(
    name="pygitmetric",
    description="Git-aware code metrics for Python repositories (POC)",
    long_description= """\
Calculate some metrics of a Python code based on the git repository and
the changes committed. This way we can calculate how a code base has changed.

Some example metrics are:
 * How often do specific classes and functions change?
 * What functions change often together?
 * How complex are the changes on a file?
 * etc.

PyGitMetric provides an API for writing small scripts to implement other
metrics.
""",
    license="LGPLv2+",
    version="1.0.0",
    author="Viktor Hercinger",
    author_email="viktor.hercinger@balabit.com",
    maintainer="Viktor Hercinger",
    maintainer_email="viktor.hercinger@balabit.com",
    zip_safe=True,
    use_2to3=False,
    entry_points={
        'console_scripts': [
            'pygitmetric = pygitmetric.__main__:main'
        ]
    },
    packages=['pygitmetric', 'pygitmetric.metric']
)
