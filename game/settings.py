
######################################################################
# Evennia MU* server configuration file
#
# You may customize your setup by copy&pasting the variables you want
# to change from the master config file src/settings_default.py to
# this file. Try to *only* copy over things you really need to customize
# and do *not* make any changes to src/settings_default.py directly.
# This way you'll always have a sane default to fall back on
# (also, the master config file may change with server updates).
#
######################################################################

from src.settings_default import *

######################################################################
# Custom settings
######################################################################

BASE_CHARACTER_TYPECLASS = "game.gamesrc.objects.world.character.Hero"
LOCK_FUNC_MODULES = ("src.locks.lockfuncs", "game.gamesrc.overrides.lockfuncs")
CMDSET_UNLOGGEDIN = "game.gamesrc.menu_login"

######################################################################
# SECRET_KEY was randomly seeded when settings.py was first created.
# Don't share this with anybody. It is used by Evennia to handle
# cryptographic hashing for things like cookies on the web side.
######################################################################
SECRET_KEY = 'M~ot@$&*u[legiBsk,V6a)j.U#}L<AX"ch94Y0pT'

