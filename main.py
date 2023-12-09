import requests
import json
import urllib3
from copy import deepcopy

def cap_stat(stat: int, talent_type: str) -> int:
    """
    forces all stats to be at least 0, and defense stats at most 100
    
    parameters:
    stat (int): stat value
    talent_type (str): "attack" or "defense" talent

    returns:
    int: final stat value
    """
    if stat > 100 and talent_type == "defence":
        return 100
    elif stat < 0:
        return 0
    else:
        return stat


def edit_stat(stat_type: str, entity_stats: dict, effect_values: dict, talent_type: str) -> None:
    """
    edits a single stat, with either a flat or a percent buff / debuff

    parameters:
    stat_type (str): type of stat e.g. 'physical', 'fire', etc.
    entity_stats (dict): collection of all stat types of an entity with their stat values
    effect_values (dict): collection of the type and the value of an effect
    talent_type (str): "attack" or "defence" talent

    """
    if effect_values["type"] == 'flat':
        entity_stats[stat_type] = cap_stat(entity_stats[stat_type] + effect_values["value"], talent_type)
    elif effect_values["type"] == 'percent':
        entity_stats[stat_type] = cap_stat(round(entity_stats[stat_type] + entity_stats[stat_type] * effect_values["value"]), talent_type)
    else:
        pass


def apply_effect(effect: dict, entity_stats: dict, talent_type: str) -> None:
    """
    applies an effect to the stats of an entity.
    to apply the effect, it needs to edit one or more stats.

    parameters:
    effect (dict): collection of the stat modifications done by a single effect
    entity_stats (dict): collection of the entity's stats that can be modified by an effect
    talent_type (str): identifies an "attack" or "defence" talent
    """
    if "all" in  effect:
        effect_values = effect["all"]
        for stat_type in entity_stats:
            edit_stat(stat_type, entity_stats, effect_values, talent_type)
    else:
        stat_type = list(effect.keys())[0]
        effect_values = effect[stat_type]
        edit_stat(stat_type, entity_stats, effect_values, talent_type)


def apply_talent(entity: dict, talent: dict) -> None:
    """
    applies a talent to an entity by traversing both objects.
    to apply the talent, it needs to apply one or more effects.
    modifications that alter all armours or all stat types (physical, fire, lightning) are considered a single effect.

    parameters:
    entity (dict): entity on which the talent is applied
    talent (dict): collection of all the effects of a talent
    """
    if "attack" in talent:
        entity_attack_stats = entity["weapon"]["attack"]
        for effect in talent["attack"]:
            apply_effect(effect, entity_attack_stats, "attack")
    if "defence" in talent:
        if talent["defence"]["armour-type"] == "all":
            for armour_type in ["headArmour", "chestArmour"]:
                for effect in talent["defence"]["effects"]:
                    entity_defence_stats = entity[armour_type]["defence"]
                    apply_effect(effect, entity_defence_stats, "defence")
        else:
            armour_type = talent["defence"]["armour-type"]
            for effect in talent["defence"]["effects"]:
                    entity_defence_stats = entity[armour_type]["defence"]
                    apply_effect(effect, entity_defence_stats, "defence")


if __name__ == "__main__":

    URL_GET = "https://hiring-test-dxxsnwdabq-oa.a.run.app/duel"
    URL_POST = "https://hiring-test-dxxsnwdabq-oa.a.run.app/processDuel"
    data = requests.get(URL_GET).json()
    with open('talents.json') as json_file:
        talents = json.load(json_file)

    #with open('data.json') as json_file:
    #    data = json.load(json_file)

    # deepcopy required because talents are applied in place to the entities
    # and we need to send the original entities to the server 
    enemy = data["data"]["duel"]["enemy"]
    enemy_copy = deepcopy(enemy)
    myself = data["data"]["duel"]["myself"]
    myself_copy = deepcopy(myself)
    my_weapon_stats = myself["weapon"]["attack"]

    raw_damage = sum(my_weapon_stats.values())

    for talent in myself["talents"]:
        apply_talent(myself, talents[talent])
    for talent in enemy["talents"]:
        apply_talent(enemy, talents[talent])
    
    chest_defence = enemy["chestArmour"]["defence"]
    head_defence = enemy["headArmour"]["defence"]
    
    demage_after_chest_mitigation = {stat_type: my_weapon_stats[stat_type] - my_weapon_stats[stat_type] * chest_defence[stat_type] / 100 for stat_type in my_weapon_stats}
    effective_damage = {stat_type: round(demage_after_chest_mitigation[stat_type] - demage_after_chest_mitigation[stat_type] * head_defence[stat_type] / 100) for stat_type in demage_after_chest_mitigation}

    out_data = {
        "data": {
        "enemy": enemy_copy,
        "myself": myself_copy,
        "rawDamage": raw_damage,
        "effectiveDamage": effective_damage
        }
    }

    #print(json.dumps(out_data, indent= 4))
    response = urllib3.request("POST", URL_POST,
                                headers={'Content-Type': 'application/json'},
                                body=json.dumps(out_data, sort_keys=True))
    print(json.dumps(json.loads(response.data), indent=4))

