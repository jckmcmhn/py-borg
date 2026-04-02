import argparse
import logging
import yaml

from classes.character import Character
from classes.battle import Battle


parser = argparse.ArgumentParser()
parser.add_argument("-m", "--manual_dice", help = "One of 'never', 'pc_only', 'npc_only', 'always' and 'pauses'", default="never")
parser.add_argument("-l", "--log", help = "Log level", default="info")
parser.add_argument("-a", "--allow_attack_allies", default="false")
args = parser.parse_args()


if args.log.lower() == "info":
    ll = logging.INFO
elif args.log.lower() == "debug":
    ll = logging.DEBUG
elif args.log.lower() == "warning":
    ll = logging.WARNING

logging.basicConfig(
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
    level=ll)

MANUAL_DICE_ROLLS = args.manual_dice
ALLOW_ATTACK_ALLIES = args.allow_attack_allies.lower() == "true" #TODO: Eventually need a setting where it's allowed but the game crashes or makes more of a fuss if it happens


settings = {
    "manual_dice": MANUAL_DICE_ROLLS, # one of "never", "pc_only", "npc_only", "always" and "pauses" #TODO: Convert these to integers for better performance
    "allow_attack_allies": ALLOW_ATTACK_ALLIES,
    "mod_damage": 0,
    "to_hit": 0,
    "to_dodge": 0,
    "pauses": False
}


print("Starting the game")
print(f"MANUAL_DICE_ROLLS is {MANUAL_DICE_ROLLS}\n\n")
print(f"ALLOW_ATTACK_ALLIES is {ALLOW_ATTACK_ALLIES}\n\n")
print("Enter 0 to skip manual dice rolls if needed")

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
urvarg = Character(config, settings)

with open("configs/pc_sample_2.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.SafeLoader)
rolf = Character(config, settings)

with open("configs/pc_sample_scroll.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.SafeLoader)
urm = Character(config, settings)
urm2 = Character(config, settings, "urm2")

with open("configs/npc_sample.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.SafeLoader)
big_guy = Character(config, settings)
big_guy2 = Character(config, settings, "Less big")

with open("configs/npc_sample_2.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.SafeLoader)
little_guy = Character(config, settings)
little_guy_2 = Character(config, settings, "The Other Little Guy")
little_guy_3 = Character(config, settings, "YALG")
little_guy_4 = Character(config, settings, "YALG2")


#battle = Battle([rolf, urvarg, urm],[big_guy, little_guy, little_guy_2, little_guy_3, little_guy_4], big_guy, self.settings["manual_dice"])
#battle = Battle([rolf, urm],[big_guy, little_guy, little_guy_2], settings, big_guy)
battle = Battle([rolf, urm],[big_guy], settings, big_guy)
battle.run_battle()
