from ev import Object, create_object
import random

class ItemFactory(Object):
    """
    Main Item generator.  generates items based on list seeds.

    This factory pumps out all the loot found on creatures and bosses
    alike in the game world.  Currently in avaloria everything is player made,
    so this is what creates all the components necessary for that.

    TODO:
        Cleanup the mob lootset generation, right now it's locked to t1 
        which is convienent until there is t2 and t3.
    """

    def at_object_creation(self):
        self.db.t1_armor_comp_names = ['Metallic Bits', 'Strips of Leather', 'Chain Scrap', 'Padding Scrap']
        self.db.t1_old_armor_husks = ['Rusted Plate Armor', 'Rusted Chain Armor', 'Rusted Scalemail Armor', 'Dusty Old Robes', 'Used Learther Armor']
        self.db.uncommon_items = [ 'Gently Used Blade' ]

   
    def create_lootset(self, number_of_items, loot_tier='t1'):
        loot_set = []
        print "begin loot set logic"
        if number_of_items == 0:
            return []
        #loot_groups are important.  Each one represents a school of crafting...well roughly anyhow.
        self.check_for_uncommon_drop(loot_set)
        print loot_set
        loot_groups = ['armor']
        lg = 'armor'
        for x in range(0, number_of_items):
            if loot_tier == 't1':
                if lg == 'armor':
                    rn = random.random()
                    print rn
                    if rn < .05:
                        name = random.choice(self.db.t1_old_armor_husks)
                        desc = "This old set of armor while damaged, could probably be repaired."
                    else:
                        print "in comps"
                        name = random.choice(self.db.t1_armor_comp_names)
                        desc = "Components used in the crafting of wonderful sets of armor."
                
                print "out of name gen" 
                item = create_object("game.gamesrc.objects.world.item.Item", key=name, location=self)
                item.desc = desc
                a = item.db.attributes
                a['lootable'] = True
                a['crafting_material'] = True
                a['crafting_group'] = lg
                item.db.type = 'crafting_materials'
                item.db.attributes = a
            loot_set.append(item)
        return loot_set
    
    def check_for_uncommon_drop(self, loot_set):
        rn = random.random()
        if rn < .02:
            print "I should be dropping an uncommon"
            item_name = random.choice(self.db.uncommon_items)
            storage_item = search_object(item_name)[0]
            loot_item = storage_item.copy()
            loot_set.append(loot_item)
        else:
            return
            


class MobFactory(Object):
    """
    Main Mob creation class
    """

    def at_object_creation(self):
        self.db.mob_set = []
        self.db.zone_type = None
        self.db.mob_names = []
        self.db.difficulty = 'average'
        self.db.level_range = (1, 7)
        self.db.item_factory = create_object(ItemFactory, key='%s_loot_factory' % self.id)
        

    def create_mob_set(self, number_of_mobs):
        self.db.mob_set = []
            
        for x in range(0, number_of_mobs):
            mob_name = random.choice(self.db.mob_names)
            mob_obj = create_object("game.gamesrc.objects.world.npc.Npc", key=mob_name, location=self)
            mob_obj.tags.add("%s_mobs" % self.id)
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
        ls = itemf.create_lootset(rn, loot_tier='t1')
        print ls
        for i in ls:
            i.move_to(m, quiet=True)
        print "done with mob_loot"
