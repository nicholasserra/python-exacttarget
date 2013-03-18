#!/usr/bin/env python

from setuptools import setup

setup(
    name='python-exacttarget',
    version='0.0.3',
    install_requires=[],
    author='Nicholas Serra',
    author_email='nick@528hazelwood.com',
    license='MIT License',
    url='https://github.com/nicholasserra/python-exacttarget/',
    keywords='python exacttarget exact target xml api email mailinglist',
    description='A python class to interface with the ExactTarget XML API',
    long_description=open('README.md').read(),
    download_url="https://github.com/nicholasserra/python-exacttarget/zipball/master",
    py_modules=["exacttarget"],
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet'
    ]
)
