import re

class Play(object):
    CHARACTERS_HEADER = 'Characters in the Play'
    CHARACTER_LINE = '^([A-Z]+),(.+)'

    def __init__(self, filename):
        with open(filename, 'r') as f:
            lines = map(lambda l: l.rstrip('\r\n'), f.readlines())

            # The title is the first line of the play
            self.title = lines[0]

            # Try to extract the list of characters from the intro data. This
            # is done by finding CHARACTERS_HEADER, which indicates the list of
            # characters is to follow. There is a buffer line between the header
            # line and the actual characters, so add 2. Then go through until
            # you find a blank line, at which point the list of characters is
            # over.
            try:
                # Find the lines that list out the characters.
                character_lines_start = lines.index(Play.CHARACTERS_HEADER) + 2
                for i, line in enumerate(lines[character_lines_start:]):
                    if not line:
                        character_lines_end = character_lines_start + i
                        break
                character_lines = lines[character_lines_start:character_lines_end]

                self.characters = []
                for line in character_lines:
                    m = re.match(Play.CHARACTER_LINE, line)
                    if m:
                        self.characters.append(Character(m.group(1), m.group(2)))

            except ValueError:
                # There is no character list in this case becausee there is no
                # CHARACTERS_HEADER.
                self.characters = []

class Character(object):
    def __init__(self, name, desc):
        self.name = name
        self.desc = desc
