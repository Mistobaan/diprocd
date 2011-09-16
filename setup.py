#!/usr/bin/env python

from distutils.core import setup

setup(name='diprocd',
      version='1.0',
      description='Distributed Process Control Daemon',
      author='Loic d\'Anterroches',
      author_email='open@danterroches.org',
      url='http://www.ceondo.com/',
      packages=['diprocd', 'diprocd.utils'],
      package_dir = {'diprocd': 'lib'},
      scripts=['tools/dpd-clientd', 'tools/dpd-masterd', 'tools/dpd-workerd']
     )
