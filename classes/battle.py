from random import shuffle
from classes import roll_dice
from classes.team import Team

class Battle: # Is this one class too many? Probably, but I've got class fever over here
    def initiative(self):
        print("Roll for initiative")
        initiative_roll = roll_dice("1d6", self.manual)
        print(f"Initiative roll is {initiative_roll}")
        if initiative_roll <= 3:
            return False # PCs not going first
        else:
            return True # PCs going first
        # TODO: Individual initiative may not be RAW

    
    def __init__(self, pcs, npcs, leader = None, manual=False):
        self.manual = manual
        shuffle(pcs)
        shuffle(npcs)
        self.pcs = pcs
        self.starting_npcs = len(npcs)
        self.npcs = npcs
        self.leader = leader
        self.leader_killed = False
        self.half_elim = False
        self.one_third = False
        self.participants_starting = pcs + npcs
        self.participants = pcs + npcs
        self.round = 1

        pcs_going_first = self.initiative()
        if pcs_going_first:
            self.first_team = Team(pcs,"Team 1", manual)
            self.pc_team = self.first_team
            self.second_team = Team(npcs,"Team 2", manual)
            self.npc_team = self.second_team
        else:
            self.first_team = Team(npcs,"Team 1", manual)
            self.npc_team = self.first_team
            self.second_team = Team(pcs,"Team 2", manual)
            self.pc_team = self.second_team

        self.battle_over = False

    def run_round_side(self, on_team, off_team):
        i_team_turns_taken = 0
        i_individual_turns_taken = 0
        for char in on_team.chars:
            others = [x for x in self.participants if x != char and x.alive is True]
            if char.alive:
                target = char.start_turn(others)
                i_individual_turns_taken += 1
                if target is not None:
                    on_team.last_target = target
                if max([on_team.update_team(),off_team.update_team()]) == 0:
                    self.battle_over = True
                    break
                if (not self.leader.alive) and (not self.leader_killed):
                    print(f"The NPC leader {self.leader.name} is dead!")
                    self.leader_killed = True # So we only check this once
                    self.npc_team.morale_test()
                if (0.5 > (len(self.npcs) /self.starting_npcs) / 2) and (not self.half_elim):
                    print(f"Half the NPCs are gone")
                    self.half_elim = True # So we only check this once
                    self.npc_team.morale_test()
                self.npc_team.morale_test_check_one_third()
                    
        i_team_turns_taken += 1
        if 0 == on_team.update_team():
            self.battle_over = True
            print(f"The other team ({off_team.name}) won. Congrats to the survivor(s): {','.join([char.name for char in off_team.chars])}")
            return off_team, i_team_turns_taken, i_individual_turns_taken
        if 0 == off_team.update_team():
            self.battle_over = True
            print(f"Current round team ({on_team.name}) won. Congrats to the survivor(s): {', '.join([char.name for char in on_team.chars])}")
            return on_team, i_team_turns_taken, i_individual_turns_taken
        return None, i_team_turns_taken, i_individual_turns_taken

    def run_battle(self):
        rounds = 0
        team_turns_taken = 0
        individual_turns_taken = 0
        while self.battle_over is False:
            #TODO: This whole team term block could be a function
            winner, i_team_turns_taken, i_individual_turns_taken = self.run_round_side(self.first_team, self.second_team)
            if self.battle_over is False:
                winner, i_team_turns_taken, i_individual_turns_taken = self.run_round_side(self.second_team, self.first_team)
            team_turns_taken += i_team_turns_taken
            individual_turns_taken += i_individual_turns_taken
            rounds += 1
        print(f"There were {rounds} rounds and {individual_turns_taken} individual turns")

