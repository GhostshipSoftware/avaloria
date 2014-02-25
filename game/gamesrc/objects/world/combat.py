from ev import Object

class CombatManager(Object):
    """
    Main Combat management object.
    """

    def at_object_creation(self):
        self.db.pc_combatant = None
        self.db.npc_combatant = None
        self.db.round = 0

    def do_round(self):
        pc_initiative = self.db.pc_combatant.get_initiative()
        npc_initiative = self.db.npc_combatant.get_initiative()
        pc = self.db.pc_combatant
        npc = self.db.npc_combatant
        if pc_initiative > npc_initiative:
                print "in attack block pc"
                pc.do_attack_phase()
                pc.do_skill_phase()
                npc.do_attack_phase()
                npc.do_skill_phase()
        else:
                print "in attack block npc"
                npc.do_attack_phase()
                npc.do_skill_phase()
                pc.do_attack_phase()
                pc.do_skill_phase()
        print "going to stats"
        self.check_stats()
    
    def check_stats(self):
        print "in stats"
        pc = self.db.pc_combatant
        npc = self.db.npc_combatant
        if pc.db.attributes['temp_health'] <= 0:
            pc.msg("{RYou have been slain by %s unmercifully, death awaits..{n" % npc.name)
            pc.db.in_combat = False 
            pc.unconcious() 
        if npc.db.attributes['temp_health'] <= 0:
            pc.db.in_combat = False
            pc.msg("{CYou have destroyed %s!{n" % npc.name)
            if npc.db.attributes['exp_reward'] > 0:
                pc.award_exp(npc.db.attributes['exp_reward'])
                pc.award_exp(npc.db.attributes['exp_reward'], archtype='soldier')
            if len(npc.db.attributes['currency_reward'].keys()) > 0:
                for ct in npc.db.attributes['currency_reward']:
                    pc.award_currency(npc.db.attributes['currency_reward'][ct], type=ct)
            npc.death()
