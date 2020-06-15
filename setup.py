from setuptools import setup, find_packages
from codecs import open
from os import path
from version import get_git_version

here = path.abspath(path.dirname(__file__))

setup(
    name='adeploy',
    version=get_git_version(),
    description='An universal deployment tool for k8s deployments',
    author='awesome IT',
    author_email='daniel.morlock@awesome-it.de',
    packages=find_packages(),
    install_requires=open('%s/requirements.txt' % here, 'r',).readlines(),
    entry_points={
        'console_scripts': [
            'adeploy=lib.main:main',
        ],
    })