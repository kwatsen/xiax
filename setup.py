#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
import sys
from glob import glob
from shutil import rmtree
from setuptools import setup, find_packages, Command

# a combination of:
#  -  https://realpython.com/pypi-publish-python-package
#  -  https://github.com/kennethreitz/setup.py/blob/master/setup.py

NAME = "xiax"
DESCRIPTION = "Extract or insert artwork/sourcecode from/to an `xml2rfc` XML document."
URL = 'https://github.com/kwatsen/xiax'
EMAIL = 'kent@watsen.net'
AUTHOR = 'Kent Watsen'
REQUIRES_PYTHON = '>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*'

REQUIRED = [ 'lxml', 'gitpython' ]

EXTRAS = { }

HERE = os.path.abspath(os.path.dirname(__file__))


# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
try:
    with io.open(os.path.join(HERE, 'README.md'), encoding='utf-8') as f:
        README = '\n' + f.read()
except FileNotFoundError:  # "NameError: name 'FileNotFoundError' is not defined" is a PYTHON 2.7 only issue!
    README = DESCRIPTION


# Load the package's __version__.py module as a dictionary.
about = {}
with open(os.path.join(HERE, 'src', NAME, '__version__.py')) as f:
    exec(f.read(), about)


class UploadCommand(Command):
    """Support setup.py upload."""

    description = 'Build and publish the package.'
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds...')
            rmtree(os.path.join(HERE, 'dist'))
        except OSError:
            pass

        self.status('Building Source and Wheel (universal) distribution...')
        os.system('{0} setup.py sdist bdist_wheel --universal'.format(sys.executable))

        self.status('Uploading the package to PyPI via Twine...')
        os.system('twine upload dist/*')

        self.status('Pushing git tags...')
        os.system('git tag v{0}'.format(about['__version__']))
        os.system('git push --tags')
        
        sys.exit()


# Where the magic happens:
setup(
    url=URL,
    name=NAME,
    license='ISC',
    version=about['__version__'],
    description=DESCRIPTION,
    long_description=README,
    long_description_content_type='text/markdown',
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    packages=find_packages("src"),
    package_dir = {"": "src"},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    #packages=['src/xiax'],
    #package_dir={'xiax': 'src/xiax'},
    package_data={'xiax': ['data/*.rng']},
    include_package_data = True,
    keywords = ["ietf", "rfc", "artwork", "sourcecode", "extraction", "insertion", "folding", "unfolding"],
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    setup_requires = ["pytest-runner"],
    tests_require = ["pytest"],
    entry_points = {
        "console_scripts": [
            "xiax = xiax:main",
        ]
    },
    classifiers = [
      # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
      "Development Status :: 2 - Pre-Alpha",
      "License :: OSI Approved :: ISC License (ISCL)",
      "Programming Language :: Python :: 3.7",
      "Programming Language :: Python :: 3.6",
      "Programming Language :: Python :: 3.5",
      "Programming Language :: Python :: 3.4",
      "Programming Language :: Python :: 2.7"
    ],
    # $ setup.py publish support.
    cmdclass={
        'upload': UploadCommand,
    },
)

