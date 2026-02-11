from classes import roll_dice
import logging

class Team:
    def __init__(self, characters, name, settings, leader = None):
        self.chars_starting = characters
        self.len_chars_starting = len(characters)
        self.chars = characters
        self.name = name
        self.settings = settings
        if leader is not None: # Only applies to npc team
            self.leader = leader
            self.leader_killed = False
            self.half_elim = False
            self.one_third = False

    def morale_test(self):
        if len(self.chars):
            print("Running a morale test")
        for char in self.chars:
            print(f"Morale test for {char.name}")
            check = roll_dice("2d6", self.settings["manual_dice"] in ["always", "npc_only"])
            logging.debug(f"Morale check was {check}")
            if check > char.morale:
                logging.debug(f"Morale check success for PCs")
                check = roll_dice("2d6", self.settings["manual_dice"] in ["always", "pc_only"]) #TODO flea or surrender here
                print(f"{char.name} is leaving the combat")
                self.chars = [char_left for char_left in self.chars if char_left != char]
                logging.debug(f"This many NPCs left {len(self.chars)}")
            else:
                logging.debug(f"Morale check fail for PCs")

    def update_team(self):
        self.chars = [char for char in self.chars if char.alive]
        return len(self.chars)
    
    def morale_test_check_one_third(self):
        npcs_passed = True
        for char in self.chars:
            logging.debug(f"Checking if need morale test based on one third rule for: {char.name} {char.current_hp} {char.max_hp} {(char.current_hp / char.max_hp)}")
            if 0.33 >= (char.current_hp / char.max_hp):
                logging.debug(f"NPCs failed morale_test_check_one_third.")
                self.morale_test()
                npcs_passed = False
                self.one_third = True
                break
        if npcs_passed:
            logging.debug("NPCs passed morale_test_check_one_third")

    def morale_test_check_leader_dead(self):
        # Only call this when the leader is dead
        if not self.leader.alive:
            print(f"The NPC leader {self.leader.name} is dead!")
            self.leader_killed = True # So we only check this once
            self.morale_test()
        else:
            logging.debug("NPCs passed morale_test_check_leader_dead")

    def morale_test_check_half_elim(self):
        if 0.5 > (len(self.chars) /self.len_chars_starting) / 2:
            print(f"Half the NPCs are gone")
            self.half_elim = True # So we only check this once
            self.morale_test()
        else:
            logging.debug("NPCs passed morale_test_check_half_elim")

    def morale_test_check_all(self):
        logging.debug("Running the morale test checks")
        if not self.half_elim:
            self.morale_test_check_half_elim()
        else:
            logging.debug("Half elim test has already been done this battle")
        if not self.one_third:
            self.morale_test_check_one_third()
        else:
            logging.debug("One third test has already been done this battle")
        if not self.leader_killed:
            self.morale_test_check_leader_dead()
        else:
            logging.debug("Leader dead test has already been done this battle")
