import argparse
import logging
import re
import uuid
import yaml

from random import randint, choice, shuffle
from itertools import combinations_with_replacement

parser = argparse.ArgumentParser()
parser.add_argument("-m", "--manual", help = "If true, prompt the user to provide every dice roll", nargs='?', const=False)
parser.add_argument("-l", "--log", help = "Log level", nargs='?', const="info")
args = parser.parse_args()
if args.log == "info":
    logging.basicConfig(
        format="{asctime} - {levelname} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M",
        level=logging.INFO)
elif args.log == "debug":
    logging.basicConfig(
        format="{asctime} - {levelname} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M",
        level=logging.DEBUG)

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

class Scroll:
    def list_actions(self,others):
        if self.scroll_code == 1: # Fireball
            #TODO: Need to filter based on ALLOW_ATTACK_ALLIES
            target_combinations = list(combinations_with_replacement(others,2))
            action_tuples = [ (tc, self) for tc in target_combinations]
            return action_tuples


    def __init__(self, name, flavour):
        self.name = name
        self.flavour = flavour
        self.id = uuid.uuid4()
        if name.lower().replace(" ","").replace("_","") == "fireball":
            self.type = "offensive"
            self.scroll_code = 1


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
        print('"' + greeting + '"')

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
        logging.debug(f"{self.name}'s weapon {weapon.name} is being destroyed")
        if weapon.category == "unarmed":
            logging.debug("Cannot destroy an unarmed weapon")
        else:
            for weapon_object in self.weapons:
                if weapon_object.id == weapon.id:
                    self.weapons.remove(weapon_object)
                    print(f"{self.name}'s weapon {weapon.name} has been destroyed")
                    self.set_weapons(False)
                    break

    def random_action(self, actions):
        return choice(actions)
    
    def manual_action(self, actions):
        print("\n\nHere are the available options\n")
        for i, action in enumerate(actions):
            print(f"Option {i}: ")
            print(f"Use {action[1].name} on {action[0].name}")
        decision = int(input("\nWhich option? Just type the number: "))
        return actions[decision]
    
    def set_scrolls(self, items):
        scrolls = []
        for item in items:
            print(item)
            if item["type"] == "scroll":
                scrolls.append(Scroll(item["name"], item["flavour_name"]))
        self.scrolls = scrolls
                

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
            self.make_standard_attack = self.pc_make_standard_attack
            self.set_scrolls(self.items) #TODO: It would be nice to be able to add new scrolls
        else:
            self.morale = config["morale"]
            self.size = config.get("size", 2)
            self.make_standard_attack = self.npc_make_standard_attack
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
        if MANUAL_DICE_ROLLS is True:
            self.decision_function = self.manual_action
        else:
            self.decision_function = self.random_action

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
        logging.debug("Death roll") # Not crazy about this whole "broken" concept
        broken_roll = roll_dice("1d4")
        if broken_roll == 4:
            print(f"{self.name} is DEAD")
            self.alive = False

    def take_standard_damage(self,damage):
        if self.armour is not None:
            logging.debug("Rolling for armour")
            armour_reduction = roll_dice(self.armour.dice)
            logging.debug(f"{self.name} has {self.current_hp} HP before taking damage.")
            print(f"Reducing damage by {armour_reduction} due to armour")
            damage -= armour_reduction
        if damage > 0:
            self.current_hp -= damage
            print(f"{self.name} took {damage} damage and is {self.current_hp} HP now")
            if self.current_hp == 0:
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
            print("CRITICAL DEFENCE WIN")
            self.actions_this_turn += 1
        elif defence_roll == 1:
            print("DEFENCE FUMBLE")
            fumble = True
        defence_roll += self.defence
        dr = 12
        logging.debug(f"DR is {dr}, roll result is {defence_roll}")
        if defence_roll >= dr:
            logging.debug(f"{self.name} dodged the attack from {attacker.name}")
            return True, fumble
        else:
            logging.debug(f"{self.name} did not dodge the attack from {attacker.name}")
            return False, fumble

    def pc_make_standard_attack(self, target, weapon):
        print(f"{self.name} (PC) attacks {target.name} with {weapon.name}")
        dr = weapon.dr
        multiplier = 1
        critical = False
        attack_roll = roll_dice("1d20")
        if attack_roll == 20:
            critical = True
            print("CRITICAL")
            multiplier = 2
        if attack_roll == 1:
            self.destroy_weapon(weapon)
        # fumble rolls go here
        else:
            if weapon.type == "melee":
                attack_roll += self.abilities["strength"]
            elif weapon.type == "ranged":
                attack_roll += self.abilities["presence"]
            logging.debug(f"DR is {dr}, roll result is {attack_roll}, critical is {critical}")
            if critical or attack_roll >= dr: # Presumably Crits always hit?
                print(f"{self.name} hits! Rolling for damage.")
                damage = roll_dice(weapon.damage)
                logging.debug(f"Damage roll is {damage}, multiplier is {multiplier}")
                target_alive = target.take_standard_damage(multiplier * damage)
                if target_alive and critical and target.armour is not None:
                    target.armour.reduce_tier(target,1)
            else:
                print(f"{self.name} misses")
            if MANUAL_DICE_ROLLS:
                input("--Continue--")


    def npc_make_standard_attack(self, target, weapon):
        print(f"{self.name} (NPC) attacks {target.name} with {weapon.name}")
        multiplier = 1
        missed, fumble = target.make_defence_roll(self)
        if fumble:
            multiplier = 2
        if missed:
            print(f"{self.name} misses.")
        else:
            print(f"{self.name} hits! Rolling for damage.")
            damage = roll_dice(weapon.damage)
            logging.debug(f"Damage roll is {damage}, multiplier is {multiplier}")
            target_alive = target.take_standard_damage(multiplier * damage)
            if fumble and target_alive is True:
                print(f"{target.name}'s armour is damaged")
                target.armour.reduce_tier(target, 1)

    def npc_make_standard_attack_on_npc(self, target, weapon):
        # To handle this edge-case, assume any npc on npc attack hit automatically
        # TODO: Give NPCs placeholder defence stats to handle this better
        print(f"{self.name} (NPC) attacks {target.name} with {weapon.name}")
        multiplier = 1
        damage = multiplier * roll_dice(weapon.damage)
        target.take_standard_damage(damage)

    def get_available_actions(self, others):
        #TODO: Need to filter based on ALLOW_ATTACK_ALLIES
        action_tuples = []
        for other in others:
            action_tuples += [ (other, weapon) for weapon in [self.primary_weapon, self.secondary_weapon] ]
        if self.scrolls is not None:
            for scroll in self.scrolls:
                scroll_actions = scroll.list_actions(others)
                logging.debug(scroll_actions)

        return action_tuples
    
    def start_turn(self, others):
        print("------------------------------")
        print(f"{self.name} is starting {self.possessive} turn")
        if self.am_i_dead():
            logging.warning(f"{self.name} is supposed to be dead. Something has gone wrong here")
            print("------------------------------")
            return None
        self.actions_this_turn += 1
        for _ in range(0, self.actions_this_turn):
            actions = self.get_available_actions(others)
            action = self.decision_function(actions)
            if action[0].is_pc and self.is_pc: # this might be the usecase for is_ally?
                logging.warning(f"{self.name} is attacking their ally {action[0].name}")
                self.make_standard_attack(action[0], action[1])
            elif (not action[0].is_pc) and (not self.is_pc):
                logging.warning(f"{self.name} is attacking their ally {action[0].name}")
                self.npc_make_standard_attack_on_npc(action[0], action[1])
            else:
                self.make_standard_attack(action[0], action[1])
            self.last_target = action[0]
            print("------------------------------")
            return action[0]
        # TODO: Check for status effects
        # TODO: Check if dead after status effects
        # Get actions
        # Decide on action
        # Take action
        # Log results of action
        # Check if dead before ending turn

    def __str__(self):
        return f"A character called {self.name}. {self.description}"
    

