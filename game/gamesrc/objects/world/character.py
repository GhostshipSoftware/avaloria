from ev import Object, Character, utils, create_object, create_channel
from game.gamesrc.commands.world.character_commands import CharacterCmdSet
import random
from prettytable import PrettyTable



class Hero(Character):
    """
    Main player character class

    This class will be a very large part of just about everything related to the game.

    TODO:
        Allow for auxillary stats to be updated when core attributes change (i.e. buffs and debuffs).
        Effects manager -  Write a management function to add and remove effects from the character
        model.
        Crafting manager - Need something to facilitate crafting.  Most of this will likely end up
        here.
    """

    def at_object_creation(self):
        self.db.attributes = { 'name': None, 
                                'strength': 10,
                                'constitution': 10,
                                'intelligence': 10,
                                'dexterity': 10,
                                'luck': 10,
                                'health': 0,
                                'mana': 0,
                                'stamina': 0,
                                'temp_health': 0,
                                'temp_mana': 0,
                                'temp_stamina': 0,
                                'level': 0,
                                'exp_needed': 300,
                                'exp': 0,
                                'total_exp': 0,
                                }
        self.db.combat_attributes = {'attack_rating': 0, 'armor_rating': 0, 'defense_rating': 0 }
        self.db.currency = { 'gold': 0, 'silver': 0, 'copper': 0 }
        self.db.skills = { 'listen': { 'rating': 0, 'desc': 'Your ability to listen to your surroundings.'},
                            'search': { 'rating': 0, 'desc': 'Your ability to search your surroundings visually'},
                            'bladed weapons': { 'rating': 0, 'desc': 'Your innate ability to wield bladed weaponry'},
                            'blunt weapons': {'rating': 0, 'desc': 'Your innate ability to wield blunt weaponry.'},
                            }
        self.db.archtypes = { 'soldier': { 'level': 1, 'exp_to_level': 100, 'exp': 0, 'total_exp': 0 },
                                'mage': { 'level': 1, 'exp_to_level': 100, 'exp': 0, 'total_exp': 0 },
                                'rogue': { 'level': 1, 'exp_to_level': 100, 'exp': 0, 'total_exp': 0 },
                                'leader': { 'level': 1, 'exp_to_level': 100, 'exp': 0, 'total_exp': 0}
                            }
        self.db.equipment = { 'armor': None, 'main_hand_weapon': None, 'offhand_weapon': None, 'shield': None, 'right_hand_ring': None, 'left_hand_ring': None}

	#Object creation
	questlog = create_object('game.gamesrc.objects.world.quests.QuestManager', location=self, key="Questlog")
	self.db.questlog = questlog
        self.tags.add('character_runner')
        self.at_post_creation()


    def at_post_creation(self):
        """
        Hook used to set auxillary stats that are based off of
        core attributes.  Called at the end of at_object_creation
        """
        a = self.db.attributes
        c = self.db.combat_attributes
        a['health'] = a['constitution'] * 4
        a['temp_health'] = a['health']
        a['mana'] = a['intelligence'] * 4
        a['temp_mana'] = a['mana']
        a['stamina'] = a['constitution'] * 2
        a['temp_stamina'] = a['stamina']
        c['attack_rating'] = a['dexterity'] / 10
        c['defense_rating'] = (a['dexterity'] / 10) + 10
        c['damage_threshold'] = a['constitution'] / 10
        self.db.attributes = a
        self.db.combat_attributes = c


    def at_disconnect(self):
        self.prelogout_location = self.location

    def at_post_puppet(self):
        self.cmdset.add(CharacterCmdSet)
        self.location = self.db.prelogout_location
   

    def display_character_sheet(self):
        a_table = PrettyTable()
        ca_table = PrettyTable()
        a_table._set_field_names(["Attributes", "Value"])
        ca_table._set_field_names(["Attributes", "Value"])
        for k in self.db.attributes:
            a_table.add_row(["%s:" % k, self.db.attributes[k]])
        for k in self.db.combat_attributes:
            ca_table.add_row(["%s:" % k , self.db.combat_attributes[k]])
        a_string = a_table.get_string()
        self.msg(a_string)
        ca_string = ca_table.get_string()
        self.msg(ca_string) 
         
    def award_currency(self, amount, type='copper'):
        """
        award the passed amount of currency to the characters money levels.
        """
        c = self.db.currency
        c[type] += amount
        self.msg("{CYou have received %s %s.{n" % (amount, type))
        self.db.currency = c
        

    def award_exp(self, exp, archtype=None):
        """
        Award passed amount of experience to character experience levels and
        archtype experience levels.
        """
        attributes = self.db.attributes
        archtypes = self.db.archtypes
        if archtype is None:
            self.msg("{CYou have earned %s experience.{n" % exp)     
        else:
            self.msg("{CYou have earned %s experience in archtype: %s" % (exp, archtype)) 
        if archtype is not None:
            archtypes[archtype]['exp'] += exp
            archtypes[archtype]['total_exp'] += exp
            self.db.archtypes = archtypes
            if archtypes[archtype]['exp'] == archtypes[archtype]['exp_to_level']:
                self.level_up_archtype(archtype='%s' % archtype)
            elif archtypes[archtype]['exp'] > archtypes[archtype]['exp_to_level']:
                offset = archtypes[archtype]['exp'] - archtypes[archtype]['exp_to_level']
                self.level_up_archtype(archtype='%s' % archtype, offset=offset)
        attributes['exp'] += exp
        attributes['total_exp'] += exp
        self.db.attributes = attributes
        if attributes['exp'] == attributes['exp_needed']:
            self.level_up()
        elif attributes['exp'] > attributes['exp_needed']:
            offset = attributes['exp'] - attributes['exp_needed']
            self.level_up(offset=offset) 

    def level_up_archtype(self, archtype, offset=None):
        archtypes = self.db.archtypes
        if archtype is not None:
            if offset is not None:
                archtypes[archtype]['exp'] = offset
                archtypes[archtype]['exp_to_level'] = archtypes[archtype]['total_exp'] * 1.5
                archtypes[archtype]['level'] += 1
            else:
                archtypes[archtype]['exp'] = 0
                archtypes[archtype]['exp_to_level'] = archtypes[archtype]['total_exp'] * 1.5
                archtypes[archtype]['level'] += 1
                
            self.msg("{cYou have gained an archtype level in: {C%s.{n" % archtype)
            self.db.archtypes = archtypes
        else:
            return

    def tick(self):
        """
        Main function for all things needing to be done/checked every time the mob tick
        script fires itself (health and mana regen, kos checks etc etc)
        """
        a = self.db.attributes
        if a['temp_health'] < a['health'] and not self.db.in_combat:
            pth = int(a['health'] * .02) + 1
            a['temp_health'] = a['temp_health'] + pth
            if a['temp_health'] > a['health']:
                a['temp_health'] = a['health']

        self.db.attributes = a

    def take_damage(self, damage):
        """
        remove health when damage is taken
        """
        a = self.db.attributes
        a['temp_health'] -= damage
        self.db.attributes = a

    ###########################
    #COMBAT RELATED FUNCTIONS##
    ###########################

    def begin_combat(self, target):
        """
        begins combat sequence
        """
        self.db.target = target
        target.db.target = self
        self.scripts.add("game.gamesrc.scripts.world_scripts.combat.CombatController")

    def unconcious(self):
        """
        put a character unconcious, which adds a script that checks to see if they
        have woken up yet from their dirt nap.
        """
        attributes = self.db.attributes
        attributes['temp_health'] = attributes['health']
        self.db.attributes = attributes
        self.db.in_combat = False
        
       # self.db.unconcious = True
        
    def get_initiative(self):
        """
        roll for attack initiative
        """
        idice = (1, 20)
        roll = random.randrange(idice[0], idice[1])
        return roll

    def do_attack_phase(self):
        """
        run through attack logic and apply it to self.db.target,
        return gracefully upon None target.
        """
        t = self.db.target
        e = self.db.equipment
        w = e['main_hand_weapon']
        attack_roll = self.attack_roll()
        print "attack roll"
        if attack_roll >= t.db.combat_attributes['defense_rating']:
            damage = self.get_damage()
            unarmed_hit_texts = [ 'You punch %s unrelenlessly for %s damage' % (t.name, damage),
                                   'You pummel the daylights out of %s for %s damage.' % (t.name, damage),
                                   'As %s attempts to grab you, you dodge and uppercut them for %s damage.' % (t.name, damage),
                                   'You punch %s hard in the mouth for %s damage' % (t.name, damage),
                                   'As you land a hard blow against %s, you feel bones breaking under your fist.  You deal %s damage.' % (t.name, damage)
                                ]
            print "unarmed hit texts"
            if w is None:
                ht = random.choice(unarmed_hit_texts)
            self.msg(ht) 
            t.take_damage(damage)
        else:
            #miss
            pass

    def do_skill_phase(self):
        #placeholder
        pass
        
    def get_damage(self):
        e = self.db.equipment
        w = e['main_hand_weapon']
        if w is None:
            damagedice = (1, 4)
            damage = random.randrange(damagedice[0], damagedice[1])
            return damage
        else:
            damagedice = w.db.attributes['damage_dice']
            damage = random.randrange(damagedice[0], damagedice[1])
            return damage

    def attack_roll(self):
        dice = (1, 20)
        roll = random.randrange(dice[0], dice[1])
        return roll
