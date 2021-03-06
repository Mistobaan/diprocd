#!/usr/bin/env python

from distutils.core import setup

setup(name='diprocd',
      version='1.0',
      description='Distributed Process Control Daemon',
      author='Loic d\'Anterroches',
      author_email='open@danterroches.org',
      url='http://projects.ceondo.com/p/diprocd/',
      packages=['diprocd', 'diprocd.utils'],
      package_dir = {'diprocd': 'lib'},
      scripts=['tools/dpd-clientd', 'tools/dpd-masterd', 'tools/dpd-workerd'],
      data_files=[('/etc/default', ['init.d/diprocd']),
                  ('/etc/init.d', ['init.d/dpd-clientd', 'init.d/dpd-workerd', 'init.d/dpd-masterd']),
                  ('/usr/share/doc/diprocd', ['examples/diprocd-worker.example.json',
                                              'examples/diprocd-client.example.json',
                                              'examples/diprocd-master.example.json',
                                              'examples/diprocd-emptyworker.example.json',
                                              'init.d/dpd-clientd.cron', 
                                              'init.d/dpd-workerd.cron', 
                                              'init.d/dpd-masterd.cron'])

                  ]
     )
