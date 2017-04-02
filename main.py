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

BOOTSTRAP_NUM_SAMPLES = 1000
BOOTSTRAP_SAMPLE_SIZE = 100

# Condense the PlayAtoms of the given character from the provided list (which may
# include lines from other characters) into sentences. This will return one
# continuous string of the desired characters dialogue from the given PlayAtoms.
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

def sentiments_to_percent_positive(sents):
    return sum(s > 0 for s in sents) / len(sents)

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
        annotations[items[0]] = tuple(items[1:])

p = Play(play_filename)

# Each annotation consists of the key value in the text and also a dyad or pair
# of characters involved in the betrayal.
betrayer_lines = []
victim_lines = []

# TODO: Try to think of how to get rid of this loop.
for label, info in annotations.items():
    for atom in p.atoms:
        m = re.search(label + '_HOSTILE_' + info[2]  + '_BEGIN', atom.content)
        if m:
            break

        try:
            if atom.speaker == info[0] and info[1] in atom.audience:
                betrayer_lines.append(atom.content)
            elif atom.speaker == info[1] and info[0] in atom.audience:
                victim_lines.append(atom.content)
        except AttributeError:
            # The atom was an Annotation or a StageNote and so does not have a
            # speaker or audience.
            pass

betrayer_diag = ' '.join(betrayer_lines)
victim_diag = ' '.join(victim_lines)

betrayer_sents = analysis.sentiment(nlp, betrayer_diag)
victim_sents = analysis.sentiment(nlp, victim_diag)

if len(betrayer_sents) > 0:
    p_b = sentiments_to_percent_positive(betrayer_sents)
    bootstrap_b = analysis.bootstrap(betrayer_sents,
                                     sentiments_to_percent_positive,
                                     BOOTSTRAP_NUM_SAMPLES)
else:
    p_b = 0
    bootstrap_b = 0

if len(victim_sents) > 0:
    p_v = sentiments_to_percent_positive(victim_sents)
    bootstrap_v = analysis.bootstrap(victim_sents,
                                     sentiments_to_percent_positive,
                                     BOOTSTRAP_NUM_SAMPLES)
else:
    p_v = 0
    bootstrap_v = 0

# Print out the results.
print 'Betrayer sentences: ' + str(len(betrayer_sents))
print 'Betrayer words: ' + str(len(betrayer_diag.split(' ')))
print 'Betrayer percent of sentences positive: ' + str(p_b)
print 'Betrayer bootstrapped CI (95%): ' + str(bootstrap_b[0:2])
print 'Betrayer bootstrapped SE: ' + str(bootstrap_b[2])
print 'Victim sentences: ' + str(len(victim_sents))
print 'Victim words: ' + str(len(victim_diag.split(' ')))
print 'Victim percent of sentences positive: ' + str(p_v)
print 'Victim bootstrapped CI (95%): ' + str(bootstrap_v[0:2])
print 'Victim bootstrapped SE: ' + str(bootstrap_v[2])
