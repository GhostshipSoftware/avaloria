"""
A cmdset holds a set of commands available to the object or to other
objects near it. All the commands a player can give (look, @create etc)
are stored as the default cmdset on the player object and managed using the
CmdHandler object (see cmdhandler.py).

The power of having command sets in CmdSets like this is that CmdSets
can be merged together according to individual rules to create a new
on-the-fly CmdSet that is some combination of the
previous ones. Their function are borrowed to a large parts from mathematical
Set theory, it should not be much of a problem to understand.

See CmdHandler for practical examples on how to apply cmdsets
together to create interesting in-game effects.
"""

from weakref import WeakKeyDictionary
from django.utils.translation import ugettext as _
from src.utils.utils import inherits_from, is_iter
__all__ = ("CmdSet",)


class _CmdSetMeta(type):
    """
    This metaclass makes some minor on-the-fly convenience fixes to
    the cmdset class.
    """
    def __init__(mcs, *args, **kwargs):
        """
        Fixes some things in the cmdclass
        """
        # by default we key the cmdset the same as the
        # name of its class.
        if not hasattr(mcs, 'key') or not mcs.key:
            mcs.key = mcs.__name__
        mcs.path = "%s.%s" % (mcs.__module__, mcs.__name__)

        if not type(mcs.key_mergetypes) == dict:
            mcs.key_mergetypes = {}

        super(_CmdSetMeta, mcs).__init__(*args, **kwargs)


