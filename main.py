################################################################################
# This is the main script to produce the desired results from Shakespeare plays.
# That's all I know for now. Simply pass in the filename of the Folger Digital
# Shakespeare play and let it go to work.
################################################################################

import collections
import re
import sys

from shakespeare import Play, Annotation

# Goes through every atom in the play and returns a dictionary where the
# annotations are keys, and the lines between the BEGIN and END annotations
# are the values. The annotations are transformed into a 3-tuple of the form
# (ID, Desc, Num), where ID is the identifier for the annotation such as 'GonL',
# Desc, is something like 'PLAN', or 'HOSTILE', and Num is simply a number.
def find_inter_annotations(play):
    BEGIN_ANNOTATION = '^(.+)_(.+)_(\d+)_BEGIN$'
    END_ANNOTATION = '^(.+)_(.+)_(\d+)_END$'

    inters = collections.defaultdict(list)

    active = []
    for atom in play.atoms:
        # If this atom is a begin annotation, then add it's id to the list of
        # current active annotations.
        m = re.match(BEGIN_ANNOTATION, atom.content)
        if m:
            active.append(m.groups())

            # Do not add the annotation to inters dict.
            continue
        else:
            m = re.match(END_ANNOTATION, atom.content)
            if m:
                try:
                    active.remove(m.groups())
                except ValueError:
                    pass

        # For each active annotation's id, add the current atom to the inters
        # dictionary under the id.
        for ann_id in active:
            inters[ann_id].append(atom)

    return inters

# Condense the lines of the given character from the provided lines (which may
# include lines from other characters) into sentences.
def condense_character_lines(character, lines):
    blurbs = []

    for line in lines:
        try:
            if character == line.speaker:
                blurbs.append(line.content)
        except AttributeError:
            # The given line is not dialogue, in which case we don't care about
            # it.
            pass

    return ' '.join(blurbs)

if len(sys.argv) >= 3:
    play_filename = sys.argv[1]
    ann_key_filename = sys.argv[2]
else:
    raise TypeError("Illegal number of arguments.")

# The annotation key is the file that explicitly states which annotation ids
# are associated with which characters.
annotation_key = {}
with open(ann_key_filename, 'r') as f:
    for line in f:
        items = line.rstrip().split(', ')
        annotation_key[items[0]] = (items[1], items[2])

p = Play(play_filename)
inter_anns = find_inter_annotations(p)

for ann_id, lines in inter_anns.items():
    pass
