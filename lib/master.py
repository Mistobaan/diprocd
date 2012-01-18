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

"""Control loop.

Provides the loop object which is starting to poll for the configuration
changes and push them to the nodes clients.

"""


import logging
import simplejson
import zmq
import os

from time import time
from time import sleep

from diprocd.config import GetConfig

def Run(cfg, configfile):
    """Start the loop.

    The loop is very simple as it is basically just broadcasting
    configuration updates and doing poll for stats coming from the
    clients.
    """
    context = zmq.Context()

    stats_receiver = context.socket(zmq.PULL)
    stats_receiver.bind(cfg["master_stats"])
    logging.info("Collect stats on %s." % cfg["master_stats"])
    up_sender = context.socket(zmq.PUB)
    up_sender.bind(cfg["master_updates"])
    logging.info("Publish updates on %s." % cfg["master_updates"])
    poller = zmq.Poller()
    poller.register(stats_receiver, zmq.POLLIN)
    logging.info("Sleep 2 seconds to let clients connect.")
    sleep(2)
    refresh = FileRefresher(configfile)
    last_read = time()
    PublishChanges(cfg, up_sender)    
    while True:
        # We poll for max 1 sec.
        socks = dict(poller.poll(1000)) 

        if stats_receiver in socks and socks[stats_receiver] == zmq.POLLIN:
            # Log the stats
            stats = stats_receiver.recv()
            logging.info(stats)
        
        ctime = time()
        if ctime - last_read > 1.0:
            # Read the configuration and possibly push the updates
            new_cfg = refresh.refresh()
            if new_cfg is not None:
                PublishChanges(new_cfg, up_sender)
                cfg = new_cfg
                last_read = ctime

def PublishChanges(cfg, socket):
    """For each node we publish a message addressed to it."""
    for node, config in cfg["nodes"].items():
        logging.info("Publish to node %s %d processes." % (node, len(config)))
        socket.send("%s %s" % (node, simplejson.dumps(config)))
        
class FileRefresher:
    """Just load the new configuration. 

    It is not smart, it reloads the complete configuration.
    """
    def __init__(self, config_file):
        self.config_file = config_file
        self.last_update = time()
        
    def refresh(self):
        last_modif = int(os.path.getmtime(self.config_file))
        logging.info("Last modif time: %d, last update: %d." % (last_modif, self.last_update))
        if last_modif > self.last_update:
            logging.info("Refresh configuration from %s." % self.config_file)
            # We need to update the profiles
            self.last_update = time()
            return GetConfig(self.config_file)
        return None
        

