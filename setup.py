#!/usr/bin/env python
import os

from setuptools import find_packages, setup

setup(
    name='django-datatablesview',
    version='0.0.9',
    description='A Django app that integrates with DataTables.net javascript api.',
    author='dahlkar',
    url='http://github.com/dahlkar/django-datatables',
    packages=find_packages(exclude=['example', 'example.*']),
    install_requires=[
        "django>=2.1"
    ],
    include_package_data=True,
    zip_safe=True,
    license='MIT License',
    classifiers=[
        "Programming Language :: Python",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
    ]
)
