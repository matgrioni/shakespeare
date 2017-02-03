from collections import namedtuple
import re

Line = namedtuple('Line', ['act', 'scene', 'line', 'speaker', 'audience'])

class Play(object):
    ACT_HEADER = '^ACT (\d+)$'
    SCENE_HEADER = '^Scene (\d+)$'
    # TODO: Must account for multiline stage notes still.
    STAGE_NOTES = '\[(.+)\]'
    CHARACTER = '^[A-Z]+\s'
    PADDING = '^=+$'

    def __init__(self, filename):
        with open(filename, 'r') as f:
            self.raw_lines = map(lambda l: l.rstrip('\r\n'), f.readlines())

            # The title is the first line of the file
            self.title = self.raw_lines[0]

            act = 0
            scene = 0
            line_num = 0
            last_blank = -1
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

                # Do not bother if the line is a padded line or a blank line.
                if re.match(Play.PADDING, line):
                    continue

                if not line:
                    last_blank = i
                    continue

                # A line for the act and for the scene has been found and this
                # line is not a padding line or a blank line, so it is a content
                # line to be added.
                if act >= 1 and scene >= 1:
                    line_num += 1
                    print line
