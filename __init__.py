from random import randint, choice
import re
import yaml
import uuid


import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-m", "--manual", help = "If true, prompt the user to provide every dice roll", nargs='?', const=False)
# Read arguments from command line
args = parser.parse_args()


MANUAL_DICE_ROLLS = False
if args.manual:
    MANUAL_DICE_ROLLS = True
ALLOW_ATTACK_ALLIES = True

print("Starting the game")
print(f"MANUAL_DICE_ROLLS is {MANUAL_DICE_ROLLS}\n\n")
print("Enter 0 to skip manual dice rolls if needed")

def roll_dice(nd):
    result = 0
    if nd.startswith("d"):
        nd = "1" + nd
    if bool(re.search("^[0-9]*d[0-9]*$", nd)):
        split_nd = nd.split("d")
        n = int(split_nd[0])
        d = int(split_nd[1])
    else:
        raise ValueError("Invalid roll description")
    if MANUAL_DICE_ROLLS:
        result = int(input(f"Roll {nd} and type in the result. Press 0 to let the computer do it: "))
        if result > n * d:
            result = int(input(f"That result {result} is more than is possible with {nd}. If you're doing this on purpose as a test, enter the same thing now: "))

    if result == 0: # If manual dice rolls is false or the input from the user was 0
        nd = nd.lower()
        for _ in range(0,n):
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
        self.id = uuid.uuid4()        
        


    def __str__(self):
        return "It's a %s called %s it deals %s" % (self.category, self.name, self.damage)
    
class Armour:
    def __init__(self, config, self_character):
        self.type = config["type"]
        self.dice = config["dice"]
        if self.dice == "1d2":
            self.tier = 2
        if self.dice == "1d4":
            self.tier = 3
            if self_character.is_pc:
                self_character.abilities["agility"] += 2
                self_character.defence += 2
        if self.dice == "1d6":
            self.tier = 4
            if self_character.is_pc:
                self_character.abilities["agility"] += 4
                self_character.defence += 2
        else:
            self.tier = 1
        #TODO: What about shields. They would be a type of Reaction

    def reduce_tier(self, self_character, tier_reduction):
        # TODO: introduce tiers to this properly
        # Per the rules, if armour is damanged, the penalties to abilities are not modified. Thankfully...
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
    
    #TODO: Should there be an option to remove armour?

