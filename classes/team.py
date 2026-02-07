class Team:
    def __init__(self, characters, name):
        self.chars_starting = characters
        self.chars = characters
        self.name = name

    def update_team(self):
        self.chars = [char for char in self.chars if char.alive]
        return len(self.chars)