import random
from ev import Room, Object, create_object
from src.utils import search

class Zone(Object):
    """
    Main Zone class
    """

    def at_object_creation(self):
        self.db.rooms = search.objects("%s_room" % self.key)
        self.db.mob_map = {}
        self.db.player_map = {}
        self.db.quest_items = []
        self.db.zone_map = {}
        self.db.mob_factory = create_object("game.gamesrc.objects.world.factories.MobFactory", key='%s MobFactory' % self.key)
        self.aliases = [ 'zone_manager']

    def figure_mob_levels(self):
        mf = self.db.mob_factory
        self.db.rooms = search.objects('%s_room' % self.key)
        self.db.mobs = search.objects("%s_mobs" % mf.id)
        for room in self.db.rooms:
            mob_set = []
            print "checking %s" % room.name
            mobs = room.db.mobs
            print mobs

            for mob in room.db.mobs:
                if mob.db.corpse:
                    continue
                self.db.mob_map['%s' % mob.dbref ] = room

            if len(room.db.mobs) < 2:
                #create mobs
                rn = random.randrange(0,10)
                mob_set = mf.create_mob_set(rn)
                for mob in mob_set:
                    mob.move_to(room, quiet=True)
                    mobs.append(mob)
            else:
                pass
                room.db.mobs +=  mob_set

            
    def set_zone_manager(self):
        rooms = self.db.rooms
        zone_map = self.db.zone_map
        for room in rooms:
            zone_map['%s' % room.dbref] = room
            room.db.manager = self
        self.db.zone_map = zone_map
            
        
class WorldRoom(Room):
    """
    Main Room Class
    """

    def at_object_creation(self):
        
        self.db.tiles = {}
        self.db.attributes = { 'danger_level': .05, 'scouted': False, }
        self.db.decor_objects = {}
        self.db.mobs = []
        self.db.zone = None

    def at_object_receive(self, moved_obj, source_location):
        if hasattr(self, 'manager'):
            manager = self.db.manager
            if manager is None:
                return
            if moved_obj.has_player:
                player_map = manager.db.player_map
                player_map['%s' % moved_obj.name] = self
                manager.db.player_map = player_map
                self.db.manager = manager
            else:
                return
        self.post_object_receive(caller=moved_obj)
        
    def post_object_receive(self, caller):
        pass
       
    def at_object_leave(self, moved_obj, target_location):
        if hasattr(self, 'manager'):
            manager = self.db.manager
            if moved_obj.player:
                player_map = manager.db.player_map
                try:
                    del player_map[moved_obj.name]
                except KeyError:
                    pass
                manager.db.player_map = player_map
                self.db.manager = manager
 
