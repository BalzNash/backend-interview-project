import unittest
import json
from app import cap_stat, edit_stat, apply_effect, apply_talent, compute_mitigation, compute_effective_damage, round_effective_damage
from copy import deepcopy

class Test_cap_stat(unittest.TestCase):
    def test_no_actions_attack(self):
        actual = cap_stat(14, "attack")
        expected = 14
        self.assertEqual(actual, expected)

    def test_no_actions_defence(self):
        actual = cap_stat(14, "defence")
        expected = 14
        self.assertEqual(actual, expected)

    def test_cap_max_defence(self):
        actual = cap_stat(120, "defence")
        expected = 100
        self.assertEqual(actual, expected)

    def test_cap_max_attack(self):
        actual = cap_stat(120, "attack")
        expected = 120
        self.assertEqual(actual, expected)

    def test_cap_min_attack(self):
        actual = cap_stat(-20, "attack")
        expected = 0
        self.assertEqual(actual, expected)

    def test_cap_min_defence(self):
        actual = cap_stat(-20, "defence")
        expected = 0
        self.assertEqual(actual, expected)


class Test_edit_stat(unittest.TestCase):
    entity_stats = {
            "physical": 10,
            "lightning": 20,
            "fire": 30
            }
    stat_type = "physical"
    talent_type = "defence"
    def test_flat_buff(self):
        entity_stats_copy = deepcopy(self.entity_stats)
        effect_values = {
            "value": 10,
            "type": "flat"
        }
        edit_stat(self.stat_type, entity_stats_copy, effect_values, self.talent_type)
        expected = {
            "physical": 20,
            "lightning": 20,
            "fire": 30
        }
        self.assertEqual(expected, entity_stats_copy)

    def test_percent_buff(self):
        entity_stats_copy = deepcopy(self.entity_stats)
        effect_values = {
            "value": 0.50,
            "type": "percent"
        }
        edit_stat(self.stat_type, entity_stats_copy, effect_values, self.talent_type)
        expected = {
            "physical": 15,
            "lightning": 20,
            "fire": 30
        }
        self.assertEqual(expected, entity_stats_copy)


class Test_apply_effect(unittest.TestCase):
    entity_stats = {
            "physical": 10,
            "lightning": 20,
            "fire": 30
            }
    talent_type = "attack"
    def test_effect_all_stat_types(self):
        entity_stats_copy = deepcopy(self.entity_stats)
        effect = {
            "all": {
                "type": "percent",
                "value": 0.50
                }
            }
        apply_effect(effect, entity_stats_copy, self.talent_type)
        expected = {
            "physical": 15,
            "lightning": 30,
            "fire": 45  
        }
        self.assertEqual(expected, entity_stats_copy)

    def test_effect_single_stat_type(self):
        entity_stats_copy = deepcopy(self.entity_stats)
        effect = {
            "fire": {
                "type": "percent",
                "value": 0.50
                }
            }
        apply_effect(effect, entity_stats_copy, self.talent_type)
        expected = {
            "physical": 10,
            "lightning": 20,
            "fire": 45  
        }
        self.assertEqual(expected, entity_stats_copy)


class Test_apply_talent(unittest.TestCase):
    with open('./tests_data/example_data.json') as json_file:
        entity = json.load(json_file)["data"]["duel"]["myself"]
    with open('./talents.json') as json_file:
        talents = json.load(json_file)

    def test_attack_talent(self):
        entity_copy = deepcopy(self.entity)
        apply_talent(entity_copy, self.talents["Fire affinity"])
        with open('./tests_data/test_attack_talent.json') as json_file:
            expected = json.load(json_file)
        self.assertEqual(expected, entity_copy)

    def test_defence_talent_all_armours(self):
        entity_copy = deepcopy(self.entity)
        apply_talent(entity_copy, self.talents["God"])
        with open('./tests_data/test_defence_talent_all_armour.json') as json_file:
            expected = json.load(json_file)
        self.assertEqual(expected, entity_copy)

    def test_defence_talent_single_armour(self):
        entity_copy = deepcopy(self.entity)
        apply_talent(entity_copy, self.talents["Massive"])
        with open('./tests_data/test_defence_talent_single_armour.json') as json_file:
            expected = json.load(json_file)
        self.assertEqual(expected, entity_copy)


class Test_compute_mitigation(unittest.TestCase):
    def test_compute_mitigation(self):
        attack_stats = {
            "physical": 100,
            "lightning": 50,
            "fire": 10
        }
        chest_defence = {
            "physical": 75,
            "lightning": 50,
            "fire": 100           
        }
        damage_after_mitigation = compute_mitigation(attack_stats, chest_defence)
        expected = {
            "physical": 25,
            "lightning": 25,
            "fire": 0    
        }
        self.assertEqual(damage_after_mitigation, expected)


class Test_compute_effective_damage(unittest.TestCase):
    def test_compute_effective_damage(self):
        attack_stats = {
            "physical": 100,
            "lightning": 50,
            "fire": 10
        }
        chest_defence = {
            "physical": 75,
            "lightning": 50,
            "fire": 100           
        }
        head_defence = {
            "physical": 50,
            "lightning": 5,
            "fire": 100           
        }
        effective_damage = compute_effective_damage(attack_stats, chest_defence, head_defence)
        expected = {
            "physical": 12.5,
            "lightning": 23.75,
            "fire": 0               
        }
        self.assertEqual(effective_damage, expected)

    
class Test_round_effective_damage(unittest.TestCase):
    def test_round_effective_damage(self):
        effective_damage = {
            "physical": 12.5,
            "lightning": 23.75,
            "fire": 0
        }
        round_effective_damage(effective_damage)
        expected = {
            "physical": 12,
            "lightning": 24,
            "fire": 0
        }
        self.assertEqual(effective_damage, expected)


if __name__ == '__main__':
    unittest.main()