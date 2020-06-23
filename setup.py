# -*- coding: utf-8 -*-

# Learn more: https://confluence.securepassage.com/display/DEVNETSEC/FMAPI%3A+Python+Firemon+API+module

from setuptools import setup, find_packages
from distutils.util import convert_path

PROJECT = 'firemon-api'

with open('README.md') as f:
    readme = f.read()

main_ns = {}
with open(ver_path) as f:
    exec(f.read(), main_ns)

setup(
    name='firemon-api',
    version=main_ns['__version__'],
    description='NetSec Python Wrapper for Firemon API',
    long_description=readme,
    author='Firemon NetSec <dev-netsec@firemon.com>',
    author_email='dev-netsec@firemon.com',
    url='https://www.firemon.com/',
    project_urls = {
        'Repository': 'https://stash.securepassage.com/scm/nsu/firemon-api',
    },
    packages=find_packages(exclude=('tests', 'docs')),
    include_package_data=True,
    install_requires=[
        'requests',
    ],
    zip_safe=False,
)
