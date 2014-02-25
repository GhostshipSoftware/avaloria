from ev import Object, create_object
import random

class ItemFactory(Object):
    """
    Main Item generator.  generates items based on list seeds.
    """

    def at_object_creation(self):
        self.db.gun_weapon_types = [ 'pistol', 'rifle', 'shotgun', 'smg' ]
        self.db.melee_weapon_types = [ 'bladed', 'non-bladed']
        self.db.gun_pistol_names = [ 'Glock 9mm', 'CZ 75', 'P22', 'Springfield 1911', 'P95', 'SR22', 'LC9' ]
        self.db.gun_rifle_names = [ 'AR-15', 'AK-47', 'SKS', '10/22', 'M4', 'M1A', 'M1 Garand', 'M1 Carbine']
        self.db.gun_shotgun_names = [ 'SPAS-12', 'UTS-15', 'KSG', 'Mossberg 500', 'Remington 870' ]
        self.db.gun_smg_names =  [ 'AK74U', 'Uzi', 'Mac 11', 'MP5K', 'MP5', 'Sepctre M4' ]
        self.db.loot_ratings = ['below average', 'fair', 'good', 'excellent']
        self.db.scavenging_items = {'Can of Beans': .01, 'Bag of Rice': .10, 'Metal Scraps': .35, 'Wood Scraps':.35, 'Wood planks':.15, 'Sheet metal': .10, 'Old tire rubber':.40, 
                                    'Old can of Spinach':.12, 'Bottle of Water':.07, 'Old can of Soda': .1, 'Candybar': .20, 'Can of Carrots': .15, 'Can of Green beans': .01,
                                    'Bag of Northern Beans': .30, 'Can of Oranges': .15, 'Can of Pears': .20, 'Can of Peaches': .20, 'Nails and Screws': .30, 'Nuts and Bolts': .40,
                                    'First Aid Kit': .25, 'Pain Reliever': .40 }

   
    def create_lootset(self, number_of_items, loot_rating='below average'):
        loot_set = []
        print "begin loot set logic"
        if number_of_items == 0:
            return []
        for x in range(0, number_of_items):
            mix = ['gun', 'scavenging']
            c = random.choice(mix)
            if 'gun' in c:
                print "creating a gun."
                type = random.choice(self.db.gun_weapon_types)
                if 'pistol' in type:
                    name = random.choice(self.db.gun_pistol_names)
                    dd = (2,6)
                elif 'rifle' in type:
                    name = random.choice(self.db.gun_rifle_names)
                    dd = (2,10)
                elif 'shotgun' in type:
                    name = random.choice(self.db.gun_rifle_names)
                    dd = (3,10)
                elif 'smg' in type:
                    name = random.choice(self.db.gun_smg_names)
                    dd = (3,6)
        

                if 'below average' in loot_rating:
                    prefix = 'Damaged '
                    name = prefix + name
                    desc = 'A mistreated and abused %s that has been to hell at back judging by it\'s condition.' % self.key
                elif 'fair' in loot_rating:
                    prefix = 'Used'
                    name = prefix + name
                    desc = 'A very used but generally taken care of %s.  While there is some damage it would be easily repairable.' % self.key
                elif 'good' in loot_rating:
                    prefix = 'New'
                    name = prefix + name
                    desc = 'This %s is in quite good shape, whoever it\'s previous owner was took very good care of it.' % self.key
                elif 'excellent' in loot_rating:
                    prefix = random.choice(['Amazing', 'Excellent', 'Spectacular'])
                    name = prefix + name
                    desc = 'It\'s as if this %s has never been fired, let alone seen any sort of heavy use.  It is in exquisite condition.' % self.key
            
                item = create_object("game.gamesrc.objects.world.item.Item", key=name, location=self)
                item.desc = desc
                a = item.db.attributes
                a['damage_dice'] = dd
                a['weapon_type'] = type
                a['item_slot'] = 'weapon'
                a['lootable'] = True
                a['equipable'] = True
                item.db.type = c
                item.db.attributes = a
                print "gun creation complete"
            elif 'scavenging' in c:
                print "begin scavenging"
                rn = random.random()
                first_pass_choices = {}
                second_pass_choices = []
                for i in self.db.scavenging_items:
                    if self.db.scavenging_items[i] >= rn:
                        first_pass_choices['%s' % i] = self.db.scavenging_items[i]
                print first_pass_choices 
                rn = random.random()        
                for i in first_pass_choices:
                    if first_pass_choices[i] >= rn:
                       second_pass_choices.append(i)
                print second_pass_choices
                if len(second_pass_choices) == 0:
                    continue
                itemname = random.choice(second_pass_choices)
                item = create_object("game.gamesrc.objects.world.item.Item", key=itemname, location=self)
                a = item.db.attributes
                item.db.type = c
                a['equipable'] = False
                a['consumable'] = True
                a['lootable'] = True
                item.db.attributes = a
                item.generate_attributes()
                print "scavenging end"
            #elif 'melee' in c:
            #    pass
            print "appending"
            loot_set.append(item)
        return loot_set


class MobFactory(Object):
    """
    Main Mob creation class
    """

    def at_object_creation(self):
        self.db.mob_set = []
        self.db.zone_type = None
        self.db.mob_names = ['Irradiated Rat', 'Survivor Scavenger', 'Infected Survivor', 'Shambling Corpse', 'Irradiated Dog', 'Reanimated Corpse', 'Crazed Looter']
        self.db.difficulty = 'average'
        self.db.level_range = (1, 7)
        self.db.item_factory = create_object(ItemFactory, key='%s_loot_factory' % self.id)
        

    def create_mob_set(self, number_of_mobs):
        self.db.mob_set = []
        for x in range(0, number_of_mobs):
            mob_name = random.choice(self.db.mob_names)
            mob_obj = create_object("game.gamesrc.objects.world.npc.Npc", key=mob_name, location=self)
            a = mob_obj.db.attributes
            a['level'] = random.randrange(self.db.level_range[0], self.db.level_range[1])
            mob_obj.db.attributes = a
            mob_obj.db.difficulty_rating = self.db.difficulty
            mob_obj.generate_attributes()
            self.db.mob_set.append(mob_obj)
            rn = random.random()
            if rn >= .20:
                self.create_mob_loot(mob_obj)
        return self.db.mob_set

    def create_mob_loot(self, m):
        print "beginning create_mob_loot"
        itemf = self.db.item_factory
        rn = random.randrange(0,4)
        ls = itemf.create_lootset(rn, loot_rating='below average')
        for i in ls:
            i.move_to(m, quiet=True)
        print "done with mob_loot"
