#
#

# Copyright (C) 2011 Ceondo Ltd.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

"""Module implementing configuration loading.

To stay simple, the configuration of o given controller on a node is
stored in a json file. The file is updated outside of the scope of the
controller but the controller can receive a SIGHUP signal to forcely
reload it or it checks every second the inode of the file to just
reload it.

The configuration format is very simple.

{pid_file: '/path/to/diprocd/pid.file',
    procs: [{name: 'myapplication.worker.1',
    	     run: '/full/path/to/command',
     	     pid_file: '/full/path/to/pid/file',
             args: ['list', 'of', 'args'],
             user: 'nobody', 
             chroot: '/path/to/chroot',
             restart: 1,
             depends: ['otherapp.handler', 'otherapp.worker.1'],
             env: {SMTP_SERVER: 'smtp.foo.tld',
                   SMTP_PASSWD: 'password',
                   ENV_KEY: 'value'},
        }]}

procs is a list of processes to manage.
"""

import simplejson
import logging
import sys

def GetConfig(config_file):
  try:
    datafile = open(config_file, "r")
  except IOError, msg:
      logging.fatal("Failed to open config file %s: %s." % (config_file, msg))
      sys.exit(2)

  cfg_content = datafile.read()
  datafile.close()

  return loadConf(cfg_content)


def loadConf(txt):
    """Load a json config and returns the content.

    """
    return simplejson.loads(txt)


proc = {'name': 'myapplication.worker.1', # unique name
        'run': '/full/path/to/command',
        'pid_file': '/full/path/to/pid/file', # outside of the chroot
        'args': ['list', 'of', 'args'],
        'user': 'nobody', # string or integer
        'chroot': '/path/to/chroot',
        'restart': True, # or False if not restarted when it dies
        'depends': ['otherapp.handler', 'otherapp.worker.1'],
        # Extra env variables given to the process
        'env': {'SMTP_SERVER': 'smtp.foo.tld',
                'SMTP_PASSWD': 'password',
                'ENV_KEY': 'value'},
        }

config = {'base': {},
          'procs': []}

