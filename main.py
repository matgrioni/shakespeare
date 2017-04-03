################################################################################
# This is the main script to produce the desired results from Shakespeare plays.
# That's all I know for now. Simply pass in the filename of the Folger Digital
# Shakespeare play and let it go to work.
################################################################################

from __future__ import division

import collections
import itertools
import re
import sys

from pycorenlp import StanfordCoreNLP

import analysis
from shakespeare import Play

BOOTSTRAP_NUM_SAMPLES = 5000
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
        annotations[tuple(items[1:3])] = (items[0], items[3])

p = Play(play_filename)

# Each annotation consists of the key value in the text and also a dyad or pair
# of characters involved in the betrayal.
betrayer_lines = []
victim_lines = []
non_hostile_lines = []

names = map(lambda c: c.short or c.name, p.characters)
current_dyads = dict.fromkeys(itertools.permutations(names, 2))

for atom in p.atoms:
    hostile_pair_found = False
    valid_line = True

    for dyad, _ in current_dyads.items():
        try:
            info = annotations[dyad]
            m = re.search(info[0] + '_HOSTILE_' + info[1]  + '_BEGIN', atom.content)
            if m:
                del current_dyads[dyad]
                continue

            try:
                if dyad[0] == atom.speaker and dyad[1] in atom.audience:
                    betrayer_lines.append(atom.content)
                    hostile_pair_found = True
                if dyad[1] == atom.speaker and dyad[0] in atom.audience:
                    victim_lines.append(atom.content)
                    hostile_pair_found = True
            except AttributeError:
                # This line is not a Line instance, but an Annotation or
                # StageNote so we can ignore it.
                valid_line = False
        except KeyError:
            pass

    if not hostile_pair_found and valid_line:
        non_hostile_lines.append(atom.content)

betrayer_diag = ' '.join(betrayer_lines)
victim_diag = ' '.join(victim_lines)
non_hostile_diag = ' '.join(non_hostile_lines)

betrayer_sents = analysis.sentiment(nlp, betrayer_diag)
victim_sents = analysis.sentiment(nlp, victim_diag)
non_hostile_sents = analysis.sentiment(nlp, non_hostile_diag, 17000)

if len(betrayer_sents) > 0:
    p_b = sentiments_to_percent_positive(betrayer_sents)
    bootstrap_b = analysis.bootstrap(betrayer_sents,
                                     sentiments_to_percent_positive,
                                     BOOTSTRAP_NUM_SAMPLES)
else:
    p_b = 0
    bootstrap_b = (0, 0, 0)

if len(victim_sents) > 0:
    p_v = sentiments_to_percent_positive(victim_sents)
    bootstrap_v = analysis.bootstrap(victim_sents,
                                     sentiments_to_percent_positive,
                                     BOOTSTRAP_NUM_SAMPLES)
else:
    p_v = 0
    bootstrap_v = (0, 0, 0)

if len(non_hostile_sents) > 0:
    p_nh = sentiments_to_percent_positive(non_hostile_sents)
    bootstrap_nh = analysis.bootstrap(non_hostile_sents,
                                      sentiments_to_percent_positive,
                                      BOOTSTRAP_NUM_SAMPLES)
else:
    p_nh = 0
    bootstrap_nh = (0, 0, 0)

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
print 'Non hostile sentences: ' + str(len(non_hostile_sents))
print 'Non hostile words: ' + str(len(non_hostile_diag.split(' ')))
print 'Non hostile percent of sentences positive: ' + str(p_nh)
print 'Non hostile bootstrapped CI (95%): ' + str(bootstrap_nh[0:2])
print 'Non hostile bootstrapped SE: ' + str(bootstrap_nh[2])
