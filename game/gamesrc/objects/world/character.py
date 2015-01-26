from ev import Object, Character, utils, create_object, create_channel, search_object_tag
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
        self.db.attributes = { 'name': self.key, 
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
                                'level': 1,
                                'exp_needed': 300,
                                'exp': 0,
                                'experience_currency': 0,
                                'total_exp': 0,
                                'race': None,
                                'deity': None,
                                'gender': None,
                                }
        self.db.combat_attributes = {'attack_rating': 0, 'armor_rating': 0, 'defense_rating': 0 }
        self.db.currency = { 'gold': 0, 'silver': 0, 'copper': 0 }
        self.db.skills = { 'listen': { 'rating': 0, 'desc': 'Your ability to listen to your surroundings.'},
                            'search': { 'rating': 0, 'desc': 'Your ability to search your surroundings visually'},
                            'bladed weapons': { 'rating': 0, 'desc': 'Your innate ability to wield bladed weaponry'},
                            'blunt weapons': {'rating': 0, 'desc': 'Your innate ability to wield blunt weaponry.'},
                            'hide': { 'rating': 0, 'desc': 'Your innate ability to hide in the shadows and become unseen.'},
                            
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
   

    def accept_quest(self, quest):
        print "In accept_quest"
        manager = self.db.questlog
        quest_object = search_object_tag(quest.lower())[0]
        print quest_object
        exclusions = quest_object.db.exclusions
        print exclusions
        attributes = self.db.attributes
        
        try:
            split_list = exclusions.split(":")
        except:
            split_list = []
        print len(split_list)
        if len(split_list) > 1:
            print "in deity logic"
            attribute = split_list[0]
            exclude = split_list[1]
            if 'deity' in attributes:
                if attributes['deity'] in exclude:
                    self.msg("{rYou are a devout follower of %s and therefore have moral and religious objections to what this person asks of you.{n" % attributes['deity'])
                    return 
        print "past deity checks"
        if quest_object.db.prereq is not None:
            if ';' in quest_object.db.prereq:
                found = 0
                split_list = quest_object.prereq.split(';')
                for item in split_list:
                    item = item.strip()
                    if item.title() in [key.title() for key in manager.db.completed_quests.keys()]:
                        found = 1
                if found != 1:
                    self.msg("{RPre req not met.{n")
                    return
            else:
                if quest_object.prereq.title() in [key.title() for key in manager.db.completed_quests.keys()]:
                    pass
                else:
                    self.msg("{RPre requisite not met.{n")
                    return 
        character_quest = quest_object.copy()
        character_quest.name = quest_object.name
        character_quest.add_help_entry()
        manager.add_quest(character_quest)
        character_quest.move_to(manager, quiet=True)
        self.db.quest_log = manager
        self.msg("{yYou have accepted: %s" % character_quest.name)
        return

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
        attributes['total_exp'] = int(attributes['total_exp']) + int(exp)
        attributes['experience_currency'] += int(exp)
        difference = int(attributes['exp_needed']) - exp
        if difference == 0:
            self.level_up(zero_out_exp=True)
            return
        elif difference < 0:
            #self.msg("Added %s to %s" %(attributes['experience_needed'], difference))
            attributes['exp_needed'] = int(attributes['exp_needed']) + difference
            #get a positive number for the amount made into the next level
            positive_difference = difference * -1
            exp_made = positive_difference
            attributes['exp_made'] = exp_made
            attributes['exp_needed'] = attributes['exp_needed'] - exp_made
            self.db.attributes = attributes
            self.level_up(difference=positive_difference)
            return
        attributes['exp_made'] = (int(attributes['exp_made']) + exp)
        attributes['exp_needed'] = (int(attributes['exp_needed']) - exp)
        self.db.attributes = attributes
        self.msg("{gYou have been awarded %s experience.{n" % exp_to_award)
        return

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
    
    def level_up(self, zero_out_exp=False, difference=0):
        attributes = self.db.attributes
        attributes['level'] = int(attributes['level']) + 1
        if zero_out_exp is True:
            attributes['experience_made'] = 0
        attributes['experience_needed'] = int((int(attributes['total_exp_made']) * .50) + attributes['total_exp_made'])
        attributes['experience_to_next_level'] = attributes['experience_needed']
        attributes['experience_needed'] = attributes['experience_needed'] - attributes['experience_made']
        attributes['attribute_points'] = attributes['attribute_points'] + (int(attributes['intelligence'] / 2))
        self.db.attributes = attributes
        self.msg("{CYou have gained a level of experience! You are now level %s! {n" % attributes['level'])

    def equip_item(self, ite=None, slot=None):
        """ 
        Equip items, either specified or not.  If no item is given, then
        we simply try to equip the first item we find in our inventory for
        each slot type respectively.
        """
        equipment = self.db.equipment
        if equipment[slot] is not None:
            self.msg("You must unequip %s before you may equip %s." % (equipment[slot].name, ite.name))
            return
 
        if ite is None:
            wep_equipped = 0
            armor_equipped = 0
            lring_equipped = 0
            rring_equipped = 0
            back_equipped = 0
            trinket_equipped = 0
            shield_equipped = 0

            for item in self.contents:
                if item.db.item_type is not None:
                    if 'weapon' in item.db.slot and wep_equipped == 0:
                        equipment['weapon'] = item
                        wep_equipped = 1
                        item.on_equip()
                    elif 'armor' in item.db.slot and armor_equipped == 0:
                        equipment['armor'] = item
                        armor_equipped = 1
                        item.on_equip()
                    elif 'left finger' in item.db.slot and lring_equipped == 0:
                        equipment['left finger'] = item
                        lring_equipped = 1
                        item.on_equip()
                    elif 'right finger' in item.db.slot and rring_equipped == 0:
                        equipment['right finger'] = item
                        rring_equipped = 1
                        item.on_equip()
                    elif 'back' in item.db.slot and back_equipped == 0:
                        equipment['back'] = item
                        back_equipped = 1
                        item.on_equip()
                    elif 'trinket' in item.db.slot and trinket_equipped == 0:
                        equipment['trinket'] = item
                        trinket_equipped = 1
                        item.on_equip()
                    elif 'shield' in item.db.slot and shield_equipped == 0:
                        equipment['shield'] = item
                        shield_equipped = 1
                        item.on_equip()

            if wep_equipped != 1:
                self.msg("You had no weapons to equip.")
            else:
                self.db.equipment = equipment
                self.msg("You now wield %s in your main hand." % self.db.equipment['weapon'])

            if armor_equipped != 1:
                self.msg("You had no armor to equip")
            else:
                self.db.equipment = equipment
                self.msg("You are now wearing %s for armor." % self.db.equipment['armor'])
            return
                
        if 'main_hand_weapon' in slot:
            equipment[slot] = ite
            self.db.equipment = equipment
            self.msg("You now wield %s in your main hand." % self.db.equipment['main_hand_weapon'])
        elif 'armor' in slot:
            equipment['armor'] = ite
            self.db.equipment = equipment
            self.msg("You are now wearing %s for armor." % self.db.equipment['armor'])
        elif 'left finger' in slot:
            equipment['left finger'] = ite
            self.db.equipment = equipment
            self.msg("You are now wearing %s on your left finger." % ite.name)
        elif 'right finger' in slot:
            equipment['right finger'] = ite
            self.db.equipment = equipment
            self.msg("You are now wearing %s on your right finger." % ite.name)
        elif 'back' in slot:
            equipment['back'] = ite
            self.db.euqipment = equipment
            self.msg("You are now wearing %s on your back." % ite.name)
        elif 'shield' in slot:
            equipment['shield'] = ite
            self.db.equipment = equipment
            self.msg("You are now using %s as a shield" % ite.name)
        elif 'trinket' in slot:
            equipment['trinket'] = ite
            self.db.equipment = equipment
            self.msg("You are now using %s as your trinket." % ite.name)
        else:
            self.msg("{r%s is not equippable in any slot!{n" % ite)
            
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
            sword_hit_texts = [ 'You swing your blade deftly at %s for %s damage.' % (t.name, damage) ]
            print "unarmed hit texts"
            if w is None:
                ht = random.choice(unarmed_hit_texts)
            else:
                if w.db.attributes['weapon_type'] == 'sword':
                    ht = random.choice(sword_hit_texts)
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
    
#################################
# SETTERS
#################################

    def set_deity(self, deity):
        attributes = self.db.attributes
        attributes['deity'] = deity
        self.db.attributes = attributes
        
    def set_race(self, race):
        attributes = self.db.attributes
        attributes['race'] = race
        self.db.attributes = attributes
        
    def set_gender(self, gender):
        attributes = self.db.attributes
        attributes['gender'] = gender
        self.db.attributes = attributes

##################################
# BOOLEAN CHECKS
##################################

    def on_quest(self, quest, completed=False):
        """
        return true if on said quest,
        false otherwise.
        """
        manager = self.db.questlog
        print "objects.world.character.CharacterClass on_quest check => %s " % quest
        if completed:
            print "in completed"
            quest = manager.find_quest(quest, completed=True)
        else:
            print "non completed"
            quest = manager.find_quest(quest)
        if quest is None:
            return False
        else:
            return True
