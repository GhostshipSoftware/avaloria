from ev import Script, create_object


class CombatController(Script):
    """
    Main battle arbitration script
    """

    def at_script_creation(self):
        self.key = 'battle_arbiter'
        self.interval = 5
        self.persistent = False
        self.desc = "Combat Management Script"
        self.db.pc = self.obj
        self.db.npc = self.obj.db.target


    def at_start(self):
        self.obj.db.in_combat = True
        cm = create_object("game.gamesrc.objects.world.combat.CombatManager", key="%s_combat_manager" % self.obj.name)
        if self.obj.db.combat_manager is not None:
            try:
                old_cm = self.obj.db.combat_manager
                old_cm.delete()
            except AttributeError:
                pass

        self.obj.db.combat_manager = cm
        cm.db.pc_combatant = self.db.pc
        cm.db.npc_combatant = self.db.npc

    def at_repeat(self):
        cm = self.obj.db.combat_manager
        cm.db.round += 1
        cm.do_round()

    def at_stop(self):
        cm = self.obj.db.combat_manager
        if cm is not None:
            cm.delete()
        cm = None

    def is_valid(self):
        return self.obj.db.in_combat