def poll_team(team):
    team_left = False
    for char in team.chars:
        if char.alive:
            team_left = True
            print(f"There's someone {char.name} left on {team.name}")
            break
    return team_left

class Team:
    def __init__(self, characters, name):
        self.chars_starting = characters
        self.chars = characters
        self.name = name

    def update_team(self):
        self.chars = [char for char in self.chars if char.alive]
        return len(self.chars)



class Battle: # Is this one class too many? Probably, but I've got class fever over here
    def initiative(self):
        print("Roll for initiative")
        initiative_roll = roll_dice("1d6")
        print(f"Initiative roll is {initiative_roll}")
        if initiative_roll <= 3:
            return False # PCs not going first
        else:
            return True # PCs going first
        # TODO: Individual initiative may not be RAW

    
    def __init__(self, pcs, npcs):
        shuffle(pcs)
        shuffle(npcs)
        self.pcs = pcs
        self.npcs = npcs
        self.participants_starting = pcs + npcs
        self.participants = pcs + npcs
        self.round = 1

        pcs_going_first = self.initiative()
        if pcs_going_first:
            self.first_team = Team(pcs,"Team 1")
            self.second_team = Team(npcs,"Team 2")
        else:
            self.first_team = Team(npcs,"Team 1")
            self.second_team = Team(pcs,"Team 2")

        self.battle_over = False


    def run_battle(self):
        rounds = 0
        team_turns_taken = 0
        individual_turns_taken = 0
        while self.battle_over is False:

            #TODO: This whole team term block could be a function
            for char in self.first_team.chars:
                others = [x for x in self.participants if x != char and x.alive is True]
                if char.alive:
                    target = char.start_turn(others)
                    individual_turns_taken += 1
                    if target is not None:
                        self.first_team.last_target = target
            team_turns_taken += 1
            if 0 == self.first_team.update_team():
                self.battle_over = True
                print(f"Second team ({self.second_team.name}) won. Congrats to the survivor(s): {','.join([char.name for char in self.second_team.chars])}")
                break
            if 0 == self.second_team.update_team():
                self.battle_over = True
                print(f"First team ({self.first_team.name}) won. Congrats to the survivor(s): {', '.join([char.name for char in self.first_team.chars])}")
                break
            
            for char in self.second_team.chars:
                others = [x for x in self.participants if x != char and x.alive is True]
                if char.alive:
                    char.start_turn(others)
                    individual_turns_taken += 1
            team_turns_taken += 1
            if 0 == self.second_team.update_team():
                self.battle_over = True
                print(f"First team ({self.first_team.name}) won. Congrats to the survivors(s): {','.join([char.name for char in self.first_team.chars])}")
                break
            if 0 == self.first_team.update_team():
                self.battle_over = True
                print(f"Second team ({self.second_team.name}) won. Congrats to the survivors(s): {','.join([char.name for char in self.second_team.chars])}")
                break
            rounds += 1
        print(self.first_team.chars)
        print(self.second_team.chars)
        print(f"There were {rounds} rounds and {individual_turns_taken} individual turns")



with open("configs/pc_sample.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.SafeLoader)
urvarg = Character(config)

with open("configs/pc_sample_2.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.SafeLoader)
rolf = Character(config)

with open("configs/pc_sample_scroll.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.SafeLoader)
urm = Character(config)

with open("configs/npc_sample.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.SafeLoader)
big_guy = Character(config)

with open("configs/npc_sample_2.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.SafeLoader)
little_guy = Character(config)
little_guy_2 = Character(config, "The Other Little Guy")

urm.get_available_actions([big_guy])

#battle = Battle([rolf, urvarg, urm],[big_guy, little_guy, little_guy_2])
#battle.run_battle()
