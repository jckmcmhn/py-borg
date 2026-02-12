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
        "n": "1d2"
    },
    "lightningbolt": {
        "dice": "1d6",
        "scroll_code": 6,
        "type": "offensive",
        "n": "1d2"
    },
    "death": {
        "dice": "4d10",
        "scroll_code": 10,
        "type": "offensive"
    },
    "grace": {
        "dice": "1d10",
        "scroll_code": 11,
        "type": "healing",
        "n": "1d2"
    },
    "aegis": {
        "dice": "2d6",
        "scroll_code": 14,
        "type": "healing",
        "n": "1d1"
    },
}

class Equipment:
    def heal(self,target, multiplier):
        print(f"Roll for {self.name} healing")
        healing = roll_dice(self.dice, self.settings["manual_dice"] in ["always", "pc_only"])
        healing = multiplier * healing #TODO: decide if the mod should apply here
        print(f"Applying {healing} healing to {target.name}")
        target.apply_healing(healing)

    def do_damage(self, target, multiplier):
        print(f"Roll for {self.name} damage")
        damage = roll_dice(self.dice, self.settings["manual_dice"] in ["always", "pc_only"])
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
        n = config.get("n", "1d10000000") #TODO: This should just be infinite
        self.max_n = int(n.split("d")[1])
        self.n = n
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
            #target_combinations = []
            #for i in range(int(self.n)):
            #    i_combinations = list(combinations_with_replacement(targets,i + 1))
            #    target_combinations += i_combinations
            target_combinations = list(combinations_with_replacement(targets, self.max_n))
            action_tuples = [ (tc, self) for tc in target_combinations]
        elif self.scroll_code == 10:
            all = allies + enemies + [caster] # TODO: The rules say "All creatures within 30 feet" not all creatures
            action_tuples = [ (all, self) ]
        elif self.scroll_code in [11, 14]:
            if self.settings["allow_attack_allies"]:
                targets = allies + enemies + [caster]
            else:
                targets = allies + [caster]
            #target_combinations = []
            #for i in range(int(self.n)):
            #    i_combinations = list(combinations_with_replacement(targets,i + 1))
            #    target_combinations += i_combinations
            target_combinations = list(combinations_with_replacement(targets, self.max_n))
            action_tuples = [ (tc, self) for tc in target_combinations]
        #logging.debug(f"Possible scroll actions for {caster.name}: {action_tuples}")
        return action_tuples

    def use(self, user, targets):
        if user.dizzy:
            logging.warning("Shouldn't try and use a scroll when dizzy")
            user.apply_damage(4 + self.settings["mod_damage"]) #TODO: This shouldn't be as hardcoded
            return
        print(f"Rolling to hit for a scroll ({self.name})")
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
            print(f"Rolling to see how many targets the {self.name} scroll will have")
            n_targets = roll_dice(self.n, self.settings["manual_dice"] in ["always", "pc_only"])
            if n_targets < len(targets):
                print(f"The number of targets rolled for this scroll was less than the maximum. Only the first {n_targets} will be carried out")
            elif n_targets == len(targets):
                print(f"Rolled {n_targets}, the max number of targets for this scroll")
            for target in targets[:n_targets]:
                if target.alive is False:
                    logging.warning("Attacking someone who is already dead") #TODO: Fix this
                self.apply_scroll_effect(target, multiplier)
            #target_alive = target.apply_damage(multiplier * damage)
            user.powers -= 1
        elif scroll_roll < dr:
            print(f"{user.name} failed the scroll roll and is now dizzy. Roll a d2 for HP loss")
            damage = roll_dice("1d2", self.settings["manual_dice"] in ["always", "pc_only"])
            user.apply_damage(damage + self.settings["mod_damage"])
            user.dizzy = True #TODO: How to make this only apply "for the next hour"

    def __str__(self):
        return f"A scroll object called {self.name} ({self.flavour})"

class General(Equipment):
    def __init__(self, name, dice, settings):
        self.settings = settings
        self.name = name
        self.id = uuid.uuid4()
        self.name = name.lower().replace("_"," ")
        self.dice = dice
        self.count = 4 #TODO: Make this configurable

    def list_actions(self, allies, enemies, user):
        targets = allies + enemies
        if self.settings["allow_attack_allies"]:
            targets = allies + enemies + [user]
        else:
            targets = allies + [user]
        action_tuples = [ (tc, self) for tc in targets]
        #logging.debug(f"Possible equipment actions for {user.name}: {action_tuples}")
        return action_tuples

    def use(self, target):
        print(f"Applying {self.name} to {target.name}")
        multiplier = 1
        self.heal(target, multiplier)

class Weapon(Equipment): #TODO: could weapon use things that are defined in the equipment class
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
    
class Armour(Weapon):
    def __init__(self, config, wearer, settings):
        self.settings = settings
        self.type = config["type"]
        self.dice = config["dice"]
        if self.dice == "1d2":
            self.tier = 2
        if self.dice == "1d4":
            self.tier = 3
            if wearer.is_pc:
                wearer.abilities["agility"] += 2
                wearer.defence += 2
        if self.dice == "1d6":
            self.tier = 4
            if wearer.is_pc:
                wearer.abilities["agility"] += 4
                wearer.defence += 2
        else:
            self.tier = 1
        #TODO: What about shields. They would be a type of Reaction
        #TODO: Would be good to log if armour has been damaged

    def reduce_tier(self, wearer, tier_reduction):
        # TODO: introduce tiers to this properly
        # Per the rules, if armour is damanged, the penalties to abilities are not modified. Thankfully...
        print(f"Reducing {wearer.name}'s armour by a tier of {tier_reduction}")
        if self.dice == "1d2":
            print("Armour has been destroyed")
            wearer.armour = None #TODO: Have an unarmoured state
        elif self.dice == "1d4":
            self.dice = "1d2"
        elif self.dice == "1d6":
            self.dice = "1d4"

    def __str__(self):
        return "It's a %s armour, it provides %s damage reduction" % (self.type, self.dice)
    
    #TODO: Should there be an option to remove armour?