class Character:
    def greet(self, greeting):
        print(greeting)

    def set_weapons(self, is_init = False):
        print(f"Setting weapons for {self.name}")
        self.primary_weapon = None
        self.secondary_weapon = None
        if is_init:
            #We have to convert all the config into Weapon objects
            weapons = []
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
            if len(weapons) > 2:
                print(f"{self.name} is carrying {len(weapons)} weapons in {self.possessive} inventory. {len(weapons) - 2} will have to go in {self.possessive} bag")
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
        print(f"{self.name}'s weapon {weapon.name} is being destroyed")
        if weapon.category == "unarmed":
            print("Cannot destroy an unarmed weapon")
        else:
            for weapon_object in self.weapons:
                if weapon_object.id == weapon.id:
                    self.weapons.remove(weapon_object)
                    print(f"{self.name}'s weapon {weapon.name} has been destroyed")
                    self.set_weapons(False)
                    break

    def __init__(self, config, name = None):
        if name is not None:
            self.name = name
        else:
            self.name = config["name"]
        self.description = config.get("description")
        print(self.description)
        if "greeting" in config:
            self.greet(config["greeting"])
        self.max_hp = config["hp"]
        self.current_hp = config["hp"]
        self.alive = True
        self.is_pc = config["is_pc"]
        self.actions_this_turn = 0 #TODO: RAW are a bit vague on if there is a difference between attacks and actions (which could be using an item), but for now I'm treating them as the same
        if self.is_pc:
            self.abilities = config["abilities"]
            self.defence = config["abilities"]["agility"] # This can be modified separate to standard agility tests
            self.items = config["items"]
            self.init_weapons = config["weapons"]
        else:
            self.morale = config["morale"]
            self.size = config.get("size", 2)
        pronouns = config.get("pronouns", "they/them/their")
        pronouns_split = pronouns.split("/")
        if len(pronouns_split) != 3:
            pronouns_split = ["they","them","their"]
        self.subject = pronouns_split[0]
        self.third = pronouns_split[1] # TODO: read up on grammar terms
        self.possessive = pronouns_split[2]
        
        self.weapons = config.get("weapons",[])
        self.set_weapons(True)
        if config["armour"] is not None:
            self.armour = Armour(config["armour"], self)
        else:
            self.armour = None
        

    def am_i_dead(self):
        # Well?
        if self.alive is False:
            msg = choice([
                f"{self.name}: I'm dead folks!",
                f"I guess that's the last we'll see of ol' {self.name}",
                f"{self.name}'s dead Jim",
                f"That's a wrap on {self.name}",
            ])
            print(msg)
            return True
        else:
            return False
    
   
    def roll_broken(self):
        print("Death roll") # Not crazy about this whole "broken" concept
        broken_roll = roll_dice("1d4")
        if broken_roll == 4:
            print(f"{self.name} is DEAD")
            self.alive = False

    def take_standard_damage(self,damage):
        if self.armour is not None:
            print("Rolling for armour")
            armour_reduction = roll_dice(self.armour.dice)
            print(f"{self.name} has {self.current_hp} HP now.")
            print(f"Reducing damage by {armour_reduction} due to armour")
            damage -= armour_reduction
        if damage > 0:
            self.current_hp -= damage
            print(f"{self.name} took {damage} damage and is {self.current_hp} HP now")
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

    def make_defence_roll(self, attacker):
        defence_roll = roll_dice("1d20")
        fumble = False
        if defence_roll == 20:
            print("CRITICAL DEFENCE FAIL")
            self.actions_this_turn += 1
        elif defence_roll == 1:
            print("DEFENCE FUMBLE")
            fumble = True
        defence_roll += self.defence
        dr = 12
        if defence_roll >= dr:
            print(f"{self.name} dodged the attack from {attacker.name}")
            return True, fumble
        else:
            print(f"{self.name} did not dodge the attack from {attacker.name}")
            return False, fumble

    def pc_make_standard_attack(self, target, weapon):
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
                print(f"{self.name} hits! Rolling for damage")
                damage = roll_dice(weapon.damage)
                target_alive = target.take_standard_damage(multiplier * damage)
                if target_alive and critical and target.armour is not None:
                    target.armour.reduce_tier(target,1)
            else:
                print(f"{self.name} misses")

    def npc_make_standard_attack(self, target, weapon):
        print(f"{self.name} attacks {target.name} with {weapon.name}")
        multiplier = 1
        missed, fumble = target.make_defence_roll(self)
        if fumble:
            multiplier = 2
        if missed is not True:
            print("HIT. Rolling for damage")
            damage = multiplier * roll_dice(weapon.damage)
            target_alive = target.take_standard_damage(damage)
            if fumble and target_alive is True:
                print(f"{target.name} armour being reduced")
                target.armour.reduce_tier(target, 1)

    def get_available_actions(self, others):
        action_tuples = []
        for other in others:
            action_tuples += [ (other, weapon) for weapon in [self.primary_weapon, self.secondary_weapon] ]
        print(action_tuples)
        return action_tuples
    
    def start_turn(self):
        print(f"{self.name} is starting {self.possessive} turn")
        if self.am_i_dead():
            print(f"{self.name} is supposed to be dead. Something has gone wrong here")
        self.actions_this_turn += 1
        for _ in self.actions_this_turn:
            actions = get_available_actions(others)
        # TODO: Check for status effects
        # TODO: Check if dead after status effects
        # Get actions
        # Decide on action
        # Take action
        # Log results of action
        # Check if dead before ending turn



with open("pc_sample.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.SafeLoader)

urvarg = Character(config)
#urvarg2 = Character(config, "Urvarg2")
#urvarg3 = Character(config, "Urvarg3")

with open("pc_sample_2.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.SafeLoader)
rolf = Character(config)
#rolf2 = Character(config, "Rolf2")

#rolf.pc_make_standard_attack(urvarg, rolf.primary_weapon)
#rolf.pc_make_standard_attack(urvarg, rolf.primary_weapon)
#rolf.pc_make_standard_attack(urvarg, rolf.primary_weapon)
#rolf.pc_make_standard_attack(urvarg, rolf.primary_weapon)
#rolf.pc_make_standard_attack(urvarg, rolf.primary_weapon)

#while (urvarg.alive) and (rolf.alive):
#    urvarg.pc_make_standard_attack(rolf, urvarg.primary_weapon)
#    if rolf.alive:
#        rolf.pc_make_standard_attack(urvarg, rolf.primary_weapon)

with open("npc_sample.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.SafeLoader)

big_guy = Character(config)

#actions = rolf.get_available_actions([urvarg])
#print(actions)
#rolf.pc_make_standard_attack(actions[0][0], actions[0][1])

#rolf.start_turn()

#urvarg.pc_make_standard_attack(big_guy, urvarg.primary_weapon)

big_guy.npc_make_standard_attack(urvarg, big_guy.primary_weapon)
rolf.pc_make_standard_attack(big_guy, rolf.primary_weapon)