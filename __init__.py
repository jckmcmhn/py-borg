import argparse
import logging
import yaml

from random import choice

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


from classes import roll_dice
from classes.battle import Battle
from classes.armour import Armour
from classes.weapon import Weapon
from classes.scroll import Scroll

print("Starting the game")
print(f"MANUAL_DICE_ROLLS is {MANUAL_DICE_ROLLS}\n\n")
print("Enter 0 to skip manual dice rolls if needed")

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
            if isinstance(action[1], Weapon):
                print(f"Use {action[1].name} on {action[0].name}")
            elif isinstance(action[1], Scroll):
                print(f"Use {action[1].name} on {','.join([a.name for a in action[0]])}")
        decision = int(input("\nWhich option? Just type the number: "))
        return actions[decision]
    
    def set_scrolls(self, items):
        scrolls = []
        for item in items:
            if item["type"] == "scroll":
                scrolls.append(Scroll(item["name"], item["flavour_name"]))
        print("Here are the scrolls" + ", ".join([scroll.name for scroll in scrolls]))
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
            print("Getting powers for today")
            self.powers = roll_dice("1d4", MANUAL_DICE_ROLLS) + self.abilities["presence"]
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
        self.dizzy = False # TODO: If true: During this time, Powers will always fail in the worst possible way.

    def am_i_dead(self):
        # Well?
        if self.alive is False or self.current_hp < 0:
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
        broken_roll = roll_dice("1d4", MANUAL_DICE_ROLLS)
        if broken_roll == 4:
            print(f"{self.name} is DEAD")
            self.alive = False

    def take_standard_damage(self,damage):
        if (self.armour is not None) and (not self.armour.dice.startswith("0d2")):
            logging.debug("Rolling for armour")
            armour_reduction = roll_dice(self.armour.dice, MANUAL_DICE_ROLLS)
            logging.debug(f"{self.name} has {self.current_hp} HP before taking damage.")
            print(f"Reducing damage by {armour_reduction} due to armour")
            damage -= armour_reduction
        else:
            print(f"{self.name} has no armour")
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
        defence_roll = roll_dice("1d20", MANUAL_DICE_ROLLS)
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
    
    def use_scroll(self, action):
        if self.dizzy:
            logging.warning("Shouldn't try and use a scroll when dizzy")
            self.take_standard_damage(4)
            return
        print("Rolling to hit for a scroll") #TODO: fix this
        scroll_roll = roll_dice("1d20", MANUAL_DICE_ROLLS)
        critical = False
        multiplier = 1
        if scroll_roll == 20:
            critical = True
            print("CRITICAL")
            multiplier = 2
        if scroll_roll == 1:
            #self.destroy_weapon(weapon)
            print("FUMBLE") # TODO: Figure out what to do here
        # fumble rolls go here
        scroll_roll += self.abilities["presence"]
        dr = 12
        logging.debug(f"DR is {dr}, roll result is {scroll_roll}, critical is {critical}")
        if critical or scroll_roll >= dr:
            for target in action[0]:
                if target.alive is False:
                    logging.warning("Attacking someone who is already dead") #TODO: Fix this
                action[1].inflict_damage(target,multiplier)
            #target_alive = target.take_standard_damage(multiplier * damage)
            self.powers -= 1
        elif scroll_roll < dr:
            print(f"{self.name} failed the scroll roll and is now dizzy. Roll a d2 for HP loss")
            damage = roll_dice("1d2", MANUAL_DICE_ROLLS)
            self.take_standard_damage(damage)
            self.dizzy = True #TODO: How to make this only apply "for the next hour"


    def pc_make_standard_attack(self, target, weapon):
        print(f"{self.name} (PC) attacks {target.name} with {weapon.name}")
        dr = weapon.dr
        multiplier = 1
        critical = False
        attack_roll = roll_dice("1d20", MANUAL_DICE_ROLLS)
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
                damage = roll_dice(weapon.damage, MANUAL_DICE_ROLLS)
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
            damage = roll_dice(weapon.damage, MANUAL_DICE_ROLLS)
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
        damage = multiplier * roll_dice(weapon.damage, MANUAL_DICE_ROLLS)
        target.take_standard_damage(damage)

    def get_available_actions(self, others):
        #TODO: Need to filter based on ALLOW_ATTACK_ALLIES
        weapon_actions = []
        scroll_actions = []
        for other in others:
            weapon_actions += [ (other, weapon) for weapon in [self.primary_weapon, self.secondary_weapon] ]
        if self.is_pc is True:
            if self.powers > 1 and (self.scrolls is not None):
                for scroll in self.scrolls:
                    scroll_actions = scroll.list_actions(others)
                    logging.debug(scroll_actions)
        return scroll_actions + weapon_actions
    
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
            # Scrolls can attack more than one Character, so this bit needs to handle them differently
            if isinstance(action[1], Scroll):
                self.use_scroll(action)
                #self.make_standard_attack(action[0], action[1])
            else:
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


with open("configs/pc_sample.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.SafeLoader)
urvarg = Character(config)

with open("configs/pc_sample_2.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.SafeLoader)
rolf = Character(config)

with open("configs/pc_sample_scroll.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.SafeLoader)
urm = Character(config)
urm2 = Character(config, "urm2")

with open("configs/npc_sample.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.SafeLoader)
big_guy = Character(config)
big_guy2 = Character(config, "Less big")

with open("configs/npc_sample_2.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.SafeLoader)
little_guy = Character(config)
little_guy_2 = Character(config, "The Other Little Guy")
little_guy_3 = Character(config, "YALG")
little_guy_4 = Character(config, "YALG2")


battle = Battle([rolf, urvarg, urm],[big_guy, little_guy, little_guy_2, little_guy_3, little_guy_4], big_guy, MANUAL_DICE_ROLLS)
battle.run_battle()