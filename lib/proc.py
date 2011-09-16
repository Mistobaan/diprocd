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

"""Module implementing process control.

"""

from diprocd import utils
from diprocd.utils import retry as utils_retry
from time import sleep

class Checker:
    """Given a process definition, check if running accordingly.

    """

    def simple(self):
        """List the running processes.

        """
        my_cmd = ["/bin/ps", "axww"]
        env = {"FOO": "BAR"}
        result = utils.RunCmd(my_cmd, env=env)
        return result

    def forked(self):
        """List the running processes.

        """
        my_cmd = ["/usr/bin/php", "testpackage.phar", "serve", "--daemonize"]
        env = {"FOO": "BAR"}
        result = utils.RunCmd(my_cmd, env=env, cwd="/home/loa/Projects/baregit/app")
        return result

    def Daemon(self):
        my_cmd = ["/usr/bin/php", "testpackage.phar", "serve"]
        env = {"FOO": "BAR"}
        pid = utils.StartDaemon(my_cmd, env=env, cwd="/home/loa/Projects/baregit/app", pidfile="/home/loa/Projects/baregit/app/test.pid")
        return pid

    def DaemonLs(self):
        my_cmd = ["/bin/ls", "-lh"]
        env = {"FOO": "BAR"}
        cwd="/"
        pidfile="/home/loa/Projects/baregit/app/ls.pid"
        timeout = 10.0
        pid = None
        try:
            pid = utils_retry.Retry(_LaunchRetried, (1.0, 1.2, 5.0), max(0, timeout),
                                    args=[my_cmd, env, cwd, pidfile])
        except utils_retry.RetryTimeout:
            print "Error, timed out\n"
        return pid

    def DaemonFailed(self):
        my_cmd = ["/home/loa/Projects/diprocd/test.sh", "-lh"]
        env = {"FOO": "BAR"}
        cwd="/"
        pidfile="/home/loa/Projects/diprocd/test.sh.pid"
        timeout = 10.0
        pid = None
        try:
            pid = utils_retry.Retry(_LaunchRetried, (1.0, 1.2, 5.0), max(0, timeout),
                                    args=[my_cmd, env, cwd, pidfile])
        except utils_retry.RetryTimeout:
            print "Error, timed out\n"
        return pid

    def DaemonFailed2(self, my_cmd):
        env = {"FOO": "BAR"}
        cwd="/"
        pidfile="/home/loa/Projects/diprocd/test.sh.pid"
        timeout = 10.0
        pid = None
        try:
            pid = utils_retry.Retry(_LaunchRetried, (1.0, 1.2, 5.0), max(0, timeout),
                                    args=[my_cmd, env, cwd, pidfile])
        except utils_retry.RetryTimeout:
            print "Error, timed out\n"
        return pid

    def RobustDaemon(self, my_cmd):
        pid = self.DaemonFailed2(my_cmd)

def _LaunchRetried(my_cmd, env, cwd, pidfile):
    """Raises L{utils_retry.RetryAgain} if child is still alive.
    
    @raises utils_retry.RetryAgain: If child is still alive
    
    """
    pid = utils.StartDaemon(my_cmd, env, cwd, pidfile)
    sleep(0.05) # Wait 50ms to possibly catch a daemon going out immediately
    if utils.IsProcessAlive(pid) is False:
        raise utils_retry.RetryAgain()
    return pid

def launchTest(my_cmd):
    pidfile = "/home/loa/Projects/diprocd/test.sh.pid"
    cwd = "/home/loa/Projects/baregit/app"
    return utils.StartDaemon(my_cmd, {}, cwd, pidfile)


