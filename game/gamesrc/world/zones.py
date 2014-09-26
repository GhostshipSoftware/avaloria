
#HEADER

from ev import create_object, search_object
from game.gamesrc.objects.world.room import Zone

#CODE (Message Caller)
caller.msg("Starting on zone creation")
zone = create_object(Zone, key="marshlands")
zone.aliases = ['zone_runner']
zone.db.zone_name = "The Marshlands"
zone.set_zone_manager()
