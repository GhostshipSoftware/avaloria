from ev import Object
from prettytable import PrettyTable
import random

class Item(Object):
    """
    base item class used for attributes and methods
    global to all items regardless of type.
    """

    def at_object_creation(self):
        self.db.item_type = None
        self.db.attributes = { 'weight': 1.0, 'value': { 'gold': 5 }, 'equipable': False, 
                                'quest_item': False, 'item_slot': None, 'is_equipped': False, 
                                'display_name': None, 'lootable': False , 'damage_dice': None,
                                'critical_range': None, 'weapon_type': None, 'useable': None,
                                'crafting_material': False, 'crafting_group': None
                                 }
        self.db.attribute_bonuses = {'strength': 0, 'dexterity': 0, 'intelligence': 0, 
                                        'constitution': 0,  'attack_bonus': 0, 'armor_rating': 0, 
                                        'damage_threshold': 0, 'defense_rating': 0, 'luck': 0}

    def generate_attributes(self):
        a = self.db.attributes
 
        
        
            
    def on_equip(self):
        ca = self.location.db.attributes
        for b in self.db.attribute_bonuses:
            if self.db.attribute_bonuses[b] > 0:
                ca[b] = self.db.attribute_bonuses[b] + ca[b]
        self.location.db.attributes = ca
        
    def on_unequip(self):
        ca = self.location.db.attributes
        for b in self.db.attribute_bonuses:
            if self.db.attribute_bonuses[b] > 0:
                ca[b] = self.db.attribute_bonuses[b] - ca[b]
        self.location.db.attributes = ca

    def at_inspect(self):
        a = self.db.atrributes
        table = PrettyTable(['Name', 'Type', 'Value', 'Weight', 'Attribute Bonuses'])
        attrbstring = ''
        for b in self.db.attribute_bonuses:
            if self.db.attribute_bonuses[b] > 0:
                attrbstring += "{G%s:{n {C+%s{n\n" % (b, self.db.attribute_bonuses[b])
            
        table.add_row(['%s' % self.key, '%s' % self.db.type, '%s' % a['value']['dollars'], '%s' % a['weight'], attrbstring])
        print table

    def get_damage(self):
        a = self.db.attributes
        dd = a['damage_dice']
        if dd is None:
            return
        roll = random.randrange(dd[0], dd[1])
        return roll
