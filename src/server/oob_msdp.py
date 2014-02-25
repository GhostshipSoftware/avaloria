"""
Out-of-band default plugin commands available for OOB handler. This
follows the standards defined by the MSDP out-of-band protocol
(http://tintin.sourceforge.net/msdp/)

This module is pointed to by settings.OOB_PLUGIN_MODULES. All functions
(not classes) defined globally in this module will be made available
to the oob mechanism.

    function execution - the oob protocol can execute a function directly on
                         the server. The available functions must be defined
                         as global functions via settings.OOB_PLUGIN_MODULES.
    repeat func execution - the oob protocol can request a given function be
                            executed repeatedly at a regular interval. This
                            uses an internal script pool.
    tracking - the oob protocol can request Evennia to track changes to
               fields on objects, as well as changes in Attributes. This is
               done by dynamically adding tracker-objects on entities. The
               behaviour of those objects can be customized via
               settings.OOB_PLUGIN_MODULES.

What goes into the OOB_PLUGIN_MODULES is a list of modules with input
for the OOB system.

oob functions have the following call signature:
    function(caller, session, *args, **kwargs)

oob trackers should build upon the OOBTracker class in this module
    module and implement a minimum of the same functionality.

a global function oob_error will be used as optional error management.
"""
from django.conf import settings
from src.utils.utils import to_str
_GA = object.__getattribute__
_SA = object.__setattr__
_NA = lambda o: (None, "N/A")  # not implemented

# default properties defined by the MSDP protocol. These are
# used by the SEND oob function below. Each entry should point
# to a function that takes the relevant object as input and
# returns the data it is responsible for. Most of these
# are commented out, but kept for reference for each
# game to implement.

OOB_SENDABLE = {
   ## General
    "CHARACTER_NAME": lambda o: ("db_key", o.key),
    "SERVER_ID": lambda o: ("settings.SERVERNAME", settings.SERVERNAME),
    #"SERVER_TIME": _NA,
   ## Character
    #"AFFECTS": _NA,
    #"ALIGNMENT": _NA,
    #"EXPERIENCE": _NA,
    #"EXPERIENCE_MAX": _NA,
    #"EXPERIENCE_TNL": _NA,
    #"HEALTH": _NA,
    #"HEALTH_MAX": _NA,
    #"LEVEL": _NA,
    #"RACE": _NA,
    #"CLASS": _NA,
    #"MANA": _NA,
    #"MANA_MAX": _NA,
    #"WIMPY": _NA,
    #"PRACTICE": _NA,
    #"MONEY": _NA,
    #"MOVEMENT": _NA,
    #"MOVEMENT_MAX": _NA,
    #"HITROLL": _NA,
    #"DAMROLL": _NA,
    #"AC": _NA,
    #"STR": _NA,
    #"INT": _NA,
    #"WIS": _NA,
    #"DEX": _NA,
    #"CON": _NA,
   ## Combat
    #"OPPONENT_HEALTH": _NA,
    #"OPPONENT_HEALTH_MAX": _NA,
    #"OPPONENT_LEVEL": _NA,
    #"OPPONENT_NAME": _NA,
   ## World
    #"AREA_NAME": _NA,
    #"ROOM_EXITS": _NA,
    #"ROOM_VNUM": _NA,
    "ROOM_NAME": lambda o: ("db_location", o.db_location.key),
    #"WORLD_TIME": _NA,
   ## Configurable variables
    #"CLIENT_ID": _NA,
    #"CLIENT_VERSION": _NA,
    #"PLUGIN_ID": _NA,
    #"ANSI_COLORS": _NA,
    #"XTERM_256_COLORS": _NA,
    #"UTF_8": _NA,
    #"SOUND": _NA,
    #"MXP": _NA,
   ## GUI variables
    #"BUTTON_1": _NA,
    #"BUTTON_2": _NA,
    #"BUTTON_3": _NA,
    #"BUTTON_4": _NA,
    #"BUTTON_5": _NA,
    #"GAUGE_1": _NA,
    #"GAUGE_2": _NA,
    #"GAUGE_3": _NA,
    #"GAUGE_4": _NA,
    #"GAUGE_5": _NA
    }
# mapping for which properties may be tracked
OOB_REPORTABLE = OOB_SENDABLE


#------------------------------------------------------------
# Tracker classes
#
# Trackers are added to a given object's trackerhandler and
# reports back changes when they happen. They are managed using
# the oobhandler's track/untrack mechanism
#------------------------------------------------------------

class TrackerBase(object):
    """
    Base class for OOB Tracker objects.
    """
    def __init__(self, oobhandler, *args, **kwargs):
        self.oobhandler = oobhandler

    def update(self, *args, **kwargs):
        "Called by tracked objects"
        pass

    def at_remove(self, *args, **kwargs):
        "Called when tracker is removed"
        pass


class OOBFieldTracker(TrackerBase):
    """
    Tracker that passively sends data to a stored sessid whenever
    a named database field changes. The TrackerHandler calls this with
    the correct arguments.
    """
    def __init__(self, oobhandler, fieldname, sessid, *args, **kwargs):
        """
        name - name of entity to track, such as "db_key"
        sessid - sessid of session to report to
        """
        self.oobhandler = oobhandler
        self.fieldname = fieldname
        self.sessid = sessid

    def update(self, new_value, *args, **kwargs):
        "Called by cache when updating the tracked entitiy"
        # use oobhandler to relay data
        try:
            # we must never relay objects across the amp, only text data.
            new_value = new_value.key
        except AttributeError:
            new_value = to_str(new_value, force_string=True)
        # this is a wrapper call for sending oob data back to session
        self.oobhandler.msg(self.sessid, "report", self.fieldname,
                                                    new_value, *args, **kwargs)


