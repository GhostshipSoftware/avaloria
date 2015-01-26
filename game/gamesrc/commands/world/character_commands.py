from ev import Command, CmdSet
from src.commands.default.muxcommand import MuxCommand

class CmdAttack(Command):
    """
    Begin to fight a target, typically an npc enemy.

    Usage:
        attack target-name

    """

    key = 'attack'
    aliases = ['kill']
    help_category = "Combat"
    locks = "cmd:all()"
    
    def parse(self):
        self.what = self.args.strip()
        
    def func(self):
        caller = self.caller
        mob = caller.search(self.what, global_search=False)
        if mob is None:
            return
        caller.begin_combat(mob)



class CmdTalk(Command):
    """
    Attempt to talk to the given object, typically an npc who is able to respond
    to you.  Will return gracefully if the particular object does not support
    having a conversation with the character.
    
    Usage:
        talk to <npc|object name> <whatever yer message is>

    NOTE: Just because you can talk to an npc does not mean that they care about
    or know about what you are discussing with them.  Typically the control words
    will be very easy to spot.
    """
    key = 'talk'
    aliases = ['talk to', 't']
    help_category = 'general'
    locks = "cmd:all()"

    def parse(self):
        if len(self.args) < 1:
            print "usage: talk to <npc> <message>"
            return
        args = self.args.split()
        self.npc = args[0]
        args.remove(self.npc)
        self.message = ' '.join(args)

    def func(self):
        if self.caller.db.in_combat:
            self.caller.msg("{RCan't talk to people while in combat!")
            return
        if len(self.args) < 1:
            self.caller.msg("usage: talk to <npc> <message>")
            return
        npc = self.caller.search(self.npc, global_search=False)
        if hasattr(npc, "combatant"):
            self.caller.msg("You can't talk to that, are you mad?")
        else:
            if npc is not None:
                self.caller.msg("{mYou tell %s: %s{n" % (npc.name, self.message)) 
                npc.dictate_action(self.caller, self.message)  
            else:
                self.caller.msg("I don not see anyone around by that name.")
                return
            


class CmdDisplaySheet(Command):
    """
    Display your character sheet.

    Usage:
        stats
    """
    key = 'stats'
    aliases = ['points', 'sheet']
    help_category = "General"
    locks = "cmd:all()"
    

    def func(self):
        caller = self.caller
        caller.display_character_sheet()


class CmdLoot(Command):
    """
    Pass a corpse name to this command to loot the corpse.
    
    Usage:
        loot <corpse>
    """

    key = 'loot'
    help_category = "General"
    locks = "cmd:all()"

    def parse(self):
        self.what = self.args.strip()
    
    def func(self):
        obj = self.caller.search(self.what, global_search=False)
        if obj is None:
            return
        if obj.db.corpse:
            if len(obj.contents) == 0:
                self.caller.msg("That corpse is empty.")
                obj.db.destroy_me = True
                return
            for i in obj.contents:
                if i.db.attributes['lootable']:
                    i.move_to(self.caller, quiet=True)
                    self.caller.msg("{CYou have looted a: %s{n" % i.name)
            obj.db.destroy_me = True
        else:
            self.caller.msg("{RThat is not a corpse.{n")

class CmdEquip(Command):
    key = 'equip'
    help_category = "General"
    locks = "cmd:all()"

    def parse(self):
        self.what = self.args.strip()

    def func(self):
        e = self.caller.db.equipment
        obj = self.caller.search(self.what, global_search=False)
        print e
        print obj
        oa = obj.db.attributes
        if obj is None:
            return
        e['%s' % oa['item_slot']] = obj
        self.caller.msg("{CYou have equipped: %s as your weapon.{n")
        

class CmdLook(MuxCommand):
    """
    look at location or object

    Usage:
      look
      look <obj>
      look *<player>

    Observes your location or objects in your vicinity.
    """
    key = "look"
    aliases = ["l", "ls"]
    locks = "cmd:all()"
    arg_regex = r"\s.*?|$"

    def func(self):
        """
        Handle the looking.
        """
        caller = self.caller
        args = self.args
        if args:
            # Use search to handle duplicate/nonexistant results.
            if self.caller.location.db.decor_objects is not None and len(self.caller.location.db.decor_objects) > 0:
                for k in self.caller.location.db.decor_objects:
                    print k
                    if k.lower() == args.lower():
                        caller.msg("%s" % self.caller.location.db.decor_objects[k])
                        return
            looking_at_obj = caller.search(args, use_nicks=True)
        
            if not looking_at_obj:
                return
        else:
            looking_at_obj = caller.location
            if not looking_at_obj:
                caller.msg("You have no location to look at!")
                return

        if not hasattr(looking_at_obj, 'return_appearance'):
            # this is likely due to us having a player instead
            looking_at_obj = looking_at_obj.character
        if not looking_at_obj.access(caller, "view"):
            caller.msg("Could not find '%s'." % args)
            return
        # get object's appearance
        caller.msg(looking_at_obj.return_appearance(caller))
        # the object's at_desc() method.
        looking_at_obj.at_desc(looker=caller)

class CmdEquip(Command):
    """
    This attempts to equip items on the character. If no arguements are
    given, then it picks the first item for each slot it finds and equips
    those items in their respective slots.

    usage: 
        equip <item to equip>
    
    aliases: wield, equip item, e
    """
    key = 'equip'
    aliases = ['equip item', 'wield', 'e']
    help_category = "General"
    locks = "cmd:all()"

    def parse(self):
        if len(self.args) < 1:
            self.what = None
        else:
            self.what = self.args.strip()

    def func(self):
        if self.caller.db.in_combat:
            self.caller.msg("{RCan't equip while in combat!")
        if len(self.args) < 1:
            self.caller.msg("What did you want to equip?  equip <item to equip>")
            return
        if self.what is not None:
            obj = self.caller.search(self.what, global_search=False)
            if not obj:
                self.caller.msg("Are you sure you are carrying the item you are trying to equip?")
            else:
                self.caller.equip_item(ite=obj, slot=obj.db.attributes['item_slot'])
                obj.on_equip()
        else:
            self.caller.equip_item(ite=None,slot=None)
                   
class CharacterCmdSet(CmdSet):

    key = "CharacterClassCommands"

    def at_cmdset_creation(self):
        self.add(CmdAttack())
        self.add(CmdLoot())
        self.add(CmdDisplaySheet())
        self.add(CmdEquip())
        self.add(CmdTalk())
        self.add(CmdLook())
        self.add(CmdEquip())

