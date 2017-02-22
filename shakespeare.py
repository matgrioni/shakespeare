################################################################################
#
# Python module to help analyze shakeseare plays from the Folger online library.
# Right now this is going off the formatting from King Lear from this online
# library and makes various assumptions based on this text. Your mileage may
# vary with other selections from this library.
#
################################################################################

from collections import namedtuple
import re

PlayAtom = namedtuple('PlayAtom', ['act', 'scene', 'num', 'content'])
StageNote = namedtuple('StageNote', PlayAtom._fields + ('context',))
Annotation = namedtuple('Annotation', PlayAtom._fields)
Line = namedtuple('Line', PlayAtom._fields + ('speaker', 'audience'))

Character = namedtuple('Character', ['name', 'short', 'desc'])

class Play(object):
    ACT_HEADER = '^ACT (\d+)$'
    SCENE_HEADER = '^Scene (\d+)$'
    STAGE_NOTES = '\[(.+)\]|\[([^\]]+)|([^\[]+)\]'
    CHARACTER = '^([A-Z]+),?\s*'
    PADDING = '^=+$'

    ANNOTATION = '^\{(.+)\}$'

    CHARACTERS_SECTION_HEADER = 'Characters in the Play'
    CHARACTER_LISTING = '^(.+?)(, (.+))?$'
    CHARACTER_OF = ' OF '

    ENTER_VERBS = ['ENTER', 'ENTERS']
    EXIT_VERBS = ['EXIT', 'EXITS']
    CONJUNCTIONS = '\, AND +|\, +'

    def __init__(self, filename):
        with open(filename, 'r') as f:
            self.raw_lines = map(lambda l: l.rstrip('\r\n'), f.readlines())
            self.atoms = []

            # The title is the first line of the file
            self.title = self.raw_lines[0]

            self._parseCharacters()
            self._parseActs()

    # A compartmentalized method to read in the list of characters at the
    # beginning of the play. These names are not used directly in the atoms list
    # however they are useful still. For example, on parsing the stage notes
    # one must be able to tell if a potential character is actually a character.
    def _parseCharacters(self):
        self.characters = []

        header_found = False
        for line in self.raw_lines:
            # Once we've reached the character section, and there is a blank
            # line, the character section is over.
            if header_found and not re.match(Play.PADDING, line):
                if not line:
                    break

                m = re.match(Play.CHARACTER_LISTING, line)
                name = m.group(1)
                short = ''
                desc = m.group(3)

                if Play.CHARACTER_OF in name:
                    idx = name.index(Play.CHARACTER_OF)
                    short = name[idx + len(Play.CHARACTER_OF):]

                self.characters.append(Character(name, short, desc))

            if not header_found:
                header_found = line == Play.CHARACTERS_SECTION_HEADER

    # A compartmentalized method to initialize reading the acts of the play
    # after all the introductory information.
    def _parseActs(self):
        act = 0
        scene = 0
        line_num = 1
        last_blank_or_ann = -1
        multiline_stage_note = False
        character = None
        for i, line in enumerate(self.raw_lines):
            m = re.match(Play.ACT_HEADER, line)
            if m:
                act = int(m.group(1))
                character = None
                continue

            m = re.match(Play.SCENE_HEADER, line)
            if m:
                scene = int(m.group(1))
                line_num = 1
                character = None
                continue

            # Do not bother if the line is a padded line.
            if re.match(Play.PADDING, line):
                continue

            # If the line is a blank line, then keep track of it and there's
            # nothing else for us to do.
            if not line:
                last_blank_or_ann = i
                continue

            # A line for the act and for the scene has been found and this
            # line is not a padding line or a blank line, so it is a content
            # line to be added.
            if act >= 1 and scene >= 1:
                m = re.search(Play.STAGE_NOTES, line)
                if m:
                    if m.group(1):
                        stage_note = StageNote(act, scene, line_num, m.group(1), character)
                        self.atoms.append(stage_note)
                    elif m.group(2):
                        stage_note = StageNote(act, scene, line_num, m.group(2), character)
                        self.atoms.append(stage_note)

                        multiline_stage_note = True
                    elif m.group(3):
                        stage_note = StageNote(act, scene, line_num, m.group(3), character)
                        self.atoms.append(stage_note)

                        multiline_stage_note = False

                    line = line[:m.start()] + line[m.end():]
                elif multiline_stage_note:
                    # If the stage note spans 3 lines or more, than the
                    # second line has no annotation to show that it is a
                    # stage note. So we keep track of if a stage note has
                    # been opened but not closed yet. In this case this
                    # entire line is part of that stage note.
                    stage_note = StageNote(act, scene, line_num, line, character)
                    self.atoms.append(stage_note)
                    line = ''

                # If there is no more line, then it was all stage notes, so
                # don't try to look for and add character / dialogue.
                if line:
                    # Check if there are annotations on this line, in which case
                    # it is the only thing on the line and we do not have to
                    # look for dialogue.
                    m = re.match(Play.ANNOTATION, line)
                    if m:
                        a = Annotation(act, scene, line_num, m.group(1))
                        self.atoms.append(a)
                        line_num += 1
                        last_blank_or_ann = i
                    else:
                        # If the last line was a blank, then a character name
                        # might be on this line.
                        start_index = 0
                        if i - 1 == last_blank_or_ann:
                            m = re.match(Play.CHARACTER, line)
                            if m:
                                character = m.group(1)
                                start_index = m.end()

                        # Get the dialogue after the characters name and if
                        # there is any, then add it to the lines.
                        dialogue = line[start_index:]
                        if dialogue:
                            l = Line(act, scene, line_num, dialogue, character, None)
                            self.atoms.append(l)

                            line_num += 1
                else:
                    # The line originally had content, but it was removed by
                    # stage notes. So that means that all the content was in
                    # stage notes, so that is a new line.
                    line_num += 1

    # Updates the given audience from the stage_note and last character's line.
    # Audience should be a set and stage_note a string. Essentially, ENTER_VERBS
    # and EXIT_VERBS are looked for by sentence, and any character names in
    # in these sentences are updated through the audience.
    def _updateAudienceFromStageNote(self, audience, stage_note):
        # Enter and exit instructions come in a sentence at a time. That is the
        # assumption at least.
        for s in stage_note.upper().split('.'):
            verb_type = 0

            # Search for enter type verbs and keep track of where it happens
            # in the sentence. Assume that only one of these verbs occurs per
            # sentence.
            f_verb = reduce(lambda f, v:
                            v if v in s and (not f or len(v) > len(f)) else f,
                            Play.ENTER_VERBS, None)
            if f_verb:
                verb_type = 1
                idx = s.index(f_verb)
            else:
                # Same thing as above but for exit type verbs.
                f_verb = reduce(lambda f, v:
                                v if v in s and (not f or len(v) > len(f)) else f,
                                Play.EXIT_VERBS, None)
                if f_verb:
                    verb_type = 2
                    idx = s.index(f_verb)

            if verb_type != 0:
                s = (s[:idx] + s[idx + len(f_verb):]).strip()
                conjuncts = set(re.split(Play.CONJUNCTIONS, s))
                p_characters = set()

                for p_character in conjuncts:
                    for word in p_character.split():
                        if self._existsCharacter(word):
                            p_characters.add(word)

                if verb_type == 1:
                    characters |= p_characters
                elif verb_type == 2:
                    characters -= p_characters

    def _existsCharacter(self, p_name):
        u = p_name.upper()
        return reduce(lambda flag, c:
                      flag or u == c.name or u == c.short,
                      self.characters, False)
