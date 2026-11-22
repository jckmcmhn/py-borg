from random import shuffle
from classes import roll_dice
from classes.team import Team
import logging

class Battle: # Is this one class too many? Probably, but I've got class fever over here
    def __init__(self, pcs, npcs, settings, leader = None):
        self.settings = settings
        shuffle(pcs)
        shuffle(npcs)
        self.pcs = pcs
        self.npcs = npcs
        self.leader = leader
        self.participants_starting = pcs + npcs
        self.participants = pcs + npcs
        self.round = 1

        pcs_going_first = self.initiative()
        if pcs_going_first:
            self.first_team = Team(pcs,"Team 1", self.settings)
            self.pc_team = self.first_team
            self.second_team = Team(npcs,"Team 2", self.settings, leader)
            self.npc_team = self.second_team
        else:
            self.first_team = Team(npcs,"Team 1", self.settings, leader)
            self.npc_team = self.first_team
            self.second_team = Team(pcs,"Team 2", self.settings)
            self.pc_team = self.second_team

        self.battle_over = False

    def initiative(self):
        print("Roll for initiative")
        initiative_roll = roll_dice("1d6", self.settings["manual_dice"] in ["always", "pc_only"])
        print(f"Initiative roll is {initiative_roll}")
        if initiative_roll <= 3:
            return False # PCs not going first
        else:
            return True # PCs going first
        # TODO: Individual initiative may not be RAW

    def run_round_side(self, on_team, off_team):
        print(f"The team of {', '.join([ char.name for char in on_team.chars])} is taking their go")
        i_individual_turns_taken = 0
        for char in on_team.chars:
            allies = [x for x in on_team.chars if x != char and x.alive is True]
            if char.alive:
                action_type = char.take_turn(allies, off_team.chars)
                i_individual_turns_taken += 1

                if min([on_team.update_team(),off_team.update_team()]) == 0:
                    self.battle_over = True
                    break
                
                self.npc_team.morale_test_check_all()
                
                if min([on_team.update_team(),off_team.update_team()]) == 0:
                    self.battle_over = True
                    break

                if action_type == "healing":
                    logging.debug(f"{off_team.name} have witnessed {char.name} from {on_team.name} attempt healing")
                    off_team.update_enemy_healers_for_team(char)
                    
        if 0 == on_team.update_team() and 0 == off_team.update_team():
            print("It's a draw")
        elif 0 == len(on_team.chars):
            self.battle_over = True
            if len(off_team.chars) == 1:
                survivor_survivors = "survivor"
            else:
                survivor_survivors = "survivors"
            print(f"\nThe other team ({off_team.name}) won. Congrats to the {survivor_survivors}: {', '.join([char.name for char in off_team.chars])}!\n")
            return off_team, i_individual_turns_taken
        elif 0 == len(off_team.chars):
            self.battle_over = True
            if len(on_team.chars) == 1:
                survivor_survivors = "survivor"
            else:
                survivor_survivors = "survivors"
            print(f"\nCurrent turn team ({on_team.name}) won. Congrats to the {survivor_survivors}: {', '.join([char.name for char in on_team.chars])}!\n")
            return on_team, i_individual_turns_taken
        return None, i_individual_turns_taken

    def run_battle(self):
        complete_rounds = 0
        individual_turns_taken = 0
        second_team_individual_turns_taken = 0 # Set default values in the unlikely event that the first team wins on their first turn
        while self.battle_over is False:
            print(f"Starting round {complete_rounds + 1}")
            winner, first_team_individual_turns_taken = self.run_round_side(self.first_team, self.second_team)
            #self.first_team.team_status()
            if self.battle_over is False: # Only do the second teams turn of the round if the first team didn't win on their turn
                winner, second_team_individual_turns_taken = self.run_round_side(self.second_team, self.first_team)
                #self.second_team.team_status()
            individual_turns_taken += first_team_individual_turns_taken + second_team_individual_turns_taken
            complete_rounds += 1
            if self.battle_over is False:
                print(f"End of round {complete_rounds}")
                print("------------------------------")

        if winner is not None:
            logging.debug(f"Clearing statuses from winning team ({winner.name})")
            for char in winner.chars:
                if char.statuses != {}: #TODO: Outside of debugging, this check is probably not needed
                    #TODO: Should all statuses be cleared automatically, check the rules
                    logging.debug(f"{char.name} had these statuses which will be cleared: {char.statuses}")
                    char.statuses = {}
        if complete_rounds == 1:
            round_string = "round"
            were_was = "was"
        else:
            round_string = "rounds"
            were_was = "were"
        if individual_turns_taken == 1:
            individual_turns_string = "turn"
        else:
            individual_turns_string = "turns"
        print(f"There {were_was} {complete_rounds} complete {round_string} and {individual_turns_taken} individual character {individual_turns_string}\n")
        #print(f"Final state summary: {winner.chars[0].get_obs('admin')}") # Get the first survivor, get their admin level obs

        if winner is not None:
            logging.debug("Final state summary")
            for char in winner.chars:
                logging.debug(char.name)
                logging.debug(f"Final state summary: {char.get_obs('friends')}") # Get the first survivor, get their admin level obs

