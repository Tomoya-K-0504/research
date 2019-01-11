from setuptools import setup, find_packages

with open('jitai/README.md') as f:
    readme = f.read()

setup(
    name='jitai',
    version='0.0.1',
    description='python program for Just-in-time adaptive intervention',
    long_description=readme,
    author='Tomoya Koike',
    author_email='makeffort134@gmail.com',
    url='https://github.com/Tomoya-K-0504/research/tree/master/jitai',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)
