#
#

"""Module holding different constants."""

import re

# Format for CONFIG_VERSION:
#   01 03 0123 = 01030123
#   ^^ ^^ ^^^^
#   |  |  + Configuration version/revision
#   |  + Minor version
#   + Major version
#
# It stored as an integer. Make sure not to write an octal number.

# BuildVersion and SplitVersion must be in here because we can't import other
# modules. The cfgupgrade tool must be able to read and write version numbers
# and thus requires these functions. To avoid code duplication, they're kept in
# here.

def BuildVersion(major, minor, revision):
  """Calculates int version number from major, minor and revision numbers.

  Returns: int representing version number

  """
  assert isinstance(major, int)
  assert isinstance(minor, int)
  assert isinstance(revision, int)
  return (1000000 * major +
            10000 * minor +
                1 * revision)


def SplitVersion(version):
  """Splits version number stored in an int.

  Returns: tuple; (major, minor, revision)

  """
  assert isinstance(version, int)

  (major, remainder) = divmod(version, 1000000)
  (minor, revision) = divmod(remainder, 10000)

  return (major, minor, revision)

CONFIG_MAJOR = 1
CONFIG_MINOR = 1
CONFIG_REVISION = 0
CONFIG_VERSION = BuildVersion(CONFIG_MAJOR, CONFIG_MINOR, CONFIG_REVISION)

RUN_DIPROCD_DIR = "/"

# External script validation mask
EXT_PLUGIN_MASK = re.compile("^[a-zA-Z0-9_-]+$")
# one of 'no', 'yes', 'only'
SYSLOG_USAGE = "no"
SYSLOG_NO = "no"
SYSLOG_YES = "yes"
SYSLOG_ONLY = "only"
SYSLOG_SOCKET = "/dev/log"


DEV_CONSOLE = "/dev/console"

#: Give child process up to 5 seconds to exit after sending a signal
CHILD_LINGER_TIMEOUT = 5.0
# runparts results
(RUNPARTS_SKIP,
 RUNPARTS_RUN,
 RUNPARTS_ERR) = range(3)

RUNPARTS_STATUS = frozenset([RUNPARTS_SKIP, RUNPARTS_RUN, RUNPARTS_ERR])

