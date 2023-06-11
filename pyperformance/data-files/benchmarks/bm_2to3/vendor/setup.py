from setuptools import setup

setup(
    name='lib2to3',
    version='3.12',
    description='lib2to3 for Python 3.13+',
    packages=['lib2to3', 'lib2to3.fixes', 'lib2to3.pgen2'],
    package_data={'lib2to3': ['Grammar.txt', 'PatternGrammar.txt']}
)
