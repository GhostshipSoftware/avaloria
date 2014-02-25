#HEADER
from src.utils import create, search
from game.gamesrc.objects.world.room import Zone

#CODE (Downtown STL)
zone = create.create_object(Zone, key="marshlands")
zone.aliases = ['zone_runner']
zone.db.zone_name = "The Marshlands"
zone.set_zone_manager()
