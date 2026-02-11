import uuid
from itertools import combinations_with_replacement
from classes import roll_dice
import logging

crit_multiplier = 2

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
        print("Roll for equipment healing")
        healing = roll_dice(self.dice, self.settings["manual_dice"] in ["always"])
        healing = multiplier * healing #TODO: decide if the mod should apply here
        print(f"Applying {healing} scroll damage to {target.name}")
        target.apply_healing(healing)

    def do_damage(self, target, multiplier):
        print("Roll for equipment damage")
        damage = roll_dice(self.dice, self.settings["manual_dice"] in ["always"])
        damage += self.settings["mod_damage"]
        damage = multiplier * damage
        print(f"Inflicting {damage} scroll damage to {target.name}")
        target.apply_damage(damage)

class Scroll(Equipment):
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
            self.apply_scroll_effect = self.do_damage
        elif name == "grace":
            self.apply_scroll_effect = self.heal

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

    def use(self, user, targets):
        if user.dizzy:
            logging.warning("Shouldn't try and use a scroll when dizzy")
            user.apply_damage(4 + self.settings["mod_damage"]) #TODO: This shouldn't be as hardcoded
            return
        print("Rolling to hit for a scroll") #TODO: fix this
        scroll_roll = roll_dice("1d20", self.settings["manual_dice"] in ["always", "pc_only"])
        critical = False
        multiplier = 1
        if scroll_roll == 20:
            critical = True
            print("CRITICAL")
            multiplier = crit_multiplier
        if scroll_roll == 1:
            print("FUMBLE") # TODO: Figure out what to do here
        # fumble rolls go here
        scroll_roll += user.abilities["presence"] + self.settings["to_hit"]
        dr = 12
        logging.debug(f"DR is {dr}, roll result is {scroll_roll}, critical is {critical}")
        if critical or scroll_roll >= dr:
            for target in targets:
                if target.alive is False:
                    logging.warning("Attacking someone who is already dead") #TODO: Fix this
                self.apply_scroll_effect(target, multiplier)
            #target_alive = target.apply_damage(multiplier * damage)
            user.powers -= 1
        elif scroll_roll < dr:
            print(f"{self.name} failed the scroll roll and is now dizzy. Roll a d2 for HP loss")
            damage = roll_dice("1d2", self.settings["manual_dice"] in ["always", "pc_only"])
            user.apply_damage(damage + self.settings["mod_damage"])
            user.dizzy = True #TODO: How to make this only apply "for the next hour"


class General(Equipment):
    def __init__(self, name, dice, settings):
        self.settings = settings
        self.name = name
        self.id = uuid.uuid4()
        self.name = name.lower().replace("_"," ")
        #self.type = "healing"
        self.dice = dice
        self.count = 4 #TODO: Make this configurable

    def list_actions(self, allies, enemies, caster):
        targets = allies + enemies
        if self.settings["allow_attack_allies"]:
            targets = allies + enemies + [caster]
        else:
            targets = allies + [caster]
        action_tuples = [ (tc, self) for tc in targets]
        logging.debug(action_tuples)
        return action_tuples

    def use(self, target):
        print(f"Applying {self.name} to {target.name}")
        multiplier = 1
        self.heal(target, multiplier)

class Weapon(Equipment):
    def __init__(self, settings, config = {}):
        self.settings = settings
        self.name = config.get("name","Unarmed")
        self.type = config.get("type","melee")
        self.dice = config.get("damage","1d2")
        self.dr = config.get("dr",12)
        self.category = config.get("category","unarmed")
        self.rank = config.get("rank",False)
        self.id = uuid.uuid4()        

    def __str__(self):
        return "It's a %s called %s it deals %s" % (self.category, self.name, self.damage)