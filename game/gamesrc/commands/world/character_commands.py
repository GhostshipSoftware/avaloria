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
        self.add(CmdEquip())

