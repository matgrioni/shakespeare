import re

class Play(object):
    def __init__(self, filename):
        with open(filename, 'r') as f:
            lines = map(lambda l: l.rstrip('\r\n'), f.readlines())

            # The title is the first line of the play
            self.title = lines[0]

class Character(object):
    def __init__(self, name, desc):
        self.name = name
        self.desc = desc
