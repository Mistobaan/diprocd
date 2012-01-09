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

Provides the loop object which is starting to poll the processes from
the configuration. It can optionally open zeromq sockets to update the
configuration and push stats dynamically.
"""

import os
import logging
from time import sleep, time
from pwd import getpwnam  
import random

from diprocd.config import GetConfig
from diprocd.utils import io as utils_io
from diprocd.utils import process as utils_process
from diprocd.errors import LockError, ConfigurationError


# Maximal number of starts within a minute before giving up.
MAX_STARTS = 5
STATE_waiting = "waiting"
STATE_running = "running"
STATE_ADMIN_down = "ADMIN_down"
STATE_ADMIN_notrestarted = "ADMIN_notrestarted"
STATE_ADMIN_needrestart = "ADMIN_needrestart"
STATE_ERROR_down = "ERROR_down"
STATE_ERROR_up = "ERROR_up"
STATE_ERROR_wrongnode = "ERROR_wrongnode"
STATE_ERROR_nodedown = "ERROR_nodedown"
STATE_ERROR_nodeoffline = "ERROR_nodeoffline"

STATE_TO_STOP = (STATE_ERROR_up, STATE_ADMIN_needrestart)
STATE_TO_START = (STATE_waiting, STATE_ERROR_down, STATE_ADMIN_needrestart)


class Profile:
    """Wrapper to start/stop/keep stats about a profile.

    A profile is a process. The terminology is coming from procer.
    """
    def __init__(self, cfg):
        # We explicitely set the properties to be sure
        # we have the required ones.
        self.Configure(cfg)
        self.pid = None
        self.nb_starts = 0
        self.last_start = 0
        self.max_start = MAX_STARTS
        self.state = STATE_waiting

    def Configure(self, cfg):
        self.name = cfg["name"]
        self.run = cfg["run"]
        self.pid_file = cfg["pid_file"]

        self.args = cfg.get("args", [])
        self.cwd = cfg.get("cwd", "/")        
        self.user = cfg.get("user", "nobody")
        
        self.chroot = cfg.get("chroot", None)
        self.logs = cfg.get("logs", None)
        self.restart = cfg.get("restart", True)
        self.depends = cfg.get("depends", [])
        self.env = cfg.get("env", {})
        self.daemon = cfg.get("daemon", False)
        self.write_pid = cfg.get("write_pid", True)
        self.uid = None
        self.gid = None
        self.nb_starts = 0
        self.starts = [] # All the starts
        
        if self.user:
            try:
                self.uid, self.gid = getpwnam(self.user)[2:4]
            except KeyError:
                raise ConfigurationError("User %s not found for profile %s" %
                                         (self.user, self.name))
        


    def Initialize(self):
        """Update stats based on the possibly running process.

        """
        logging.info("Init profile %s" % self.name)
        try:
            pid = utils_io.ReadPidFile(self.pid_file)
        except Exception:
            pid = 0
        if pid > 0 and utils_process.IsProcessAlive(pid):
            # We have a running process
            logging.info("%s already running with pid: %d." % (self.name, pid))
            self.pid = pid
            self.state = STATE_running
            self.nb_starts = 0
            self.last_start = int(os.path.getctime("/proc/%d" % self.pid))

    def Supervise(self):
        """Run the profile if not already running.

        """
        logging.debug("Supervise %s." % self.name)
        self.CheckPid()
        if self.state in STATE_TO_STOP:
            self.Stop()
        if self.state in STATE_TO_START:
            self.Start()

    def CheckPid(self):
        """Check if the pid in the pid file is running.

        """
        if self.state != STATE_running:
            return
        if False is utils_process.IsProcessAlive(self.pid):
            # Check if restarted outside and wrote a new pid in the
            # pid file.
            try:
                logging.debug("Try loading from pid file: %s." % self.pid_file)
                pid = utils_io.ReadPidFile(self.pid_file)
                if pid != self.pid and utils_process.IsProcessAlive(pid):
                    self.pid = pid
                    return
            except:
                pass
            if self.restart:
                self.state = STATE_ERROR_down
            else:
                self.state = STATE_ADMIN_down

    def Start(self):
        """Start the profile.

        Some information about the PID file.
        - you create a pid file, we rely on your pid in your file.
        - you do not create a pid file, we do it for you.
        - you fork, you must create your own pid.
        """
        if self.nb_starts >= self.max_start:
            # check that the start max_start ago was for less than 60 ago
            cut_off = self.starts[-self.max_start]
            if cut_off > time() - 60:
                self.state = STATE_ADMIN_notrestarted
                logging.info("%s not restarted (max start reached in 60s)." % self.name)
                return
        my_cmd = [self.run] + self.args
        logging.info("Start profile %s." % self.name)
        logging.debug("Pid in %s for %s." % (self.pid_file, self.name))
        if self.write_pid is True:
            pid_file = self.pid_file
        else:
            # In this case, diprocd will not write the pid file and let
            # the daemon do it.
            logging.debug("Pid written by the application %s." % self.name)
            pid_file = None
        logging.debug("Pid for StartDaemon is %s." % pid_file)
        logging.debug("Env for %s is %s." % (self.name, self.env))
        self.pid = utils_process.StartDaemon(my_cmd, self.env, self.cwd,
                                             pidfile=pid_file, output=self.logs,
                                             uid=self.uid, gid=self.gid)
        if self.daemon:
            logging.debug("Application %s is a daemon." % self.name)
            # Here the launched command will again fork and write to
            # the pid file, so we need to reread the pid
            self.pid = utils_io.ReadPidFile(self.pid_file)
        logging.debug("Pid for %s is %s." % (self.name, self.pid))
        self.state = STATE_running
        self.nb_starts += 1
        self.starts.append(time())

    def Stop(self):
        """Stop the profile.

        """
        logging.info("Stop profile %s." % self.name)        
        utils_process.KillProcess(self.pid, timeout=1)
        if self.state != STATE_ADMIN_needrestart:
            self.state = STATE_ADMIN_down
        if utils_process.IsProcessAlive(self.pid):
            logging.warn("Error profile not stopped %s." % self.name)
            self.state = STATE_ERROR_up
            

def Run(cfg, _refresh_cb=None):
    """Start the loop.

    Should stop on SIGTERM.
    """
    profiles = []
    for profcfg in cfg["procs"]:
        profile = Profile(profcfg)
        profile.Initialize()
        profiles.append(profile)
    # We have the profiles, now, we are going to test them
    while True:
        profiles = Supervise(profiles)
        sleep(1.0 + random.uniform(-0.1, 0.1))
        if _refresh_cb is not None:
            profiles, cfg = _refresh_cb(profiles, cfg)

def Supervise(profiles):
    for profile in profiles:
        profile.Supervise()
        if profile.state == STATE_ADMIN_down:
            profiles.remove(profile)
    return profiles



class FileRefresher:
    """Refresh the profiles on configuration file change.

    Mark profiles to stop, the ones to reload and add the new ones.
    """
    def __init__(self, config_file):
        self.config_file = config_file
        self.last_update = time()
        
    def refresh(self, profiles, old_config):
        last_modif = int(os.path.getmtime(self.config_file))
        if last_modif > self.last_update:
            logging.info("Refresh profiles from %s." % self.config_file)
            # We need to update the profiles
            return self.diffProfiles(profiles, old_config,
                                     GetConfig(self.config_file))
        return profiles, old_config

    def diffProfiles(self, profiles, old_cfg, new_cfg):
        # Index by name
        self.last_update = time()        
        old_pcfg = {}
        new_pcfg = {}
        for pcfg in new_cfg["procs"]:
            new_pcfg[pcfg["name"]] = pcfg
        for pcfg in old_cfg["procs"]:
            old_pcfg[pcfg["name"]] = pcfg
        # Find the ones to stop
        to_stop = [x for x in old_pcfg.keys() if x not in new_pcfg.keys()]
        # Find the ones to start
        to_start = [x for x in new_pcfg.keys() if x not in old_pcfg.keys()]
        # Find the ones to reload
        to_reload = []
        for name, cfg in old_pcfg.items():
            if name not in to_stop and name not in to_start:
                if new_pcfg[name] != cfg:
                    to_reload.append(name)
        # Now, we go through the profiles list and update accordingly,
        # we add the new profiles, mark the stopped as error up and
        # the changed as to be reloaded.
        new_profiles = []
        for profile in profiles:
            if profile.name in to_stop:
                logging.debug("To stop %s." % profile.name)
                profile.state = STATE_ERROR_up
                new_profiles.append(profile)
            elif profile.name in to_reload:
                logging.debug("To reload %s." % profile.name)                
                profile.state = STATE_ADMIN_needrestart
                profile.Configure(new_pcfg[profile.name])
                new_profiles.append(profile)
            else:
                # Not changed
                logging.debug("To keep %s." % profile.name)                
                new_profiles.append(profile)                
        for newp in to_start:
            logging.debug("To start %s." % newp)
            profile = Profile(new_pcfg[newp])
            profile.Initialize()
            profiles.append(profile)

        return profiles, new_cfg

    



        
