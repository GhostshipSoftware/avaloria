"""
Scripts are entities that perform some sort of action, either only
once or repeatedly. They can be directly linked to a particular
Evennia Object or be stand-alonw (in the latter case it is considered
a 'global' script). Scripts can indicate both actions related to the
game world as well as pure behind-the-scenes events and
effects. Everything that has a time component in the game (i.e. is not
hard-coded at startup or directly created/controlled by players) is
handled by Scripts.

Scripts have to check for themselves that they should be applied at a
particular moment of time; this is handled by the is_valid() hook.
Scripts can also implement at_start and at_end hooks for preparing and
cleaning whatever effect they have had on the game object.

Common examples of uses of Scripts:
- load the default cmdset to the player object's cmdhandler
  when logging in.
- switch to a different state, such as entering a text editor,
  start combat or enter a dark room.
- Weather patterns in-game
- merge a new cmdset with the default one for changing which
  commands are available at a particular time
- give the player/object a time-limited bonus/effect

"""
from django.conf import settings
from django.db import models

from src.typeclasses.models import (TypedObject, TagHandler,
                                    AttributeHandler)
from src.scripts.manager import ScriptManager

__all__ = ("ScriptDB",)
_SA = object.__setattr__


#------------------------------------------------------------
#
# ScriptDB
#
#------------------------------------------------------------

class ScriptDB(TypedObject):
    """
    The Script database representation.

    The TypedObject supplies the following (inherited) properties:
      key - main name
      name - alias for key
      typeclass_path - the path to the decorating typeclass
      typeclass - auto-linked typeclass
      date_created - time stamp of object creation
      permissions - perm strings
      dbref - #id of object
      db - persistent attribute storage
      ndb - non-persistent attribute storage

    The ScriptDB adds the following properties:
      desc - optional description of script
      obj - the object the script is linked to, if any
      interval - how often script should run
      start_delay - if the script should start repeating right away
      repeats - how many times the script should repeat
      persistent - if script should survive a server reboot
      is_active - bool if script is currently running

    """


    #
    # ScriptDB Database Model setup
    #
    # These databse fields are all set using their corresponding properties,
    # named same as the field, but withtou the db_* prefix.

    # inherited fields (from TypedObject):
    # db_key, db_typeclass_path, db_date_created, db_permissions

    # optional description.
    db_desc = models.CharField('desc', max_length=255, blank=True)
    # A reference to the database object affected by this Script, if any.
    db_obj = models.ForeignKey("objects.ObjectDB", null=True, blank=True, verbose_name='scripted object',
                               help_text='the object to store this script on, if not a global script.')
    # how often to run Script (secs). -1 means there is no timer
    db_interval = models.IntegerField('interval', default=-1, help_text='how often to repeat script, in seconds. -1 means off.')
    # start script right away or wait interval seconds first
    db_start_delay = models.BooleanField('start delay', default=False, help_text='pause interval seconds before starting.')
    # how many times this script is to be repeated, if interval!=0.
    db_repeats = models.IntegerField('number of repeats', default=0, help_text='0 means off.')
    # defines if this script should survive a reboot or not
    db_persistent = models.BooleanField('survive server reboot', default=False)
    # defines if this script has already been started in this session
    db_is_active = models.BooleanField('script active', default=False)

    # Database manager
    objects = ScriptManager()

    # caches for quick lookups
    _typeclass_paths = settings.SCRIPT_TYPECLASS_PATHS
    _default_typeclass_path = settings.BASE_SCRIPT_TYPECLASS or "src.scripts.scripts.DoNothing"

    class Meta:
        "Define Django meta options"
        verbose_name = "Script"

    def __init__(self, *args, **kwargs):
        super(ScriptDB, self).__init__(*args, **kwargs)
        _SA(self, "attributes", AttributeHandler(self))
        _SA(self, "tags", TagHandler(self))
        #_SA(self, "aliases", AliasHandler(self))

    #
    #
    # ScriptDB class properties
    #
    #


    def at_typeclass_error(self):
        """
        If this is called, it means the typeclass has a critical
        error and cannot even be loaded. We don't allow a script
        to be created under those circumstances. Already created,
        permanent scripts are set to already be active so they
        won't get activated now (next reboot the bug might be fixed)
        """
        # By setting is_active=True, we trick the script not to run "again".
        self.is_active = True
        return super(ScriptDB, self).at_typeclass_error()

    delete_iter = 0
    def delete(self):
        if self.delete_iter > 0:
            return
        self.delete_iter += 1
        super(ScriptDB, self).delete()
