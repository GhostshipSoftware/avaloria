
#HEADER
from ev import create_object, search_object
from game.gamesrc.objects.world.quests import Quest

#CODE
from ev import create_object, search_object
from game.gamesrc.objects.world.quests import Quest
storage = search_object('Limbo')[0]
copy_dir = 'gamesrc/copy/'

tut_speak = create_object(Quest, key="Speak And Be Heard", location=storage)
tut_speak.tags.add(tut_speak.key)
tut_speak.short_description = "Speak in OOC chat."
tut_speak.aliases = ['tutorial quests']
tut_speak.set_description('%squests/speak_and_be_heard.txt' % copy_dir)
tut_speak.db.gold_reward = 100
tut_speak.db.exp_reward = 100
objective = {'objective_name': 'Use the ooc command to speak in the global public channel', 'counter': 0, 'threshold': 3, 'completed': False, 'type': 'use_public'}
tut_speak.add_objective(objective)
