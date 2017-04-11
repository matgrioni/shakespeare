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

from recordclass import recordclass

PlayAtom = namedtuple('PlayAtom', ['act', 'scene', 'num', 'content'])
StageNote = namedtuple('StageNote', PlayAtom._fields + ('context',))
Annotation = namedtuple('Annotation', PlayAtom._fields)
Line = namedtuple('Line', PlayAtom._fields + ('speaker', 'audience'))

Character = namedtuple('Character', ['name', 'short', 'desc'])
CharacterInfo = recordclass('CharacterInfo', ['line_count'])

class Play(object):
    ACT_HEADER = '^ACT (\d+)$'
    SCENE_HEADER = '^Scene (\d+)$'
    STAGE_NOTES = '\[(.+)\]|\[([^\]]+)|([^\[]+)\]'
    CHARACTER = '^([A-Z]+)(?![a-z]),?\s*'
    PADDING = '^=+$'

    ANNOTATION = '^\{(.+)\}$'

    CHARACTERS_SECTION_HEADER = 'Characters in the Play'
    CHARACTER_LISTING = '^(.+?)(, (.+))?$'
    CHARACTER_OF = ' OF '

    ENTER_VERBS = ['ENTER', 'ENTERS']
    EXIT_VERBS = ['EXIT', 'EXITS']
    CONJUNCTIONS = '\, +AND +|\, *'
    SING_PRONOUNS = ['HE', 'SHE']
    PLURAL_PRONOUNS = ['THEY', 'ALL']
    NEG_MODIFIERS = ['BUT']

    def __init__(self, filename):
        with open(filename, 'r') as f:
            self.raw_lines = map(lambda l: l.rstrip('\r\n'), f.readlines())
            self.atoms = []

            # The title is the first line of the file
            self.title = self.raw_lines[0]

            self._parse_characters()
            self._parse_acts()

    # A compartmentalized method to read in the list of characters at the
    # beginning of the play. These names are not used directly in the atoms list
    # however they are useful still. For example, on parsing the stage notes
    # one must be able to tell if a potential character is actually a character.
    def _parse_characters(self):
        self.characters = []
        self.character_info = {}

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
                self.character_info[short or name] = CharacterInfo(0)

            if not header_found:
                header_found = line == Play.CHARACTERS_SECTION_HEADER

    # A compartmentalized method to initialize reading the acts of the play
    # after all the introductory information.
    def _parse_acts(self):
        act = 0
        scene = 0
        line_num = 1
        last_blank_or_ann = -1

        multiline_stage_note = False
        last_stage_notes = []

        character = None
        aud = set()

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
                # If the last line was a blank, then a character name
                # might be on this line.
                start_index = 0
                if i - 1 == last_blank_or_ann:
                    m = re.match(Play.CHARACTER, line)
                    if m:
                        character = m.group(1)
                        start_index = m.end()

                line = line[start_index:]

                stage_note = None
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

                if stage_note:
                    last_stage_notes.append(stage_note)

                # If there is no more line, then it was all stage notes, so
                # don't try to look for and add character / dialogue.
                if line:
                    if last_stage_notes:
                        self._update_audience_from_stage_notes(aud, last_stage_notes)
                        del last_stage_notes[:]

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
                        l = Line(act, scene, line_num, line, character, aud.copy())
                        self.atoms.append(l)
                        try:
                            self.character_info[character].line_count += 1
                        except KeyError:
                            # This helps handle situations like O or I, at the
                            # beginning of a line where it is unclear if it is a
                            # character name.
                            pass

                        line_num += 1
                else:
                    # The line originally had content, but it was removed by
                    # stage notes. So that means that all the content was in
                    # stage notes, so that is a new line.
                    line_num += 1

    # Updates the given audience from the stage_note and last character's line.
    # Audience should be a set and stage_notes a list of StageNote tuples.
    # Essentially, ENTER_VERBS and EXIT_VERBS are looked for by sentence, and
    # any character names in these sentences are updated through the audience.
    # It is assumed that stage_notes is a list of consecutive stage_notes. This
    # is to account for multiline stage notes which are parsed into several
    # different PlayAtoms.
    def _update_audience_from_stage_notes(self, audience, stage_notes):
        content = reduce(lambda c, sn: c + sn.content, stage_notes, '')
        last_c = stage_notes[0].context

        # Enter and exit instructions come in a sentence at a time. That is the
        # assumption at least.
        for s in content.upper().split('.'):
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
                conjuncts = re.split(Play.CONJUNCTIONS, s)
                p_characters = set()

                neg = False
                for p_character in conjuncts:
                    for word in p_character.split():
                        if self._exists_character(word):
                            # If there was a negative word, it means the
                            # character is not a operand of the ENTER or EXIT
                            # operation.
                            if not neg:
                                p_characters.add(word)
                            else:
                                p_characters.remove(word)
                        elif word in Play.SING_PRONOUNS:
                            p_characters.add(stage_notes[0].context)
                        elif word in Play.PLURAL_PRONOUNS:
                            p_characters |= audience
                        elif word in Play.NEG_MODIFIERS:
                            neg = True

                if verb_type == 1:
                    audience |= p_characters
                elif verb_type == 2:
                    audience -= p_characters

    def _exists_character(self, p_name):
        u = p_name.upper()
        return reduce(lambda flag, c:
                      flag or u == c.name or u == c.short,
                      self.characters, False)