class OOBAttributeTracker(TrackerBase):
    """
    Tracker that passively sends data to a stored sessid whenever
    the Attribute updates. Since the field here is always "db_key",
    we instead store the name of the attribute to return.
    """
    def __init__(self, oobhandler, fieldname, sessid, attrname, *args, **kwargs):
        """
        attrname - name of attribute to track
        sessid - sessid of session to report to
        """
        self.oobhandler = oobhandler
        self.attrname = attrname
        self.sessid = sessid

    def update(self, new_value, *args, **kwargs):
        "Called by cache when attribute's db_value field updates"
        try:
            new_value = new_value.dbobj
        except AttributeError:
            new_value = to_str(new_value, force_string=True)
        # this is a wrapper call for sending oob data back to session
        self.oobhandler.msg(self.sessid, "report", self.attrname, new_value, *args, **kwargs)


#------------------------------------------------------------
# OOB commands
# This defines which internal server commands the OOB handler
# makes available to the client. These commands are called
# automatically by the OOB mechanism by triggering the
# oobhandlers's execute_cmd method with the cmdname and
# eventual args/kwargs. All functions defined globally in this
# module will be made available to call by the oobhandler. Use
# _funcname if you want to exclude one. To allow for python-names
# like "list" here, these properties are read as being case-insensitive.
#
# All OOB commands must be on the form
#      cmdname(oobhandler, session, *args, **kwargs)
#------------------------------------------------------------

def oob_error(oobhandler, session, errmsg, *args, **kwargs):
    """
    This is a special function called by the oobhandler when an error
    occurs already at the execution stage (such as the oob function
    not being recognized or having the wrong args etc).
    """
    session.msg(oob=("send", {"ERROR": errmsg}))


def list(oobhandler, session, mode, *args, **kwargs):
    """
    List available properties. Mode is the type of information
    desired:
        "COMMANDS"               Request an array of commands supported
                                 by the server.
        "LISTS"                  Request an array of lists supported
                                 by the server.
        "CONFIGURABLE_VARIABLES" Request an array of variables the client
                                 can configure.
        "REPORTABLE_VARIABLES"   Request an array of variables the server
                                 will report.
        "REPORTED_VARIABLES"     Request an array of variables currently
                                 being reported.
        "SENDABLE_VARIABLES"     Request an array of variables the server
                                 will send.
    """
    mode = mode.upper()
    # the first return argument is treated by the msdp protocol as the
    # name of the msdp array to return
    if mode == "COMMANDS":
        session.msg(oob=("list", ("COMMANDS",
                                  "LIST",
                                  "REPORT",
                                  "UNREPORT",
                                  # "RESET",
                                  "SEND")))
    elif mode == "LISTS":
        session.msg(oob=("list", ("LISTS",
                                  "REPORTABLE_VARIABLES",
                                  "REPORTED_VARIABLES",
                                  # "CONFIGURABLE_VARIABLES",
                                  "SENDABLE_VARIABLES")))
    elif mode == "REPORTABLE_VARIABLES":
        session.msg(oob=("list", ("REPORTABLE_VARIABLES",) +
                                  tuple(key for key in OOB_REPORTABLE.keys())))
    elif mode == "REPORTED_VARIABLES":
        session.msg(oob=("list", ("REPORTED_VARIABLES",) +
                                    tuple(oobhandler.get_all_tracked(session))))
    elif mode == "SENDABLE_VARIABLES":
        session.msg(oob=("list", ("SENDABLE_VARIABLES",) +
                                  tuple(key for key in OOB_REPORTABLE.keys())))
    #elif mode == "CONFIGURABLE_VARIABLES":
    #    pass
    else:
        session.msg(oob=("list", ("unsupported mode",)))


def send(oobhandler, session, *args, **kwargs):
    """
    This function directly returns the value of the given variable to the
    session. vartype can be one of
    """
    obj = session.get_puppet_or_player()
    ret = {}
    if obj:
        for name in (a.upper() for a in args if a):
            try:
                key, value = OOB_SENDABLE.get(name, _NA)(obj)
                ret[name] = value
            except Exception, e:
                ret[name] = str(e)
    # return result
    session.msg(oob=("send", ret))


def report(oobhandler, session, *args, **kwargs):
    """
    This creates a tracker instance to track the data given in *args.
    vartype is one of "prop" (database fields) or "attr" (attributes)
    """
    obj = session.get_puppet_or_player()
    if obj:
        for name in (a.upper() for a in args if a):
            key, val = OOB_REPORTABLE.get(name, _NA)(obj)
            if key:
                if key.startswith("db_"):
                    oobhandler.track_field(obj, session.sessid,
                                           key, OOBFieldTracker)
                else:  # assume attribute
                    oobhandler.track_attribute(obj, session.sessid,
                                               key, OOBAttributeTracker)


def unreport(oobhandler, session, vartype="prop", *args, **kwargs):
    """
    This removes tracking for the given data given in *args.
    vartype is one of of "prop" or "attr".
    """
    obj = session.get_puppet_or_player()
    if obj:
        for name in (a.upper() for a in args if a):
            key, val = OOB_REPORTABLE.get(name, _NA)
            if key:
                if key.startswith("db_"):
                    oobhandler.untrack_field(obj, session.sessid, key)
                else:  # assume attribute
                    oobhandler.untrack_attribute(obj, session.sessid, key)

