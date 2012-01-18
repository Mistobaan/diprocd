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

Provides the loop object which is starting to SUBscribe for the
configuration changes from the master and update the local
configuration. It PUSHes stats to the master too.
"""


import logging
import simplejson
import zmq
import os
import platform

from time import time
from diprocd.config import GetConfig, loadConf
from diprocd.utils import io as utils_io

def Run(cfg):
    """Start the loop.

    The loop is very simple as it is basically just subscribing
    for configuration changes.
    """
    context = zmq.Context()

    up_receiver = context.socket(zmq.SUB)
    up_receiver.connect(cfg["master_updates"])
    logging.info("Get updates from %s." % cfg["master_updates"])
    node_name = cfg["node_name"]
    if node_name == '%H':
        node_name = platform.node()
    up_receiver.setsockopt(zmq.SUBSCRIBE, cfg["node_name"])

    stats_sender = context.socket(zmq.PUSH)
    stats_sender.connect(cfg["master_stats"])
    logging.info("Push stats on %s." % cfg["master_stats"])    
    poller = zmq.Poller()
    poller.register(up_receiver, zmq.POLLIN)

    full_conf = GetConfig(cfg["conf_file"])

    last_read = time()
    while True:
        # We poll for max 1 sec.
        socks = dict(poller.poll(1000)) 

        if up_receiver in socks and socks[up_receiver] == zmq.POLLIN:
            # New configuration
            config = up_receiver.recv()
            logging.info(config)
            node_name, payload = config.split(" ", 1)
            new_processes = loadConf(payload)
            full_conf["procs"] = new_processes
            utils_io.WriteFile(cfg["conf_file"],
                               data=simplejson.dumps(full_conf))
