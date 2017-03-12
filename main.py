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
# are the values.
def find_inter_annotations(play):
    BEGIN_ANNOTATION = '^(.+)_BEGIN$'
    END_ANNOTATION = '^(.+)_END$'

    inters = collections.defaultdict(list)

    active = []
    for atom in play.atoms:
        # If this atom is a begin annotation, then add it's id to the list of
        # current active annotations.
        m = re.match(BEGIN_ANNOTATION, atom.content)
        if m:
            active.append(m.group(1))

            # Do not add the annotation to inters dict.
            continue
        else:
            m = re.match(END_ANNOTATION, atom.content)
            if m:
                try:
                    active.remove(m.group(1))
                except ValueError:
                    pass

        # For each active annotation's id, add the current atom to the inters
        # dictionary under the id.
        for ann_id in active:
            inters[ann_id].append(atom)

    return inters

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

print annotation_key

p = Play(play_filename)
anns = find_inter_annotations(p)
