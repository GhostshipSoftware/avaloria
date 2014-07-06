
tut_speak = create.create_object(Quest, key="Speak And Be Heard", location=storage)
tut_speak.short_description = "Speak in OOC chat."
tut_speak.aliases = ['tutorial quests']
tut_speak.set_description('%squests/speak_and_be_heard.txt' % copy_dir)
tut_speak.db.gold_reward = 100
tut_speak.db.exp_reward = 100
objective = {'objective_name': 'Use the ooc command to speak in the global public channel', 'counter': 0, 'threshold': 3, 'completed': False, 'type': 'use_public'}
tut_speak.add_objective(objective)

tut_skills = create.create_object(Quest, key="Learning New Skills", location=storage)
tut_skills.short_description = "Learn a new Skill."
tut_skills.aliases = ['tutorial quests']
tut_skills.set_description('%squests/learn_a_new_skill.txt' % copy_dir)
tut_skills.db.gold_reward = 115
tut_skills.db.exp_reward = 100
objective = {'objective_name': 'Use a training book to learn a new skill.', 'counter': 0, 'threshold': 1, 'completed': False, 'type': 'use_use training manual'}
tut_skills.add_objective(objective)

tut_lspells = create.create_object(Quest, key="Learning Spells", location=storage)
tut_lspells.short_description = "Learn a new Spell."
tut_lspells.aliases = ["tutorial quests"]
tut_lspells.set_description('%squests/learn_a_spell.txt' % copy_dir)
tut_lspells.db.gold_reward = 100
tut_lspells.db.exp_reward = 125
objective = {'objective_name': 'Use a spell tome to learn a spell.', 'counter': 0, 'threshold': 1, 'completed': False, 'type': 'use_use spell tome'}
tut_lspells.add_objective(objective)

tut_iskills = create.create_object(Quest, key="Increasing Skills", location=storage)
tut_iskills.short_description = "Use the 'skills' command to increaase a skill"
tut_iskills.aliases = ['tutorial quests']
tut_iskills.set_description("%squests/increasing_skills.txt" % copy_dir)
tut_iskills.db.gold_reward = 100
tut_iskills.db.exp_reward = 100
objective = {'objective_name': 'Use the \'skills\' command to increase a skill', 'counter': 0, 'threshold': 1, 'completed': False, 'type': 'use_skills'}
tut_iskills.add_objective(objective)

tut_battle = create.create_object(Quest, key="Battle On!", location=storage)
tut_battle.short_description = "Kill the Battle Dummy!"
tut_battle.aliases = ['tutorial quests']
tut_battle.set_description("%squests/battle_on.txt" % copy_dir)
tut_battle.db.gold_reward = 100
tut_battle.db.exp_reward = 100
objective = {'objective_name': 'Kill the Battle Dummy', 'counter': 0, 'threshold': 1, 'completed': False, 'type': 'kill_battle dummy'}
tut_battle.add_objective(objective)
