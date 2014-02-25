from ev import Object
import random

class Npc(Object):
    """
    Main npc class that is used for hostiles and friendlies alike.
    
    this controls any NON character entity that is a living being.

    TODO:
        cleanup the combat code and make it relevant.  It's crap.
        cleanup the code that dictates currency rewards, its lazy
        and crappy in its current incarnation.
    """

    def at_object_creation(self):
        self.db.attributes = { 'strength': 10, 'constitution': 10, 'intelligence': 10, 'dexterity': 10, 'luck': 5, 'health': 0, 'mana': 0, 'stamina': 0, 'temp_health': 0, 'temp_stamina': 0, 'temp_mana': 0, 'level': 1, 'exp_needed': 300, 'exp': 0, 'total_exp': 0, 'exp_reward': 0, 'currency_reward': {}, 'persona': None, 'visible': True, 'perception_threshold': 20}
        self.db.combat_attributes = {'attack_bonus': 1, 'damage_threshold': 0, 'armor_rating': 1, 'defense_rating': 1}
        self.db.equipment = {'weapon': None, 'protection': None}
        attributes = self.db.attributes
        attributes['health'] = attributes['constitution'] * 4
        attributes['temp_health'] = attributes['health']
        attributes['stamina'] = attributes['constitution'] * 2
        attributes['temp_stamina'] = attributes['stamina']
        attributes['mana'] = attributes['intelligence'] * 4
        attributes['temp_mana'] = attributes['mana']
        self.db.attributes = attributes
        self.db.in_combat = False
        self.db.corpse = False
        self.db.destroy_me = False
        self.db.target = None
        self.db.difficulty_rating = 'average' #(average, hard, very_hard, impossible)
        self.aliases.append('mob_runner')
        


    def generate_attributes(self):
        a = self.db.attributes
        print "generating attributes: %s" % self.db.difficulty_rating
        if self.db.difficulty_rating in 'average':
            print "average logic"
            strength = random.randrange(10, 18 )
            endurance = random.randrange(10, 18)
            perception = random.randrange(10, 18)
            agility = random.randrange(10, 18)
            luck = random.randrange(5, 15)
            currency_reward = random.randrange(30, 68)
            currency_type = 'copper'
            exp_reward = random.randrange(25, 35)
        elif self.db.difficulty_rating in 'hard':
            strength = random.randrange(15, 35)
            endurance = random.randrange(15, 35)
            perception = random.randrange(15, 35)
            agility = random.randrange(15, 35)
            luck = random.randrange(10, 20)
            currency_reward = random.randrange(8, 20)
            currency_type = 'silver'
            exp_reward = random.randrange(35, 50)
        elif self.db.difficulty_rating in 'very_hard':
            strength = random.randrange(20, 40)
            endurance = random.randrange(20, 40)
            perception = random.randrange(20, 40)
            agility = random.randrange(20, 40)
            luck = random.randrange(15, 30)
            currency_reward = random.randrange(20, 30)
            currency_type = 'gold'
            exp_reward = random.randrange(50, 75)
            
        ca = self.db.combat_attributes
        a['strength'] = strength
        a['constitution'] = endurance
        a['intelligence'] = perception
        a['dexterity'] = agility
        a['luck'] = luck
        a['exp_reward'] = exp_reward
        a['currency_reward'][currency_type] = currency_reward
        ca['attack_bonus'] = (a['strength'] + a['dexterity']) / 10
        ca['damage_threshold'] = (a['strength'] + a['constitution']) / 10
        ca['armor_rating'] = (a['dexterity'] + a['intelligence']) / 10
        ca['defense_rating'] = ca['damage_threshold'] + ca['armor_rating']
        a['health'] = a['constitution'] * 4
        a['stamina'] = a['constitution'] * 2
        a['mana'] = a['intelligence'] * 4
        a['temp_mana'] = a['mana']
        a['temp_health'] = a['health']
        a['temp_stamina'] = a['stamina']
        self.db.attributes = a
        self.db.combat_attributes = ca
        print "attr gen complete"

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
            
        

    #############################
    #COMBAT RELATED FUNCTIONS   #
    #############################

    def take_damage(self, damage):
        a = self.db.attributes
        print a['temp_health']
        a['temp_health'] -= damage
        self.db.attributes = a
    
    def get_damage(self):
        w = self.db.equipment['weapon']
        if w is None:
            damagedice = (1, 4)
            damage = random.randrange(damagedice[0], damagedice[1])
            return damage
        else:
            damagedice = w.db.damage
            damage = random.randrange(damagedice[0], damagedice[1])
            return damage

    def attack_roll(self):
        adice = (1, 20)
        roll = random.randrange(adice[0], adice[1])
        return roll

    def get_initiative(self):
        """
        roll for attack initiative
        """
        idice = (1, 20)
        roll = random.randrange(idice[0], idice[1])
        return roll

    def do_attack_phase(self):
        a = self.db.attributes
        e = self.db.equipment
        t = self.db.target
        w = e['weapon']
        attack_roll = self.attack_roll()
        if attack_roll >= t.db.combat_attributes['defense_rating']:
            damage = self.get_damage()
            unarmed_hit_texts = [ '%s punches you relentlessly for %s damage!' % (self.name, damage),           
                                   '%s pummels the daylights out of you for %s damage.' % (self.name, damage),           
                                   'You attempt to grab %s, but they dodge and uppercut youfor %s damage.' % (self.name, damage),
                                   '%s punches you hard in the mouth for %s damage.' % (self.name, damage),
                                   'As %s lands a hard blow against you, you feel bones breaking under your skin.  You take %s damage.' % (self.name, damage) 
            ]
            if w:
                gun_hit_texts = [ 'As %s rapidly pulls the trigger of their %s, it hits you dead on dealing %s damage' % ( self.name, w.name, damage),
                                'With a squeeze of the trigger and the report of the %s, %s does %s damage to you.' % (w.name, damage, self.name),
                                '%s lets off a volley of shots hitting you dealing %s damage.' % (self.name, damage),
                                '%s unleashes a hail of lead upon you dealing %s damage.' % (self.name, damage) 
                ]
            melee_hit_texts = []
            if w is None:
                ht = random.choice(unarmed_hit_texts)
            elif w is not None and w['type'] is 'gun':
                ht = random.choice(gun_hit_texts)
            t.msg(ht)
            t.take_damage(damage)
    
    def do_skill_phase(self):
        pass


    def death(self):
        self.db.target = None
        self.db.corpse = True
        l = self.location
        mobs = l.db.mobs
        mobs.remove(self)
        l.db.mobs = mobs
        self.aliases = [ 'corpse' ]
        self.key = "Corpse of %s" % self.name
