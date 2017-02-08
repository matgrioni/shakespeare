################################################################################
#
# Python module to help analyze shakeseare plays from the Folger online library.
#
################################################################################

from collections import namedtuple
import re

Line = namedtuple('Line', ['act', 'scene', 'num', 'speaker', 'audience', 'content'])

class Play(object):
    ACT_HEADER = '^ACT (\d+)$'
    SCENE_HEADER = '^Scene (\d+)$'
    STAGE_NOTES = '.*\[(.+)\].*|.*\[([^\]]+)|([^\[]+)\].*'
    CHARACTER = '^([A-Z]+),?\s*'
    PADDING = '^=+$'

    def __init__(self, filename):
        with open(filename, 'r') as f:
            self.raw_lines = map(lambda l: l.rstrip('\r\n'), f.readlines())
            self.lines = []

            # The title is the first line of the file
            self.title = self.raw_lines[0]

            act = 0
            scene = 0
            line_num = 0
            last_blank = -1
            character = ''
            for i, line in enumerate(self.raw_lines):
                m = re.match(Play.ACT_HEADER, line)
                if m:
                    act = int(m.group(1))
                    continue

                m = re.match(Play.SCENE_HEADER, line)
                if m:
                    scene = int(m.group(1))
                    line_num = 0
                    continue

                # Do not bother if the line is a padded line.
                if re.match(Play.PADDING, line):
                    continue

                # If the line is a blank line, then write it.
                if not line:
                    last_blank = i
                    continue

                # A line for the act and for the scene has been found and this
                # line is not a padding line or a blank line, so it is a content
                # line to be added.
                if act >= 1 and scene >= 1:
                    # Prune stage notes out for now
                    m = re.search(Play.STAGE_NOTES, line)
                    if m:
                        line = line[:m.start()] + line[m.end():]

                    if line:
                        line_num += 1

                        # If the last line was a blank, then a character name
                        # might be on this line.
                        start_index = 0
                        if i - 1 == last_blank:
                            m = re.match(Play.CHARACTER, line)
                            if m:
                                character = m.group(1)
                                start_index = len(m.group())

                        # Get the dialogue after the characters name and if
                        # there is any, then add it to the lines.
                        dialogue = line[start_index:]
                        if dialogue:
                            l = Line(act, scene, line_num, character, None, dialogue)
                            self.lines.append(l)
