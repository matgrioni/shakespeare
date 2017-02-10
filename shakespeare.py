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
Line = namedtuple('Line', PlayAtom._fields + ('speaker', 'audience'))

class Play(object):
    ACT_HEADER = '^ACT (\d+)$'
    SCENE_HEADER = '^Scene (\d+)$'
    STAGE_NOTES = '\[(.+)\]|\[([^\]]+)|([^\[]+)\]'
    CHARACTER = '^([A-Z]+),?\s*'
    PADDING = '^=+$'

    def __init__(self, filename):
        with open(filename, 'r') as f:
            self.raw_lines = map(lambda l: l.rstrip('\r\n'), f.readlines())
            self.atoms = []

            # The title is the first line of the file
            self.title = self.raw_lines[0]

            act = 0
            scene = 0
            line_num = 1
            last_blank = -1
            multiline_stage_note = False
            character = ''
            for i, line in enumerate(self.raw_lines):
                m = re.match(Play.ACT_HEADER, line)
                if m:
                    act = int(m.group(1))
                    continue

                m = re.match(Play.SCENE_HEADER, line)
                if m:
                    scene = int(m.group(1))
                    line_num = 1
                    continue

                # Do not bother if the line is a padded line.
                if re.match(Play.PADDING, line):
                    continue

                # If the line is a blank line, then keep track of it.
                if not line:
                    last_blank = i
                    continue

                # A line for the act and for the scene has been found and this
                # line is not a padding line or a blank line, so it is a content
                # line to be added.
                if act >= 1 and scene >= 1:
                    m = re.search(Play.STAGE_NOTES, line)
                    if m:
                        if m.group(1):
                            stage_note = PlayAtom(act, scene, line_num, m.group(1))
                            self.atoms.append(stage_note)
                        elif m.group(2):
                            stage_note = PlayAtom(act, scene, line_num, m.group(2))
                            self.atoms.append(stage_note)

                            multiline_stage_note = True
                        elif m.group(3):
                            stage_note = PlayAtom(act, scene, line_num, m.group(3))
                            self.atoms.append(stage_note)

                            multiline_stage_note = False

                        line = line[:m.start()] + line[m.end():]
                    elif multiline_stage_note:
                        # If the stage note spans 3 lines or more, than the
                        # second line has no annotation to show that it is a
                        # stage note. So we keep track of if a stage note has
                        # been opened but not closed yet. In this case this
                        # entire line is part of that stage note.
                        stage_note = PlayAtom(act, scene, line_num, line)
                        self.atoms.append(stage_note)
                        line = ''

                    if line:
                        # If the last line was a blank, then a character name
                        # might be on this line.
                        start_index = 0
                        if i - 1 == last_blank:
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
