
#HEADER

from ev import create_object, search_object
from game.gamesrc.objects.world.room import Zone

#CODE (Message Caller)
caller.msg("Starting on zone creation: Marshlands")
zone = create_object(Zone, key="marshlands")
zone.aliases = ['zone_runner']
zone.db.zone_name = "The Marshlands"
zone.db.mob_factory.db.zone_type = 'marshlands'
zone.db.mob_factory.db.mob_names = [ 'Adult Grasswhip', 'Large Bearcat', 'Slythain Hunter', 'Slythain Juvenile', 'Young Grasswhip', 'Bearcat cub', 'Bearcat Matriarch']
zone.set_zone_manager()
