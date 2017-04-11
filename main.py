################################################################################
# This is the main script to produce the desired results from Shakespeare plays.
# That's all I know for now. Simply pass in the filename of the Folger Digital
# Shakespeare play and let it go to work.
################################################################################

from __future__ import division

import collections
from functools import partial
import itertools
import re
import sys

import numpy
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

def non_hostile_choices_left(hostile_dyads, names):
    for dyad in itertools.combinations(names, 2):
        rev = (names[1], names[1])
        if dyad in hostile_dyads or rev in hostile_dyads:
            return True

    return False

def sentiments_to_percent_positive(sents):
    return sum(s > 0 for s in sents) / len(sents)

def valid_non_hostile(play, c_name):
    return play.character_info[c_name].line_count > 50

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

p = Play(play_filename)
nlp = StanfordCoreNLP('http://localhost:9000')

# The annotation key is the file that explicitly states which annotation ids
# are associated with which characters. These are all the hostile dyads that
# will be tracked in the play.
hostile_dyads = {}
with open(ann_key_filename, 'r') as f:
    for line in f:
        items = line.rstrip().split(', ')
        hostile_dyads[tuple(items[1:3])] = (items[0], items[3])

# Now we have to find out all the non-hostile dyads and arbitrairly assign a
# betrayer and victim to them.
# TODO: Very inefficient...
names = filter(partial(valid_non_hostile, p), map(lambda c: c.short or c.name, p.characters))
non_hostile_dyads = []
while non_hostile_choices_left(hostile_dyads, names):
    choices = tuple(numpy.random.choice(names, size=2, replace=False))
    rev_choices = (choices[1], choices[0])

    while choices in hostile_dyads or rev_choices in hostile_dyads:
        choices = tuple(numpy.random.choice(names, size=2, replace=False))
        rev_choices = (choices[1], choices[0])

    names.remove(choices[0])
    names.remove(choices[1])

    non_hostile_dyads.append(choices)

print non_hostile_dyads

# Each annotation consists of the key value in the text and also a dyad or pair
# of characters involved in the betrayal.
betrayer_lines = []
victim_lines = []
arb_betrayer_lines = []
arb_victim_lines = []

for atom in p.atoms:
    hostile_pair_found = False
    valid_line = True

    for dyad, info in hostile_dyads.items():
        if info:
            m = re.search(info[0] + '_HOSTILE_' + info[1]  + '_BEGIN', atom.content)
            if m:
                del hostile_dyads[dyad]
                continue

            try:
                if dyad[0] == atom.speaker and dyad[1] in atom.audience:
                    betrayer_lines.append(atom.content)
                    hostile_pair_found = True
                elif dyad[1] == atom.speaker and dyad[0] in atom.audience:
                    victim_lines.append(atom.content)
                    hostile_pair_found = True
            except AttributeError:
                # This line is not a Line instance, but an Annotation or
                # StageNote so we can ignore it.
                valid_line = False

    if not hostile_pair_found and valid_line:
        for dyad in non_hostile_dyads:
            betrayer = dyad[0]
            victim = dyad[1]
            if betrayer == atom.speaker and victim in atom.audience:
                arb_betrayer_lines.append(atom.content)
            elif victim == atom.speaker and betrayer in atom.audience:
                arb_victim_lines.append(atom.content)

betrayer_diag = ' '.join(betrayer_lines)
victim_diag = ' '.join(victim_lines)
arb_betrayer_diag = ' '.join(arb_betrayer_lines)
arb_victim_diag = ' '.join(arb_victim_lines)

betrayer_sents = analysis.sentiment(nlp, betrayer_diag)
victim_sents = analysis.sentiment(nlp, victim_diag)
arb_betrayer_sents = analysis.sentiment(nlp, arb_betrayer_diag, 17000)
arb_victim_sents = analysis.sentiment(nlp, arb_victim_diag, 17000)

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

if len(arb_betrayer_sents) > 0:
    p_ab = sentiments_to_percent_positive(arb_betrayer_sents)
    bootstrap_ab = analysis.bootstrap(arb_betrayer_sents,
                                     sentiments_to_percent_positive,
                                     BOOTSTRAP_NUM_SAMPLES)
else:
    p_ab = 0
    bootstrap_ab = (0, 0, 0)

if len(arb_victim_sents) > 0:
    p_av = sentiments_to_percent_positive(arb_victim_sents)
    bootstrap_av = analysis.bootstrap(arb_victim_sents,
                                     sentiments_to_percent_positive,
                                     BOOTSTRAP_NUM_SAMPLES)
else:
    p_av = 0
    bootstrap_av = (0, 0, 0)

# Print out the results.
print 'Hostile dyad analysis'
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
print
print 'Non hostile dyad analysis'
print 'Betrayer sentences: ' + str(len(arb_betrayer_sents))
print 'Betrayer words: ' + str(len(arb_betrayer_diag.split(' ')))
print 'Betrayer percent of sentences positive: ' + str(p_ab)
print 'Betrayer bootstrapped CI (95%): ' + str(bootstrap_ab[0:2])
print 'Betrayer bootstrapped SE: ' + str(bootstrap_ab[2])
print 'Victim sentences: ' + str(len(arb_victim_sents))
print 'Victim words: ' + str(len(arb_victim_diag.split(' ')))
print 'Victim percent of sentences positive: ' + str(p_av)
print 'Victim bootstrapped CI (95%): ' + str(bootstrap_av[0:2])
print 'Victim bootstrapped SE: ' + str(bootstrap_av[2])
