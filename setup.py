#!/usr/bin/env python3

# FIXME:
#
# - REENABLE HG_STARTUP BENCHMARK.
# - REENABLE GENSHI BENCHMARK.
#
# Update dependencies:
#
#  - python3 -m pip install --user --upgrade pip-tools
#  - git clean -fdx  # remove all untracked files!
#  - (pip-compile --upgrade -o requirements.txt requirements.in)
#
# Prepare a release:
#
#  - git pull --rebase
#  - Remove untracked files/dirs: git clean -fdx
#  - maybe update version in pyperformance/__init__.py and doc/conf.py
#  - set release date in doc/changelog.rst
#  - git commit -a -m "prepare release x.y"
#  - run tests: tox --parallel auto
#  - git push
#  - check the CI status:
#    https://github.com/python/pyperformance/actions
#
# Release a new version:
#
#  - git tag VERSION
#  - git push --tags
#  - Remove untracked files/dirs: git clean -fdx
#  - python3 setup.py sdist bdist_wheel
#  - twine upload dist/*
#
# After the release:
#
#  - set version to n+1: pyperformance/__init__.py and doc/conf.py
#  - git commit -a -m "post-release"
#  - git push

# Import just to get the version
import pyperformance

VERSION = pyperformance.__version__

DESCRIPTION = 'Python benchmark suite'
CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Natural Language :: English',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python',
]


# put most of the code inside main() to be able to import setup.py in
# unit tests
def main():
    import io
    import os.path
    from setuptools import setup, find_packages

    with io.open('README.rst', encoding="utf8") as fp:
        long_description = fp.read().strip()

    options = {
        'name': 'pyperformance',
        'version': VERSION,
        'author': 'Collin Winter and Jeffrey Yasskin',
        'license': 'MIT license',
        'description': DESCRIPTION,
        'long_description': long_description,
        'url': 'https://github.com/python/benchmarks',
        'classifiers': CLASSIFIERS,
        'packages': find_packages(),
        'include_package_data': True,
        'entry_points': {
            'console_scripts': ['pyperformance=pyperformance.cli:main']
        },
        'install_requires': ["pyperf", "toml", "packaging"],
    }
    setup(**options)


if __name__ == '__main__':
    main()
