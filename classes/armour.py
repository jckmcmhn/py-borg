class Armour:
    def __init__(self, config, wearer, settings):
        self.settings = settings
        self.type = config["type"]
        self.dice = config["dice"]
        if self.dice == "1d2":
            self.tier = 2
        if self.dice == "1d4":
            self.tier = 3
            if wearer.is_pc:
                wearer.abilities["agility"] += 2
                wearer.defence += 2
        if self.dice == "1d6":
            self.tier = 4
            if wearer.is_pc:
                wearer.abilities["agility"] += 4
                wearer.defence += 2
        else:
            self.tier = 1
        #TODO: What about shields. They would be a type of Reaction
        #TODO: Would be good to log if armour has been damaged

    def reduce_tier(self, wearer, tier_reduction):
        # TODO: introduce tiers to this properly
        # Per the rules, if armour is damanged, the penalties to abilities are not modified. Thankfully...
        print(f"Reducing {wearer.name}'s armour by a tier of {tier_reduction}")
        if self.dice == "1d2":
            print("Armour has been destroyed")
            wearer.armour = None #TODO: Have an unarmoured state
        elif self.dice == "1d4":
            self.dice = "1d2"
        elif self.dice == "1d6":
            self.dice = "1d4"

    def __str__(self):
        return "It's a %s armour, it provides %s damage reduction" % (self.type, self.dice)
    
    #TODO: Should there be an option to remove armour?