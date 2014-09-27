#Avaloria specific locks
def onquest(accessing_obj, accessed_obj, *args, **kwargs):
    character = accessing_obj
    quest = args[0]
    ql = character.db.quest_log
    if character.on_quest(quest):
        return True
    else:
        return False

def completed_quest(accessing_obj, accessed_obj, *args, **kwargs):
    character = accessing_obj
    quest = args[0]
    return character.on_quest(quest, completed=True)

def has_skill(accessing_obj, accessed_obj, *args, **kwargs):
    character = accessing_obj
    skill = args[0]
    return character.has_skill(skill)

def has_spell(accessing_obj, accessed_obj, *args, **kwargs):
    character = accessing_obj
    spell = args[0]
    return character.has_spell(spell)
