# -*- coding: utf-8 -*-

# Learn more: https://confluence.securepassage.com/display/DEVNETSEC/FMAPI%3A+Python+Firemon+API+module

from setuptools import setup, find_packages
from distutils.util import convert_path

PROJECT = "firemon-api"

with open("README.md") as f:
    readme = f.read()

main_ns = {}
ver_path = convert_path("firemon_api/version.py")
with open(ver_path) as f:
    exec(f.read(), main_ns)

setup(
    name=PROJECT,
    version=main_ns["__version__"],
    description="NetSec Python Wrapper for Firemon API",
    long_description=readme,
    author="Firemon NetSec <dev-netsec@firemon.com>",
    author_email="dev-netsec@firemon.com",
    url="https://www.firemon.com/",
    project_urls={
        "Repository": "https://stash.securepassage.com/scm/nsu/firemon-api",
        "Documentation": "https://confluence.securepassage.com/display/DEVNETSEC/FMAPI%3A+Python+Firemon+API+module",
    },
    packages=find_packages(exclude=("tests", "docs")),
    include_package_data=True,
    python_requires=">=3.6",
    install_requires=[
        "requests",
    ],
    zip_safe=False,
)
