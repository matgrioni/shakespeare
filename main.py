################################################################################
# This is the main script to produce the desired results from Shakespeare plays.
# That's all I know for now. Simply pass in the filename of the Folger Digital
# Shakespeare play and let it go to work.
################################################################################

from __future__ import division

import collections
import re
import sys

from pycorenlp import StanfordCoreNLP

import analysis
from shakespeare import Play

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

################################################################################
#
# Main script.
#
################################################################################

if len(sys.argv) >= 3:
    play_filename = sys.argv[1]
    ann_key_filename = sys.argv[2]
else:
    raise TypeError('Illegal number of arguments.')

nlp = StanfordCoreNLP('http://localhost:9000')

# The annotation key is the file that explicitly states which annotation ids
# are associated with which characters.
annotations = {}
with open(ann_key_filename, 'r') as f:
    for line in f:
        items = line.rstrip().split(', ')
        annotations[items[0]] = (items[1], items[2])

p = Play(play_filename)

# Each annotation consists of the key value in the tex and also a dyad or pair
# of characters involved in the betrayal.
for key, dyad in annotations.items():
    prior_betrayal = []
    for atom in p.atoms:
        m = re.search(key + '_HOSTILE_.+_BEGIN', atom.content)
        if m:
            break

        try:
            if (atom.speaker == dyad[0] and dyad[1] in atom.audience) or (atom.speaker == dyad[1] and dyad[0] in atom.audience):
                prior_betrayal.append(atom)
        except AttributeError:
            # The atom was an Annotation or a StageNote and so does not have a
            # speaker or audience.
            pass

    betrayer_diag = condense_character_lines(dyad[0], prior_betrayal)
    victim_diag = condense_character_lines(dyad[1], prior_betrayal)

    betrayer_sent = analysis.sentiment(nlp, betrayer_diag)
    victim_sent = analysis.sentiment(nlp, victim_diag)

    if len(betrayer_sent) > 0:
        p_b = sum(s > 0 for s in betrayer_sent) / len(betrayer_sent)
    else:
        p_b = 0

    if len(victim_sent) > 0:
        p_v = sum(s > 0 for s in victim_sent) / len(victim_sent)
    else:
        p_v = 0

    print key
    print 'Betrayer sentences: ' + str(len(betrayer_sent))
    print 'Betrayer words: ' + str(len(betrayer_diag.split(' ')) - 1)
    print 'Betrayer percent positive: ' + str(p_b)
    print 'Victim sentences: ' + str(len(victim_sent))
    print 'Victim words: ' + str(len(victim_diag.split(' ')) - 1)
    print 'Victim percent positive: ' + str(p_v)
    print
