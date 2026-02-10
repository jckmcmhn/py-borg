import uuid
from itertools import combinations_with_replacement
from classes import roll_dice
import logging

name_to_flavour = {
    "fireball": "Palms open the southern gate",
    "lightingbolt": "Nine violet signs unknot the storm"
}

name_to_config = {
    "fireball": {
        "dice": "1d8",
        "scroll_code": 1,
        "type": "offensive",
    },
    "lightningbolt": {
        "dice": "1d6",
        "scroll_code": 6,
        "type": "offensive"
    },
    "death": {
        "dice": "4d10",
        "scroll_code": 10,
        "type": "offensive"
    },
    "grace": {
        "dice": "1d10",
        "scroll_code": 11,
        "type": "healing"
    },
    "aegis": {
        "dice": "2d6",
        "scroll_code": 14,
        "type": "healing"
    },
}

class Equipment:
    def heal(self,target, multiplier):
        print("Roll for healing")
        healing = roll_dice(self.dice, self.settings["manual_dice"] in ["always"])
        #damage += self.settings["mod_damage"] #TODO: decide if the mod should apply here
        healing = multiplier * healing
        print(f"Applying {healing} scroll damage to {target.name}")
        target.apply_healing(healing)

class Scroll(Equipment):

    def list_actions(self, allies, enemies, caster):
        if self.scroll_code in [1,6]: # Fireball Lightning
            if self.settings["allow_attack_allies"]:
                targets = allies + enemies
            else:
                targets = enemies
            target_combinations = list(combinations_with_replacement(targets,2))
            action_tuples = [ (tc, self) for tc in target_combinations]
        elif self.scroll_code == 10:
            logging.debug(f"{caster.name} is casting DEATH!")
            all = allies + enemies + [caster] # TODO: The rules say "All creatures within 30 feet" not all creatures
            action_tuples = [ (all, self) ]
            logging.debug(action_tuples)
        elif self.scroll_code in [11, 14]:
            if self.settings["allow_attack_allies"]:
                targets = allies + enemies + [caster]
            else:
                targets = allies + [caster]
            if self.scroll_code == 11:
                n = 2
            else:
                n = 1
            target_combinations = list(combinations_with_replacement(targets,n))
            action_tuples = [ (tc, self) for tc in target_combinations]
            logging.debug(action_tuples)
        
        return action_tuples

    def inflict_standard_damage(self,target, multiplier):
        print("Roll for spell damage")
        damage = roll_dice(self.dice, self.settings["manual_dice"] in ["always"])
        damage += self.settings["mod_damage"]
        damage = multiplier * damage
        print(f"Inflicting {damage} scroll damage to {target.name}")
        target.take_standard_damage(damage)

    def __init__(self, name, flavour, settings):
        self.settings = settings
        self.name = name
        self.flavour = flavour
        self.id = uuid.uuid4()
        name = name.lower().replace(" ","").replace("_","")

        config = name_to_config[name]
        self.type = config["type"]
        self.scroll_code = config["scroll_code"]
        self.dice = config["dice"]
        if name not in name_to_config.keys():
            raise ValueError(f"Invalid Scroll name {self.name}")

        if name in ["fireball", "lightningbolt", "death"]:
            self.apply_scroll_effect = self.inflict_standard_damage
        elif name == "grace":
            self.apply_scroll_effect = self.heal


class General(Equipment):

    def list_actions(self, allies, enemies, caster):
        targets = allies + enemies
        if self.settings["allow_attack_allies"]:
            targets = allies + enemies + [caster]
        else:
            targets = allies + [caster]
        action_tuples = [ (tc, self) for tc in targets]
        logging.debug(action_tuples)
        return action_tuples


    def __init__(self, name, dice, settings):
        self.settings = settings
        self.name = name
        self.id = uuid.uuid4()
        self.name = name.lower().replace("_"," ")
        #self.type = "healing"
        self.dice = dice
        self.count = 4 #TODO: Make this configurable

    def use(self, target):
        print(f"Applying {self.name} to {target.name}")
        multiplier = 1
        self.heal(target, multiplier)