#!/usr/bin/env python3

# Prepare a release:
#
#  - git pull --rebase
#  - update version in setup.py
#  - set release date in changelog
#  - run tests:
#    python2 runtests.py
#    python3 runtests.py
#    pypy runtests.py
#  - git commit -a -m "prepare release x.y"
#  - git push
#
# Release a new version:
#
#  - git tag VERSION
#  - git push --tags
#  - python3 setup.py register sdist bdist_wheel upload
#    (need wheel: sudo python3 -m pip install -U setuptools wheel)
#
# After the release:
#
#  - set version to n+1
#  - git commit -a -m "post-release"
#  - git push

VERSION = '0.0'

DESCRIPTION = 'Python benchmark suite'
CLASSIFIERS = [
    'Development Status :: 4 - Beta',
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
    from setuptools import setup

    with open('README.rst') as fp:
        long_description = fp.read().strip()

    packages = [
        'performance',
        'performance.benchmarks',
        'performance.benchmarks.data',
        'performance.benchmarks.data.2to3',
        'performance.benchmarks.pybench',
        'performance.benchmarks.pybench.package',
    ]
    data_files = [
        'spambayes_hammie.pkl',
        'spambayes_mailbox',
        'telco-bench.b',
        'w3_tr_html5.html',
    ]
    data = {
        'performance.benchmarks.data': data_files,
        'performance.benchmarks.data.2to3': ['README'],
        'performance.benchmarks.pybench': ['LICENSE', 'README'],
    }

    options = {
        'name': 'performance',
        'version': VERSION,
        'license': 'MIT license',
        'description': DESCRIPTION,
        'long_description': long_description,
        'url': 'https://github.com/python/benchmarks',
        'classifiers': CLASSIFIERS,
        'packages': packages,
        'package_data': data,
        'entry_points': {
            'console_scripts': ['bench.py=performance.cli:main']
        }
        # Note: the performance package has no direct external dependencies:
        # it installs dependencies itself by creating virtual environments
    }
    setup(**options)

if __name__ == '__main__':
    main()
