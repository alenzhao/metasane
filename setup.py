#!/usr/bin/env python

__author__ = "Jai Ram Rideout"
__credits__ = ["Jai Ram Rideout", "Jose Clemente"]
__license__ = "BSD"
__version__ = "0.0.1-dev"
__maintainer__ = "Jai Ram Rideout"
__email__ = "jai.rideout@gmail.com"

from setuptools import setup
from glob import glob

# classes/classifiers code adapted from pyqi:
# https://github.com/bipy/pyqi/blob/master/setup.py
#
# PyPI's list of classifiers can be found here:
# https://pypi.python.org/pypi?%3Aaction=list_classifiers
classes = """
    Development Status :: 1 - Planning
    License :: OSI Approved :: BSD License
    Topic :: Scientific/Engineering :: Information Analysis
    Programming Language :: Python
    Programming Language :: Python :: 2.7
    Programming Language :: Python :: Implementation :: CPython
    Operating System :: OS Independent
    Operating System :: POSIX :: Linux
    Operating System :: MacOS :: MacOS X
"""
classifiers = [s.strip() for s in classes.split('\n') if s]

long_description = ("metasane (canonically pronounced \"meta sane\") is a "
                    "lightweight, BSD-licensed, pure-Python tool to validate "
                    "the sanity of spreadsheet-based metadata.")

setup(name='metasane',
      version=__version__,
      license=__license__,
      description='metasane: a tool to validate metadata sanity',
      long_description=long_description,
      author=__author__,
      author_email=__email__,
      maintainer=__maintainer__,
      maintainer_email=__email__,
      url='https://github.com/clemente-lab/metasane',
      packages=['metasane'],
      scripts=glob('scripts/*'),
      install_requires=['python-dateutil'],
      extras_require={'test': ['nose']},
      classifiers=classifiers)
