from random import randint, choice
import re
import yaml

MANUAL_DICE_ROLLS = False
ALLOW_ATTACK_ALLIES = True

print("Starting the game")
print(f"MANUAL_DICE_ROLLS is {MANUAL_DICE_ROLLS}\n\n")

def roll_dice(nd):
    if nd.startswith("d"):
        nd = "1" + nd
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
    def __init__(self, config = {}):
        self.name = config.get("name","Unarmed")
        self.type = config.get("type","melee")
        self.damage = config.get("damage","1d2")
        self.dr = config.get("dr",12)
        self.category = config.get("category","unarmed")
        self.rank = config.get("rank",False)

    def __str__(self):
        return "It's a %s called %s it deals %s" % (self.category, self.name, self.damage)
    
class Armour:
    def __init__(self, config):
        self.type = config["type"]
        self.dice = config["dice"]
        if self.dice == "1d2":
            self.tier = 2
        if self.dice == "1d4":
            self.tier = 3
        if self.dice == "1d6":
            self.tier = 4
        else:
            self.tier = 1
        #TODO: What about shields. They would be a type of Reaction

    def reduce_tier(self, self_character, tier_reduction):
        # TODO: introduce tiers to this properly
        print(f"Reducing {self_character.name}'s armour by a tier of {tier_reduction}")
        if self.dice == "1d2":
            print("Armour has been destroyed")
            self_character.armour = None #TODO: Have an unarmoured state
        elif self.dice == "1d4":
            self.dice = "1d2"
        elif self.dice == "1d6":
            self.dice = "1d4"

    def __str__(self):
        return "It's a %s armour, it provides %s damage reduction" % (self.type, self.dice)

class Character:
    def greet(self, greeting):
        print(greeting)

    def set_weapons(self, is_init = False):
        if is_init:
            #We have to convert all the config into Weapon objects
            weapons = []
            self.primary_weapon = None
            self.secondary_weapon = None
            for weapon in self.weapons:
                weapon = Weapon(weapon)
                weapons.append(weapon)
                if weapon.rank == "primary":
                    self.primary_weapon = weapon
                elif weapon.rank == "secondary":
                    self.secondary_weapon = weapon
        else:
            weapons = self.weapons
        if len(weapons) == 0:
            self.primary_weapon = Weapon() #unarmed
            self.secondary_weapon = Weapon()
        elif len(weapons) == 1:
            self.primary_weapon = weapons[0]
            self.secondary_weapon = Weapon()
        else:
            print(f"{self.name} is carrying {len(weapons)} in their inventory")
            if self.primary_weapon is None:
                print("No primary weapon set, choosing at random")
                self.primary_weapon = choice(weapons)
        if self.secondary_weapon is None:
            print("No secondary weapon set, choosing at random")
            self.secondary_weapon = choice([weapon for weapon in weapons if weapon != self.primary_weapon.name])
        print(f"{self.name}'s primary weapon is {self.primary_weapon.name}")
        print(f"{self.name}'s secondary weapon is {self.secondary_weapon.name}")
        self.weapons = weapons

    def destroy_weapon(self, weapon):
        print(f"Weapon {weapon.name} has been destroyed")
        if weapon.category == "unarmed":
            print("Cannot destroy an unarmed weapon")
        else:
            self.weapons.remove(weapon)
            weapon = None
            self.set_weapons(False)

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
        self.init_weapons = config["weapons"]
        if self.is_pc is False:
            self.morale = config["morale"]
        self.description = config.get("description")
        print(self.description)
        if "greeting" in config:
            self.greet(config["greeting"])
        self.alive = True
        self.weapons = config.get("weapons",[])
        self.set_weapons(True)
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
            print(f"{self.name} is DEAD")
            self.alive = False

    def take_standard_damage(self,damage):
        if self.armour is not None:
            armour_reduction = roll_dice(self.armour.dice)
            print(f"reducing damage by {armour_reduction} due to armour")
            damage -= armour_reduction
        if damage > 0:
            print(f"{self.name} took {damage} damage")
            self.current_hp -= self.current_hp
            if self.current_hp == 0:
                print("Bad times for you friend")
                self.roll_broken()
            elif self.current_hp < 0:
                print(f"{self.name} is DEAD")
                self.alive = False
            else:
                print(f"{self.name} is on {self.current_hp}")
                self.alive = True
            return self.alive
        else:
            print("No damage done")

    def make_standard_attack(self, target, weapon):
        print(f"{self.name} attacks {target.name} with {weapon.name}")
        dr = weapon.dr
        multiplier = 1
        critical = True
        attack_role = roll_dice("1d20")
        if attack_role == 20:
            critical = True
            print("CRITICAL")
            multiplier = 2
        if attack_role == 1:
            self.destroy_weapon(weapon)
        # fumble rolls go here
        else:
            if weapon.type == "melee":
                attack_role += self.abilities["strength"]
            if weapon.type == "ranged":
                attack_role += self.abilities["presence"]
            if attack_role >= dr:
                print(f"{self.name} hits!")
                damage = roll_dice(weapon.damage)
                target_alive = target.take_standard_damage(multiplier * damage)
                if target_alive and critical and target.armour is not None:
                    target.armour.reduce_tier(target,1)
            else:
                print(f"{self.name} misses")

    def get_available_actions(self, others):
        action_tuples = []
        for other in others:
            action_tuples += [ (other, weapon) for weapon in [self.primary_weapon, self.secondary_weapon] ]
        print(action_tuples)
        return action_tuples



with open("pc_sample.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.SafeLoader)

urvarg = Character(config)
urvarg2 = Character(config, "Urvarg2")
urvarg3 = Character(config, "Urvarg3")

with open("pc_sample_2.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.SafeLoader)
rolf = Character(config)
rolf2 = Character(config, "Rolf2")

#def run_battle(allies, enemies):
#    for 



while (urvarg.alive) and (rolf.alive):
    urvarg.make_standard_attack(rolf, urvarg.primary_weapon)
    if rolf.alive:
        rolf.make_standard_attack(urvarg, rolf.primary_weapon)

#actions = rolf.get_available_actions([urvarg])
#print(actions)
#rolf.make_standard_attack(actions[0][0], actions[0][1])