class CmdSet(object):
    """
    This class describes a unique cmdset that understands priorities. CmdSets
    can be merged and made to perform various set operations on each other.
    CmdSets have priorities that affect which of their ingoing commands
    gets used.

        In the examples, cmdset A always have higher priority than cmdset B.

        key - the name of the cmdset. This can be used on its own for game
        operations

        mergetype (partly from Set theory):

            Union -    The two command sets are merged so that as many
                        commands as possible of each cmdset ends up in the
                        merged cmdset. Same-name commands are merged by
                        priority.  This is the most common default.
                        Ex: A1,A3 + B1,B2,B4,B5 = A1,B2,A3,B4,B5
            Intersect - Only commands found in *both* cmdsets
                        (i.e. which have same names) end up in the merged
                        cmdset, with the higher-priority cmdset replacing the
                        lower one.  Ex: A1,A3 + B1,B2,B4,B5 = A1
            Replace -   The commands of this cmdset completely replaces
                        the lower-priority cmdset's commands, regardless
                        of if same-name commands exist.
                        Ex: A1,A3 + B1,B2,B4,B5 = A1,A3
            Remove -    This removes the relevant commands from the
                        lower-priority cmdset completely.  They are not
                        replaced with anything, so this in effects uses the
                        high-priority cmdset as a filter to affect the
                        low-priority cmdset.
                        Ex: A1,A3 + B1,B2,B4,B5 = B2,B4,B5

                     Note: Commands longer than 2 characters and starting
                           with double underscrores, like '__noinput_command'
                           are considered 'system commands' and are
                           excempt from all merge operations - they are
                           ALWAYS included across mergers and only affected
                           if same-named system commands replace them.

        priority- All cmdsets are always merged in pairs of two so that
                  the higher set's mergetype is applied to the
                  lower-priority cmdset. Default commands have priority 0,
                  high-priority ones like Exits and Channels have 10 and 9.
                  Priorities can be negative as well to give default
                  commands preference.

        duplicates - determines what happens when two sets of equal
                     priority merge. Default has the first of them in the
                     merger (i.e. A above) automatically taking
                     precedence. But if allow_duplicates is true, the
                     result will be a merger with more than one of each
                     name match.  This will usually lead to the player
                     receiving a multiple-match error higher up the road,
                     but can be good for things like cmdsets on non-player
                     objects in a room, to allow the system to warn that
                     more than one 'ball' in the room has the same 'kick'
                     command defined on it, so it may offer a chance to
                     select which ball to kick ...  Allowing duplicates
                     only makes sense for Union and Intersect, the setting
                     is ignored for the other mergetypes.

        key_mergetype (dict) - allows the cmdset to define a unique
                 mergetype for particular cmdsets.  Format is
                 {CmdSetkeystring:mergetype}. Priorities still apply.
                 Example: {'Myevilcmdset','Replace'} which would make
                 sure for this set to always use 'Replace' on
                 Myevilcmdset no matter what overall mergetype this set
                 has.

        no_objs  - don't include any commands from nearby objects
                      when searching for suitable commands
        no_exits  - ignore the names of exits when matching against
                            commands
        no_channels   - ignore the name of channels when matching against
                            commands (WARNING- this is dangerous since the
                            player can then not even ask staff for help if
                            something goes wrong)


    """
    __metaclass__ = _CmdSetMeta

    key = "Unnamed CmdSet"
    mergetype = "Union"
    priority = 0
    duplicates = False
    key_mergetypes = {}
    no_exits = False
    no_objs = False
    no_channels = False
    permanent = False
    errmessage = ""
    # pre-store properties to duplicate straight off
    to_duplicate = ("key", "cmdsetobj", "no_exits", "no_objs",
                    "no_channels", "permanent", "mergetype",
                    "priority", "duplicates", "errmessage")

    def __init__(self, cmdsetobj=None, key=None):
        """
        Creates a new CmdSet instance.

        cmdsetobj - this is the database object to which this particular
             instance of cmdset is related. It is often a character but
             may also be a regular object.
        """
        if key:
            self.key = key
        self.commands = []
        self.system_commands = []
        self.actual_mergetype = self.mergetype
        self.cmdsetobj = cmdsetobj
        # this is set only on merged sets, in cmdhandler.py, in order to
        # track, list and debug mergers correctly.
        self.merged_from = []

        # initialize system
        self.at_cmdset_creation()
        self._contains_cache = WeakKeyDictionary()#{}

    # Priority-sensitive merge operations for cmdsets

    def _union(self, cmdset_a, cmdset_b):
        "C = A U B. CmdSet A is assumed to have higher priority"
        cmdset_c = cmdset_a._duplicate()
        # we make copies, not refs by use of [:]
        cmdset_c.commands = cmdset_a.commands[:]
        if cmdset_a.duplicates and cmdset_a.priority == cmdset_b.priority:
            cmdset_c.commands.extend(cmdset_b.commands)
        else:
            cmdset_c.commands.extend([cmd for cmd in cmdset_b
                                      if not cmd in cmdset_a])
        return cmdset_c

    def _intersect(self, cmdset_a, cmdset_b):
        "C = A (intersect) B. A is assumed higher priority"
        cmdset_c = cmdset_a._duplicate()
        if cmdset_a.duplicates and cmdset_a.priority == cmdset_b.priority:
            for cmd in [cmd for cmd in cmdset_a if cmd in cmdset_b]:
                cmdset_c.add(cmd)
                cmdset_c.add(cmdset_b.get(cmd))
        else:
            cmdset_c.commands = [cmd for cmd in cmdset_a if cmd in cmdset_b]
        return cmdset_c

    def _replace(self, cmdset_a, cmdset_b):
        "C = A + B where the result is A."
        cmdset_c = cmdset_a._duplicate()
        cmdset_c.commands = cmdset_a.commands[:]
        return cmdset_c

    def _remove(self, cmdset_a, cmdset_b):
        "C = A + B, where B is filtered by A"
        cmdset_c = cmdset_a._duplicate()
        cmdset_c.commands = [cmd for cmd in cmdset_b if not cmd in cmdset_a]
        return cmdset_c

    def _instantiate(self, cmd):
        """
        checks so that object is an instantiated command
        and not, say a cmdclass. If it is, instantiate it.
        Other types, like strings, are passed through.
        """
        try:
            return cmd()
        except TypeError:
            return cmd

    def _duplicate(self):
        """
        Returns a new cmdset with the same settings as this one
        (no actual commands are copied over)
        """
        cmdset = CmdSet()
        for key, val in ((key, getattr(self, key)) for key in self.to_duplicate):
            if val != getattr(cmdset, key):
                # only copy if different from default; avoid turning
                # class-vars into instance vars
                setattr(cmdset, key, val)
        cmdset.key_mergetypes = self.key_mergetypes.copy()
        return cmdset
        #cmdset = self.__class__()
        #cmdset.__dict__.update(dict((key, val) for key, val in self.__dict__.items() if key in self.to_duplicate))
        #cmdset.key_mergetypes = self.key_mergetypes.copy() #copy.deepcopy(self.key_mergetypes)
        #return cmdset

    def __str__(self):
        """
        Show all commands in cmdset when printing it.
        """
        return ", ".join([str(cmd) for cmd in sorted(self.commands, key=lambda o:o.key)])

    def __iter__(self):
        """
        Allows for things like 'for cmd in cmdset':
        """
        return iter(self.commands)

    def __contains__(self, othercmd):
        """
        Returns True if this cmdset contains the given command (as defined
        by command name and aliases). This allows for things
        like 'if cmd in cmdset'
        """
        ret = self._contains_cache.get(othercmd)
        if ret is None:
            ret = othercmd in self.commands
            self._contains_cache[othercmd] = ret
        return ret

    def __add__(self, cmdset_b):
        """
        Merge this cmdset (A) with another cmdset (B) using the + operator,

        C = A + B

        Here, we (by convention) say that 'A is merged onto B to form
        C'.  The actual merge operation used in the 'addition' depends
        on which priorities A and B have. The one of the two with the
        highest priority will apply and give its properties to C. In
        the case of a tie, A takes priority and replaces the
        same-named commands in B unless A has the 'duplicate' variable
        set (which means both sets' commands are kept).
        """

        # It's okay to merge with None
        if not cmdset_b:
            return self

        sys_commands_a = self.get_system_cmds()
        sys_commands_b = cmdset_b.get_system_cmds()

        if self.priority >= cmdset_b.priority:
            # A higher or equal priority than B

            # preserve system __commands
            sys_commands = sys_commands_a + [cmd for cmd in sys_commands_b
                                             if cmd not in sys_commands_a]

            mergetype = self.key_mergetypes.get(cmdset_b.key, self.mergetype)
            if mergetype == "Intersect":
                cmdset_c = self._intersect(self, cmdset_b)
            elif mergetype == "Replace":
                cmdset_c = self._replace(self, cmdset_b)
            elif mergetype == "Remove":
                cmdset_c = self._remove(self, cmdset_b)
            else: # Union
                cmdset_c = self._union(self, cmdset_b)
            cmdset_c.no_channels = self.no_channels
            cmdset_c.no_exits = self.no_exits
            cmdset_c.no_objs = self.no_objs
            if self.key.startswith("_"):
                # don't rename new output if the merge set's name starts with _
                cmdset_c.key = cmdset_b.key

        else:
            # B higher priority than A

            # preserver system __commands
            sys_commands = sys_commands_b + [cmd for cmd in sys_commands_a
                                             if cmd not in sys_commands_b]

            mergetype = cmdset_b.key_mergetypes.get(self.key, cmdset_b.mergetype)
            if mergetype == "Intersect":
                cmdset_c = self._intersect(cmdset_b, self)
            elif mergetype == "Replace":
                cmdset_c = self._replace(cmdset_b, self)
            elif mergetype == "Remove":
                cmdset_c = self._remove(self, cmdset_b)
            else:  # Union
                cmdset_c = self._union(cmdset_b, self)
            cmdset_c.no_channels = cmdset_b.no_channels
            cmdset_c.no_exits = cmdset_b.no_exits
            cmdset_c.no_objs = cmdset_b.no_objs
            if cmdset_b.key.startswith("_"):
                # don't rename new output if the merge set's name starts with _
                cmdset_c.key = self.key

        # we store actual_mergetype since key_mergetypes
        # might be different from the main mergetype.
        # This is used for diagnosis.
        cmdset_c.actual_mergetype = mergetype

        # return the system commands to the cmdset
        cmdset_c.add(sys_commands)
        return cmdset_c

    def add(self, cmd):
        """
        Add a command, a list of commands or a cmdset to this cmdset.

        Note that if cmd already exists in set,
        it will replace the old one (no priority checking etc
        at this point; this is often used to overload
        default commands).

        If cmd is another cmdset class or -instance, the commands
        of that command set is added to this one, as if they were part
        of the original cmdset definition. No merging or priority checks
        are made, rather later added commands will simply replace
        existing ones to make a unique set.
        """

        if inherits_from(cmd, "src.commands.cmdset.CmdSet"):
            # cmd is a command set so merge all commands in that set
            # to this one. We raise a visible error if we created
            # an infinite loop (adding cmdset to itself somehow)
            try:
                cmd = self._instantiate(cmd)
            except RuntimeError:
                string = "Adding cmdset %(cmd)s to %(class)s lead to an "
                string += "infinite loop. When adding a cmdset to another, "
                string += "make sure they are not themself cyclically added to "
                string += "the new cmdset somewhere in the chain."
                raise RuntimeError(_(string) % {"cmd": cmd,
                                                "class": self.__class__})
            cmds = cmd.commands
        elif is_iter(cmd):
            cmds = [self._instantiate(c) for c in cmd]
        else:
            cmds = [self._instantiate(cmd)]
        commands = self.commands
        system_commands = self.system_commands
        for cmd in cmds:
            # add all commands
            if not hasattr(cmd, 'obj'):
                cmd.obj = self.cmdsetobj
            try:
                ic = commands.index(cmd)
                commands[ic] = cmd  # replace
            except ValueError:
                commands.append(cmd)
            # extra run to make sure to avoid doublets
            self.commands = list(set(commands))
            #print "In cmdset.add(cmd):", self.key, cmd
            # add system_command to separate list as well,
            # for quick look-up
            if cmd.key.startswith("__"):
                try:
                    ic = system_commands.index(cmd)
                    system_commands[ic] = cmd  # replace
                except ValueError:
                    system_commands.append(cmd)

    def remove(self, cmd):
        """
        Remove a command instance from the cmdset.
        cmd can be either a cmd instance or a key string.
        """
        cmd = self._instantiate(cmd)
        self.commands = [oldcmd for oldcmd in self.commands if oldcmd != cmd]

    def get(self, cmd):
        """
        Return the command in this cmdset that matches the
        given command. cmd may be either a command instance or
        a key string.
        """
        cmd = self._instantiate(cmd)
        for thiscmd in self.commands:
            if thiscmd == cmd:
                return thiscmd

    def count(self):
        "Return number of commands in set"
        return len(self.commands)

    def get_system_cmds(self):
        """
        Return system commands in the cmdset, defined as
        commands starting with double underscore __.
        These are excempt from merge operations.
        """
        return self.system_commands
        #return [cmd for cmd in self.commands if cmd.key.startswith('__')]

    def make_unique(self, caller):
        """
        This is an unsafe command meant to clean out a cmdset of
        doublet commands after it has been created. It is useful
        for commands inheriting cmdsets from the cmdhandler where
        obj-based cmdsets always are added double. Doublets will
        be weeded out with preference to commands defined on caller,
        otherwise just by first-come-first-served.
        """
        unique = {}
        for cmd in self.commands:
            if cmd.key in unique:
                ocmd = unique[cmd.key]
                if (hasattr(cmd, 'obj') and cmd.obj == caller) and not \
                        (hasattr(ocmd, 'obj') and ocmd.obj == caller):
                    unique[cmd.key] = cmd
            else:
                unique[cmd.key] = cmd
        self.commands = unique.values()

    def get_all_cmd_keys_and_aliases(self, caller=None):
        """
        Returns a list of all command keys and aliases
        available in this cmdset. If caller is given, the
        commands is checked for access on the "call" type
        before being returned.
        """
        names = []
        if caller:
            [names.extend(cmd._keyaliases) for cmd in self.commands
                           if cmd.access(caller)]
        else:
            [names.extend(cmd._keyaliases) for cmd in self.commands]
        return names

    def at_cmdset_creation(self):
        """
        Hook method - this should be overloaded in the inheriting
        class, and should take care of populating the cmdset
        by use of self.add().
        """
        pass
