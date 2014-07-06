storage = objects.search("Limbo")[0]
tut_enemynpc = create.create_object("game.gamesrc.objects.world.npc.EnemyNpc", key="Battle Dummy", location=tutorial3)
desc = "What seems to be an animated..scarecrow...thing.  \"Mmph...mppphhnnmm\" is the only sounds it seems capable of making.\n"
desc += "In its hand materializes a magically summoned hammer and shield."
tut_enemynpc.db.desc = desc
tut_enemynpc.db.actions = { 'taunt': "Mpphhgmm mph, hpmmhhhgn!", "mock": "Hmmgpf mmpphmmgjf" }
tut_enemynpc.rating = 'hero'
tut_enemynpc.db.attributes['level'] = 1
tut_enemynpc.generate_stats()
tut_enemynpc.generate_rewards()
tut_enemynpc.update_stats()

tutorial1_room = search.objects("tutorial1")[0]
tutorial1_npc = create.create_object("game.gamesrc.objects.world.npc.Npc", key="Kayleigh", location=tutorial1_room)
desc = "This striking woman is clearly far stronger than you and could probably kill you with a mere flick of her finger.\n"
desc += "She is dressed in a black ensemble that hides all of her features except her eyes.  As you look at her face, you\n"
desc += "notice that her eyes are entirely white, though she does not seem to be blind."
tutorial1_npc.desc = desc
tutorial1_npc.name = "{Y!{n %s" % tutorial1_npc.name
tutorial1_npc.db.real_name = "Kayleigh"
tutorial1_npc.db.quests = ['Speak And Be Heard', 'Learning New Skills']
tutorial1_npc.db.merchant = False
tutorial1_npc.db.quest_giver = True
tutorial1_npc.db.trainer = False

tutorial2_room = search.objects("tutorial2")[0]
tutorial2_npc  = create.create_object("game.gamesrc.objects.world.npc.Npc", key="Green Warden", location=tutorial2_room)
desc = "A very old man clad in brownish green robes.  In his right hand he holds an impressive wooden staff, which at\n"
desc += "the end of its length is a carved talon gripping a green orb which pulsates gently.  As you look at the pulsating\n"
desc += "glow, the man quietly says \"So you have come to learn have you?\"."
tutorial2_npc.desc = desc
tutorial2_npc.name = "{Y!{n %s" % tutorial2_npc.name
tutorial2_npc.db.real_name = "Green Warden"
tutorial2_npc.db.quests = ['Learning Spells', 'Increasing Skills']
tutorial2_npc.db.merchant = False
tutorial2_npc.db.quest_giver = True
tutorial2_npc.db.trainer = False

tutorial3_room = search.objects("tutorial3")[0]
tutorial3_npc = create.create_object("game.gamesrc.objects.world.npc.Npc", key="Battlemaster Kenchi", location=tutorial3_room)
desc = "This is a large Earthen man who wears a black hooded mask in the style of an executioner.  He looks like he's\n"
desc += "spent most of his life striving to reach physical perfection.  His body is lined with scars that make it known\n"
desc += "he's seen some stuff...and some things...man."
tutorial3_npc.name = "{Y!{n %s" % tutorial3_npc.name
tutorial3_npc.db.real_name = "Battlemaster Kenchi"
tutorial3_npc.db.quests = ['Battle On!']
tutorial3_npc.db.merchant = False
tutorial3_npc.db.quest_giver = True
tutorial3_npc.db.trainer = False
