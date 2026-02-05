from random import randint, choice
import re
import yaml

MANUAL_DICE_ROLLS = False
ALLOW_ATTACK_ALLIES = True

print("Starting the game")
print(f"MANUAL_DICE_ROLLS is {MANUAL_DICE_ROLLS}\n\n")

def roll_dice(nd):
    # TODO: allow people not to set n
    if MANUAL_DICE_ROLLS:
        result = int(input(f"Roll {nd} and type in the result"))
    else:
        nd = nd.lower()
        if bool(re.search("^[0-9]*d[0-9]*$", nd)):
            split_nd = nd.split("d")
            n = int(split_nd[0])
            d = int(split_nd[1])
        else:
            raise ValueError("Invalid roll description")
        result = 0
        for i in range(0,n):
            roll = randint(1,d)
            result += roll
    return result

class Weapon:
    def __init__(self, config):
        self.name = config["name"]
        self.type = config["type"]
        self.damage = config["damage"]
        self.dr = config.get("dr",12)
        self.category = config["category"]
        self.primary = config.get("primary",False)

    def __str__(self):
        return "It's a %s called %s it deals %s" % (self.category, self.name, self.damage)
    
class Armour:
    def __init__(self, config):
        self.type = config["type"]
        self.dice = config["dice"]

    def __str__(self):
        return "It's a %s armour, it provides %s damage reduction" % (self.type, self.dice)

class Character:
    def greet(self, greeting):
        print(greeting)

    def set_weapons(self):
        weapons = []
        primary_weapon = None
        for item in self.items:            
            if "weapon" in item:
                weapon = Weapon(item["weapon"])
                weapons.append(weapon)
                if weapon.primary:
                    primary_weapon = weapon
        if primary_weapon is None:
            print("No primary weapon set, choosing at random")
            primary_weapon = choice(weapons)
        print(f"{self.name}'s primary weapon is {primary_weapon}")
        self.primary_weapon = primary_weapon
        self.weapons = weapons

    def __init__(self, config, name = None):
        if name is not None:
            self.name = name
        else:
            self.name = config["name"]
        self.is_pc = config["is_pc"]
        self.max_hp = config["hp"]
        self.current_hp = config["hp"]
        self.abilities = config["abilities"]
        self.items = config["items"]
        if self.is_pc is False:
            self.morale = config["morale"]
        self.description = config.get("description")
        print(self.description)
        if "greeting" in config:
            self.greet(config["greeting"])
        self.alive = True
        self.set_weapons()
        if config["armour"] is not None:
            self.armour = Armour(config["armour"])
        else:
            self.armour = None
        

    def am_i_dead():
        # Well?
        if self.alive is False:
            print(f"{self.name}:I'm dead folks!")
    
   
    def roll_broken(self):
        print("Death roll") # Not crazy about this whole "broken" concept
        broken_roll = roll_dice("1d4")
        if broken_roll == 4:
            print("DEAD")
            self.alive = False

    def take_standard_damage(self,damage):
        if self.armour is not None:
            armour_reduction = roll_dice(self.armour.dice)
            print(f"reducing damage by {armour_reduction} due to armour")
            damage -= armour_reduction
        print(f"{self.name} took {damage} damage")
        self.current_hp -= self.current_hp
        if self.current_hp == 0:
            print("Bad times for you friend")
            self.roll_broken()
        elif self.current_hp < 0:
            print("DEAD")
            self.alive = False
        else:
            print(f"{self.name} is on {self.current_hp}")
            self.alive = True

    def make_standard_attack(self, weapon, target):
        print(f"{self.name} attacks {target.name} with {weapon.name}")
        dr = weapon.dr
        attack_role = roll_dice("1d20")
        # critical and fumble rolls go here
        if weapon.type == "melee":
            attack_role += self.abilities["strength"]
        if weapon.type == "ranged":
            attack_role += self.abilities["presence"]
        if attack_role >= dr:
            print(f"{self.name} hits!")
            damage = roll_dice(weapon.damage)
            target.take_standard_damage(damage)
        else:
            print(f"{self.name} misses")

    def get_available_actions(self, others):
        action_tuples = []
        for other in others:
            if len(self.weapons):
                action_tuples += [ (other, weapon) for weapon in self.weapons ]
        print(action_tuples)
        return action_tuples



with open("pc_sample.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.SafeLoader)

urvarg = Character(config)

with open("pc_sample_2.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.SafeLoader)
rolf = Character(config)


while (urvarg.alive) and (rolf.alive):
    urvarg.make_standard_attack(urvarg.primary_weapon, rolf)
    if rolf.alive:
        rolf.make_standard_attack(rolf.primary_weapon, urvarg)

actions = rolf.get_available_actions([urvarg])
rolf.make_standard_attack(actions[0][1], actions[0][0])
