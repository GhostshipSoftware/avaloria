from ev import Command, CmdSet

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
            if npc is not None:
                self.caller.msg("{mYou tell %s: %s{n" % (npc.name, self.message)) 
                npc.dictate_action(self.caller, self.message)  
            else:
                self.caller.msg("I don not see anyone around by that name.")
                return
        else:
            self.caller.msg("You can't talk to that, are you mad?")


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
        

                   
class CharacterCmdSet(CmdSet):

    key = "CharacterClassCommands"

    def at_cmdset_creation(self):
        self.add(CmdAttack())
        self.add(CmdLoot())
        self.add(CmdDisplaySheet())
        self.add(CmdEquip())
        self.add(CmdTalk())

