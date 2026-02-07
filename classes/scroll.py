import uuid
from itertools import combinations_with_replacement
from classes import roll_dice

name_to_flavour = {
    "fireball": "Palms open the southern gate",
    "lightingbolt": "Nine violet signs unknot the storm"
}

name_to_config = {
    "fireball": {
        "damage": "1d8",
        "scroll_code": 1,
        "type": "offensive",
    },
    "lightningbolt": {
        "damage": "1d6",
        "scroll_code": 2,
        "type": "offensive"
    },
}

class Scroll:



    def list_actions(self,others):
        if self.scroll_code in [1,2]: # Fireball
            #TODO: Need to filter based on ALLOW_ATTACK_ALLIES
            target_combinations = list(combinations_with_replacement(others,2))
            action_tuples = [ (tc, self) for tc in target_combinations]
            return action_tuples

    def inflict_standard_damage(self,target, multiplier):
        print("Roll for spell damage")
        damage = roll_dice(self.damage, self.manual)
        damage = multiplier * 6
        print(f"Inflicting {damage} scroll damage to {target.name}")
        target.take_standard_damage(damage)

    def __init__(self, name, flavour, manual=False):
        self.manual = manual
        self.name = name
        self.flavour = flavour
        self.id = uuid.uuid4()
        name = name.lower().replace(" ","").replace("_","")

        config = name_to_config[name]
        self.type = config["type"]
        self.scroll_code = config["scroll_code"]
        self.damage = config["damage"]
        if name not in name_to_config.keys():
            raise ValueError(f"Invalid Scroll name {self.name}")

        if name in ["fireball", "lightningbolt"]:
            self.inflict_damage = self.inflict_standard_damage