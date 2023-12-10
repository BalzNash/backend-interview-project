import requests
import json
import urllib3
from copy import deepcopy
from flask import Flask
from jsonschema import validate

def cap_stat(stat: float, talent_type: str) -> float:
    """
    forces all stats to be at least 0, and defense stats at most 100
    
    parameters:
    stat (float): stat value
    talent_type (str): identifies an "attack" or "defence" talent

    returns:
    float: final stat value
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
    talent_type (str): identifies an "attack" or "defence" talent

    """
    if effect_values["type"] == 'flat':
        entity_stats[stat_type] = cap_stat(entity_stats[stat_type] + effect_values["value"], talent_type)
    elif effect_values["type"] == 'percent':
        entity_stats[stat_type] = cap_stat(round(entity_stats[stat_type] + entity_stats[stat_type] * effect_values["value"]), talent_type)
    else:
        raise Exception("effect type not recognized")


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
    modifications that alter all armours and/or all stat types (physical, fire, lightning) are considered a single effect.

    parameters:
    entity (dict): entity on which the talent is applied
    talent (dict): collection of all the effects of a talent
    """
    if "attack" in talent:
        entity_attack_stats = entity["weapon"]["attack"]
        for effect in talent["attack"]["effects"]:
            apply_effect(effect, entity_attack_stats, talent_type="attack")
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
                    apply_effect(effect, entity_defence_stats, talent_type="defence")


def compute_mitigation(attack_stats: dict, armour_stats: dict) -> dict:
    """
    computes the mitigation done by an armour on each attack stats

    parameters:
    attack_stats (dict): collection of all attack stats
    armour_stats (dict): collection of all armour stats for a specific armour

    returns:
    dict: attack stats after mitigation

    """
    return {stat_type: cap_stat(attack_stats[stat_type] 
                              - attack_stats[stat_type] * armour_stats[stat_type] / 100, "attack")
                                for stat_type in attack_stats}


def compute_effective_damage(attack_stats: dict, chest_defence: dict, head_defence: dict) -> dict:
    """
    applies chest armour mitigation first, then head mitigation, on the attack stats

    parameters:
    attack_stats (dict): collection of all attack stats
    chest_defence (dict): collection of all chest armour stats
    head_defence (dict): collection of all head armour stats

    returns:
    dict: effective damage
    """
    demage_after_chest_mitigation = compute_mitigation(attack_stats, chest_defence)
    return compute_mitigation(demage_after_chest_mitigation, head_defence)


def round_effective_damage(effective_damage: dict) -> dict:
    """rounds the effective damage"""
    for type, value in effective_damage.items():
        effective_damage[type] = round(value)


app = Flask(__name__)

@app.route('/')
def index():
    return "go to /run to execute"

@app.route('/run')
def data():
    URL_GET = "https://hiring-test-dxxsnwdabq-oa.a.run.app/duel"
    URL_POST = "https://hiring-test-dxxsnwdabq-oa.a.run.app/processDuel"
    duel_data = requests.get(URL_GET).json()

    #data validation
    with open('./data_schema.json') as json_file:
        data_schema = json.load(json_file)
    validate(instance=duel_data, schema=data_schema)

    # deepcopy required because talents are applied in place to the entities
    # but we need to send the original entities to the server
    enemy = duel_data["data"]["duel"]["enemy"]
    enemy_copy = deepcopy(enemy)
    myself = duel_data["data"]["duel"]["myself"]
    myself_copy = deepcopy(myself)
    my_attack_stats = myself["weapon"]["attack"]

    raw_damage = sum(my_attack_stats.values())

    #apply talents
    with open('./talents.json') as json_file:
        talents = json.load(json_file)

    for talent in myself["talents"]:
        apply_talent(myself, talents[talent])
    for talent in enemy["talents"]:
        apply_talent(enemy, talents[talent])
    
    #effective damage computation
    chest_defence = enemy["chestArmour"]["defence"]
    head_defence = enemy["headArmour"]["defence"]
    effective_damage = compute_effective_damage(my_attack_stats, chest_defence, head_defence)
    round_effective_damage(effective_damage)

    out_data = {
        "data": {
        "enemy": enemy_copy,
        "myself": myself_copy,
        "rawDamage": raw_damage,
        "effectiveDamage": effective_damage
        }
    }

    response = urllib3.request("POST", URL_POST,
                                headers={'Content-Type': 'application/json'},
                                body=json.dumps(out_data, sort_keys=True))
    return (json.dumps(json.loads(response.data), indent=4))

if __name__ == "__main__":
    app.run(debug=True)