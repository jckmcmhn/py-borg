import uuid

class Weapon:
    def __init__(self, config = {}, manual=False):
        self.manual = manual
        self.name = config.get("name","Unarmed")
        self.type = config.get("type","melee")
        self.dice = config.get("damage","1d2")
        self.dr = config.get("dr",12)
        self.category = config.get("category","unarmed")
        self.rank = config.get("rank",False)
        self.id = uuid.uuid4()        

    def __str__(self):
        return "It's a %s called %s it deals %s" % (self.category, self.name, self.damage)