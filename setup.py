#!/usr/bin/env python
from setuptools import setup, find_packages
import django_online_migration

with open('requirements.txt') as r:
    requirements = r.read().strip().split('\n')

setup(
    name='django_online_migration',
    version=django_online_migration.__version__,
    description='Online MySQL schema migrations for Django',
    long_description='Perform MySQL table migrations while your Django application is live without locking the table',
    author='Dan McAulay',
    author_email='dan.mcaulay@socialcodeinc.com',
    url='http://www.socialcode.com',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Intended Audience :: System Administrators",
        "Operating System :: OS Independent",
        "Topic :: Software Development",
        "Programming Language :: Python :: 2.7",
    ],
    packages=find_packages(),
)
