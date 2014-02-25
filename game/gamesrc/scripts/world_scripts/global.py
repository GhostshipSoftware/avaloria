from ev import Script
from src.utils import search

class MobRunner(Script):
    """
    Controls the firing of the update function on the mob objects in the entire world.
    """
    def at_script_creation(self):
        self.key = 'mob_runner'
        self.interval = 15
        self.persistent = True
        self.desc = 'controls the subscription list of mobs'
        self.db.mobs = []

    def at_script_start(self):
        self.ndb.mobs = [search.objects(dbref) for dbref in self.db.mobs]
    
    def at_repeat(self):
        self.ndb.mobs = search.objects('mob_runner')
        #print "MobRunner =>  update() [%s mobs in run]" % len(self.ndb.mobs)
        [mob.tick() for mob in self.ndb.mobs if mob.db.should_update and mob is not None]

    def at_stop(self):
        self.db.mobs = [mob.dbref for mob in self.ndb.mobs]

class CharacterRunner(Script):
    """
    Controls the firing of the update function on the character objects subscribed
    """
    def at_script_creation(self):
        self.key = 'character_runner'
        self.interval = 5
        self.persistent = True
        self.desc = 'controls the subscription list of charatcers with players attached'
        self.db.subscribers = []

    def at_script_start(self):
        self.ndb.subscribers = [search.objects(dbref) for dbref in self.db.subscribers]
       
    def at_repeat(self):
        self.ndb.subscribers = search.objects('character_runner')
        #print "CharRunner => tick() [%s chars in run]" % len(self.ndb.subscribers)
        [c.tick() for c in self.ndb.subscribers if c.has_player]

    def at_stop(self):
        self.db.subscribers = [c.dbref for c in self.ndb.subscribers]

class ZoneRunner(Script):
    """
    Controls the firing of zone update methods for zones subscribed
    """
    def at_script_creation(self):
        self.key = 'zone_runner'
        self.interval = 60
        self.persistent = True
        self.desc = "controls the subscription list of zones"
        self.db.subscribers = []
        self.db.corpses = []
    
    def at_script_start(self):
        self.ndb.subscribers = [search.objects(dbref) for dbref in self.db.subscribers]
        self.ndb.corpses = [search.objects(dbref) for dbref in self.db.corpses]
        
    def at_repeat(self):
        self.ndb.subscribers = search.objects('zone_manager')
        self.ndb.corpses = search.objects('corpse')
        #print "ZoneRunner => tick() [ %s zones in run ]" % len(self.db.subscribers)
        print "mob_level()"
        [z.figure_mob_levels() for z in self.ndb.subscribers]
        print "corpse delete"
        [c.delete() for c in self.ndb.corpses if c.db.destroy_me is True]

    def at_stop(self):
        self.db.subscribers = [z.dbref for z in self.ndb.subscribers]

