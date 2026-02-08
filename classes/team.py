from classes import roll_dice
import logging


class Team:
    def __init__(self, characters, name,  manual = False):
        self.chars_starting = characters
        self.chars = characters
        self.name = name
        self.manual = manual
        #side,
        #self.side = side
        #if side == "npcs":
        #    self.leader_killed = False




    def morale_test(self):
        if len(self.chars):
            print("Running a morale test")
        for char in self.chars:
            print(f"Morale test for {char.name}")
            check = roll_dice("2d6", self.manual)
            logging.debug(f"Morale check was {check}")
            if check > char.morale:
                logging.debug(f"Morale check success for PCs")
                check = roll_dice("2d6", self.manual) #TODO flea or surrender here
                print(f"{char.name} is leaving the combat")
                self.chars = [char_left for char_left in self.chars if char_left != char]
                logging.debug(f"This many NPCs left {len(self.chars)}")
            else:
                logging.debug(f"Morale check fail for PCs")

    def update_team(self):
        self.chars = [char for char in self.chars if char.alive]
        return len(self.chars)
    
    def morale_test_check_one_third(self):
        for char in self.chars:
            if 0.33 > (char.current_hp / char.max_hp):
                self.morale_test()
