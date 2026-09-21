from random import choice, random
import logging
from classes import roll_dice
from classes.equipment import Scroll, General, Weapon, Armour

class Character:
    def __init__(self, config, settings, name = None):
        if name is not None:
            self.name = name
        else:
            self.name = config["name"]
        self.settings = settings
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
            self.make_standard_attack = self.pc_attack_with_weapon
            self.set_scrolls(self.items) #TODO: It would be nice to be able to add new scrolls
            if len(self.scrolls): #TODO: What if a character gets a scroll in future. Problem for another time
                print("Getting powers for today")
                self.powers = roll_dice("1d4", self.settings["manual_dice"] in ["pc_only", "always"]) + self.abilities["presence"]
            else:
                self.powers = 0
            self.set_general_equipment(self.items)
        else:
            self.morale = config["morale"]
            self.size = config.get("size", 2)
            self.make_standard_attack = self.npc_attack_with_weapon
            self.most_damage_taken = 0
            self.most_damage_taken_from = None
            self.enemy_for_life = None
            self.last_hit_enemy = None
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
            self.armour = Armour(config["armour"], self, self.settings)
        else:
            self.armour = None
        if self.settings["manual_dice"] == "always":
            self.decision_function = self.manual_action
        elif self.is_pc and (self.settings["manual_dice"] in ["pc_only",  "pc_decisions"]):
            self.decision_function = self.manual_action
        elif (not self.is_pc) and (self.settings["manual_dice"] == "npc_only"):
            self.decision_function = self.manual_action
        elif (not self.is_pc):
            self.decision_function = self.rules_based_action
        else:
            self.decision_function = self.random_action
        self.statuses = {}
        print("----")

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
                weapon = Weapon(self.settings, weapon)
                weapons.append(weapon)
                if weapon.rank == "primary":
                    self.primary_weapon = weapon
                elif weapon.rank == "secondary":
                    self.secondary_weapon = weapon
        else:
            weapons = self.weapons
        if len(weapons) == 0:
            self.primary_weapon = Weapon(self.settings) #unarmed
            self.secondary_weapon = Weapon(self.settings)
        elif len(weapons) == 1:
            self.primary_weapon = weapons[0]
            self.secondary_weapon = Weapon(self.settings)
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

    def set_scrolls(self, items):
        scrolls = []
        scroll_codes = []
        for item in items:
            if item["type"] == "scroll":
                scroll = Scroll(item["name"], item["flavour_name"], self.settings)
                scrolls.append(scroll)
                scroll_codes.append(scroll.scroll_code)
        if len(scrolls):
            print(f"Here are {self.name}'s scrolls: {', '.join([scroll.name for scroll in scrolls])}")
        else:
            print(f"{self.name} is scroll-less")
        self.scrolls = scrolls
        self.scroll_codes = scroll_codes

    def set_general_equipment(self, items):
        equipment = []
        for item in items:
            if item["type"] != "scroll":
                i = General(item["name"], item["dice"], self.settings)
                equipment.append(i)
        print(f"Here is {self.name}'s general equipment: {', '.join([i.name for i in equipment])}")
        self.equipment = equipment

    def random_action(self, allies, enemies):
        actions = self.get_available_actions(allies, enemies)
        return choice(actions)
    
    def rules_based_action(self, allies, enemies): # TODO: Make a hard mode version of this that knows more about enemy states
        logging.debug(f"{self.name} is making a rules-based decision on what to do next")

        # Reset grudges and grievances based on whether they're targets are still alive
        if self.enemy_for_life is not None:
           if not self.enemy_for_life.alive:
                print(f"{self.name} gloats over the body of {self.possessive} fallen enemy for life {self.enemy_for_life.name}.\n'That's what you get for messing with {self.name}' {self.subject} sneers")
                self.enemy_for_life = None # TODO: This does mean an enemy can have more than one enemy for life per life, which doesn't seem right
        if self.most_damage_taken_from is not None:
            if not self.most_damage_taken_from.alive:
                self.most_damage_taken_from = None
                logging.debug(f"{self.name} has cleared their most_damage_taken_from status")
        if self.last_hit_enemy is not None:
            if not self.most_damage_taken_from.alive:
                self.most_damage_taken_from = None
                logging.debug(f"{self.name} has cleared their last_hit_enemy status")
        logging.debug(f"{self.name}'s grudges and grievances: enemy_for_life = {self.enemy_for_life}, most_damage_taken_from = {self.most_damage_taken_from}, last_hit_enemy = {self.last_hit_enemy}")
        if self.enemy_for_life is not None:
            print(f"{self.name} is attacking {self.possessive} enemy for life {self.enemy_for_life.name}")
            return ((self.enemy_for_life,), self.primary_weapon)
        elif self.most_damage_taken_from is not None:
            print(f"{self.name} is attacking the enemy who has done the most damage to {self.third}: {self.most_damage_taken_from.name}")
            return ((self.most_damage_taken_from,), self.primary_weapon)
        elif self.last_hit_enemy is not None:
            if random() < 0.7:
                print(f"{self.name} is attacking the enemy they last hit: {self.last_hit_enemy.name}")
                return ((self.last_hit_enemy,), self.primary_weapon)
            else:
                print(f"{self.name} could attack the enemy they last hit: {self.last_hit_enemy.name} but has decided not to")
                action = self.random_action(allies, enemies)
                return action
        else:
            print(f"{self.name} is picking a target at random")
            action = self.random_action(allies, enemies)
            return action

    def manual_action(self, allies, enemies):
        print("\n\nHere are the available options\n")
        actions = self.get_available_actions(allies, enemies)
        print("Option -1:") #TODO: Hide this if playing a "real" game
        print("View current game state\n",)

        for i, action in enumerate(actions):
            i += 1
            print(f"Option {i}: ")
            tool = action[1]
            targets = action[0]
            if tool.name.lower() == "death": #TODO: this is clumsy
                print(f"Cast DEATH which will hit all creatures\n")
            elif len(targets) > 1:
                print(f"Use {tool.name} on {', '.join([target.name for target in targets])}.\nHow many of these targets are affected will depend on a subsequent {tool.n} roll\n")
            else:
                print(f"Use {tool.name} on {targets[0].name}\n")
        decision = -1
        while decision == -1:
            decision = int(input("\nWhich option? Just type the number: "))
            if decision == -1:
                for char in [self] + allies + enemies: #TODO: This should be handled less clumsily. Arguably, shouldn't let people see the enemy stats by default
                    print(char.name)
                    print(char.get_obs())

        return actions[decision - 1]

    def get_obs(self, audience = "admin"):
        # admin means show everything anyone knows, friends means share stats players might share amongst each other, gm means share stats on NPCs that only the GM has
        if self.alive is False:
            return {}
        if self.is_pc: 
            obs = {
                "p_weapon_dice": self.primary_weapon.dice, # an observant human GM would know this #TODO: Though maybe not on round 1
                "s_weapon_dice": self.secondary_weapon.dice, # an observant human GM would know this #TODO: Though maybe not on round 1
                "scroll_codes": self.scroll_codes, # TODO: I would like to eventually make this "scrolls that audience has seen" but for now...
                "armour_dice": self.armour.dice, # an observant human GM would know this #TODO: Though maybe not on round 1
                "dizzy": "dizzy" in self.statuses,
                "extra_actions_this_turn": self.actions_this_turn
            }
            if audience in ["admin","friends"]: # for now, let's say all PCs have thorough knowledge of their team mates states
                obs["max_hp"] = self.max_hp
                obs["current_hp"] = self.current_hp
                obs["strength"] = self.abilities["strength"]
                obs["presence"] = self.abilities["presence"]
                obs["agility"] = self.abilities["agility"]
                obs["toughness"] = self.abilities["toughness"]
                obs["defence"] = self.defence
                obs["powers"] = self.powers
                obs["number_items"] = self.items #TODO: This should ideally be # of useful items, or # of items by category

        elif not self.is_pc:
            obs = {
                "p_weapon_dice": self.primary_weapon.dice, # an observant human player would know this
                "s_weapon_dice": self.secondary_weapon.dice, # an observant human player would know this
                "size": self.size,
            }
            if audience in ["admin", "gm"]:
                obs["max_hp"] = self.max_hp
                obs["current_hp"] = self.current_hp
                obs["morale"]: self.morale #TODO: PCs would know this post-morale roll
                #obs["defence"] = self.defence
                #obs["powers"] = self.powers
                #obs["number_items"] = self.items #TODO: This should ideally be # of useful items, or # of items by category
        return obs

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
        logging.debug("roll_broken: Death roll") # Not crazy about this whole "broken" concept
        broken_roll = roll_dice("1d4", self.settings["manual_dice"] in ["always", "npc_only"])
        if broken_roll == 4:
            print(f"{self.name} rolled a four and is now DEAD!")
            self.alive = False
        else:
            logging.debug(f"{self.name} rolled a {broken_roll}. This result hasn't been implemented in the code yet.") #TODO

    def apply_damage(self,damage):
        if (self.armour is not None) and (not self.armour.dice.startswith("0d2")):
            logging.debug(f"apply_damage: Incoming damage is {damage}. Rolling for armour")
            armour_reduction = roll_dice(self.armour.dice, self.settings["manual_dice"] in ["always"])
            logging.debug(f"apply_damage: {self.name} has {self.current_hp} HP before taking damage.")
            logging.info(f"Reducing damage by {armour_reduction} due to armour")
            damage -= armour_reduction
        else:
            print(f"{self.name} has no armour")
        if damage > 0:
            self.current_hp -= damage
            print(f"{self.name} took {damage} damage and is on {self.current_hp} HP now") #TODO: Option to hide this second part, players shouldn't know how many HP an enemy has left
            if self.current_hp == 0:
                self.roll_broken()
            elif self.current_hp < 0:
                print(f"{self.name} is DEAD")
                self.alive = False
            else:
                self.alive = True
            #if self.alive and not self.is_pc:
            #    self.npc_calculate_vendettas(attacker,damage)
            return self.alive
        else:
            print("No damage done")

    def apply_healing(self,heal):
        if heal > 0:
            self.current_hp += heal
            if self.current_hp > self.max_hp:
                logging.warning(f"{self.name}'s HP after healing would be greater than {self.possessive} max HP. The HP above max HP will be ignored.")
            self.current_hp = min(self.current_hp, self.max_hp)
            print(f"{self.name} healed {heal} damage and is {self.current_hp} HP now")
            return self.alive
        else:
            print("No healing done")

    def make_defence_roll(self, attacker):
        defence_roll = roll_dice("1d20", self.settings["manual_dice"] in ["always", "pc_only"])
        fumble = False
        if defence_roll == 20:
            print("CRITICAL DEFENCE WIN")
            self.actions_this_turn += 1
        elif defence_roll == 1:
            print("DEFENCE FUMBLE")
            fumble = True
        defence_roll += self.defence + self.settings["to_dodge"]
        dr = 12
        logging.debug(f"make_defence_roll: DR is {dr}, roll result is {defence_roll}")
        if defence_roll >= dr:
            logging.debug(f"make_defence_roll: {self.name} dodged the attack from {attacker.name}")
            return True, fumble
        else:
            logging.debug(f"make_defence_roll: {self.name} did not dodge the attack from {attacker.name}")
            return False, fumble

    def use_equipment(self, action):
        equipment = action[1]
        targets = action[0]
        for target in targets:
            logging.debug(f"use_equipment: {self.name} is using {equipment.name} on {target.name}")
            equipment.use(target)
        equipment.count -= 1
        print(f"There are {equipment.count} {equipment.name}s left")


    def pc_attack_with_weapon(self, target, weapon):
        print(f"{self.name} (PC) attacks {target.name} with {weapon.name}")
        dr = weapon.dr
        multiplier = 1
        critical = False
        attack_roll = roll_dice("1d20", self.settings["manual_dice"] in ["always", "pc_only"])
        if attack_roll == 20:
            critical = True
            print("CRITICAL")
            multiplier = 2
        if attack_roll == 1:
            self.destroy_weapon(weapon)
        # fumble rolls go here
        else:
            attack_roll += self.settings["to_hit"]
            if weapon.type == "melee":
                attack_roll += self.abilities["strength"]
            elif weapon.type == "ranged":
                attack_roll += self.abilities["presence"]
            logging.debug(f"pc_attack_with_weapon: DR is {dr}, roll result is {attack_roll}, critical is {critical}")
            if critical or attack_roll >= dr: # Presumably Crits always hit?
                print(f"{self.name} hits! Rolling for damage.")
                damage = roll_dice(weapon.dice, self.settings["manual_dice"] in ["always", "pc_only"])
                logging.debug(f"pc_attack_with_weapon: Damage roll is {damage}, multiplier is {multiplier}")
                target_alive = target.apply_damage(multiplier * damage)
                if target_alive and critical and target.armour is not None:
                    target.armour.reduce_tier(target,1)
                if (not target.is_pc) and target_alive:
                    target.npc_calculate_vendettas(self,damage) # TODO: This is the pre-armour reduction damage # Only doing this on weapon attacks isn't right
            else:
                print(f"{self.name} misses")


    def npc_attack_with_weapon(self, target, weapon):
        print(f"{self.name} (NPC) attacks {target.name} with {weapon.name}. Make defence roll.")
        multiplier = 1
        missed, fumble = target.make_defence_roll(self)
        if fumble:
            multiplier = 2
        if missed:
            print(f"{self.name} misses.")
        else:
            print(f"{self.name} hits! Rolling for damage.")
            damage = roll_dice(weapon.dice, self.settings["manual_dice"] in ["always","npc_only"])
            logging.debug(f"npc_attack_with_weapon: Damage roll is {damage}, multiplier is {multiplier}")
            target_alive = target.apply_damage(multiplier * damage)
            if target_alive and damage > 2: #TODO damage of 1 would get absorbed by armour, as would 2 probably
                self.last_hit_enemy = target
            if fumble and target_alive is True:
                print(f"{target.name}'s armour is damaged")
                target.armour.reduce_tier(target, 1)

    def npc_attack_with_weapon_on_npc(self, target, weapon):
        # To handle this edge-case, assume any npc on npc attack hit automatically
        # TODO: Give NPCs placeholder defence stats to handle this better
        print(f"{self.name} (NPC) attacks {target.name} with {weapon.name}")
        multiplier = 1
        damage = multiplier * roll_dice(weapon.dice, self.settings["manual_dice"] in ["always", "npc_only"])
        target.apply_damage(damage)

    def npc_calculate_vendettas(self, attacker, damage):
        logging.debug(f"Let's figure out {self.name}'s grievances!")
        if damage > self.most_damage_taken:
            self.most_damage_taken_from = attacker
            logging.debug(f"{self.name} has a new most_damage_taken value. It is {self.most_damage_taken}, received from {self.most_damage_taken_from}")
            if self.enemy_for_life is None and 0.5 < (damage / self.max_hp):
                print(f"{self.name} lets out a mighty roar. {self.subject.capitalize()} points at {attacker.name} and declares 'You just made an enemy for life bucko!'")
                self.enemy_for_life = attacker
            else:
                logging.debug(f"{self.name} did not designate {attacker.name} as their enemy for life")

    def get_available_actions(self, allies, enemies):
        weapon_actions = []
        scroll_actions = []
        equipment_actions = []
        others = allies + enemies
        if self.settings["allow_attack_allies"]:
            targets = others
        else:
            targets = enemies
        for target in targets:
            for weapon in [self.primary_weapon, self.secondary_weapon]:
                target_weapon = ((target,), weapon)
                weapon_actions.append(target_weapon)
        if self.is_pc is True:
            if self.powers > 1 and (self.scrolls is not None):
                for scroll in self.scrolls:
                    targets, _ = scroll.list_actions(allies, enemies, self)
                    for target in targets:
                        scroll_actions.append((target, scroll))
                    #scroll_actions.append((targets, scroll))
            if self.equipment is not None:
                for item in self.equipment:
                    if item.count > 0: #Pretty embarrassed not to remember this sooner, Urm was on -13 medicine chests
                        targets, _ = item.list_actions(allies, enemies, self)
                        for target in targets:
                            equipment_actions.append((target, item))
                        #equipment_actions.append((targets, item))
        list = weapon_actions + scroll_actions + equipment_actions
        logging.debug(f"{self.name}'s list of actions: {list}")
        return list
    
    def update_statuses(self):
        for status in self.statuses.keys():
            self.statuses[status] -= 1
            if self.statuses[status] == 0:
                self.statuses.pop(status)
                logging.debug(f"{status} has been removed from {self.name}")
    
    def apply_status_effects(self):
        for status in self.statuses.keys():
            if status == "suffocating":
                print("Applying damage from suffocating status")
                roll = roll_dice("1d4", True)
                self.current_hp -= roll
                if self.current_hp <= 0:
                    print(f"{self.name} has suffocated")
                    self.alive = False
                    return False
        return self.alive


    def take_turn(self, allies, enemies):
        print("------------------------------")
        print(f"{self.name} is starting {self.possessive} turn")
        if self.am_i_dead():
            logging.warning(f"take_turn: {self.name} is supposed to be dead. Something has gone wrong here")
            print("------------------------------")
            return None
        status_results = self.apply_status_effects()
        if status_results is False:
            return None
        self.actions_this_turn += 1
        if self.actions_this_turn > 1:
            logging.debug(f"{self.name} has {self.actions_this_turn} actions to take this turn")
        for _ in range(0, self.actions_this_turn):
            logging.debug(f"take_turn: Getting list of available actions for {self.name}")
            action = self.decision_function(allies, enemies)
            print(f"{self.name} is taking an action: {action[1]} against {', '.join([target.name for target in action[0]])}")
            if isinstance(action[1], General):
                print("Using a non-scroll action")
                self.use_equipment(action)
            elif isinstance(action[1], Scroll):
                action[1].use(self, action[0])
            elif isinstance(action[1], Weapon):
                target = action[0][0] # For weapons, there should only be one target
                if target.is_pc and self.is_pc: # this might be the usecase for is_ally? #TODO: these checks should also be applied to scrolls and general above
                    logging.warning(f"take_turn: {self.name} is attacking their ally {target.name}")
                    self.make_standard_attack(action[0], action[1])
                elif (not target.is_pc) and (not self.is_pc):
                    logging.warning(f"take_turn: {self.name} is attacking their ally {target.name}")
                    self.npc_attack_with_weapon_on_npc(target, action[1])
                else:
                    logging.info(f"take_turn: {self.name} is attacking {target.name}")
                    self.make_standard_attack(target, action[1])
                self.last_target = action[0]
            print("------------------------------")
        self.actions_this_turn = 0
        # TODO: Check for status effects
        # TODO: Check if dead after status effects
        # Log results of action
        self.update_statuses()
        if self.settings["pauses"]:
            input("--Continue--")

    def __str__(self):
        return f"A character called {self.name}"
    
