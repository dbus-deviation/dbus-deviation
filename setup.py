#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from setuptools import setup, find_packages

setup(
    name='dbus-deviation',
    version='0.1.0',
    packages=find_packages(exclude=['*.tests']),
    include_package_data=True,
    exclude_package_data={'': ['.gitignore']},
    zip_safe=True,
    setup_requires=[
        'setuptools_git >= 0.3',
    ],
    install_requires=[],
    tests_require=[],
    entry_points={
        'console_scripts': [
            'dbus-interface-diff = dbusdeviation.utilities.diff:main',
        ],
    },
    author='Philip Withnall',
    author_email='philip.withnall@collabora.co.uk',
    description='Parse D-Bus introspection XML and process it in various ways',
    long_description='dbus-deviation is a project for parsing D-Bus '
                     'introspection XML and processing it in various ways. '
                     'Its main tool is dbus-interface-diff, which calculates '
                     'the difference between two D-Bus APIs for the purpose '
                     'of checking for API breaks. This functionality is also '
                     'available as a Python module, dbusdeviation.',
    license='GPLv2+',
    url='http://people.collabora.com/~pwith/dbus-deviation/',
    test_suite='dbusdeviation.tests'
)
