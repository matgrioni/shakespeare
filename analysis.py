################################################################################
#
# A wrapper around the different analysis that will be done such as sentiment
# analysis, politeness analysis, and talkativeness analysis. This module will
# also include statistical analysis. Most of these require third parties
# libraries whose boilerplate code will be handled here.
#
################################################################################

from __future__ import division
import math

import numpy

# Provide the StanfordCoreNLP object and the text to annotate. A list of scores
# will be returned. The location of the score corresponds to the sentence in the
# original sentence. The scores are scalars with the following meanings:
#    1: Positive
#    0: Neutral
#   -1: Negative
def sentiment(nlp, text):
    result = nlp.annotate(text, properties={
        'annotators':   'sentiment',
        'outputFormat': 'json'
    })

    return map(_get_scalar_sentiment, result['sentences'])

# Internal method to return a 1, 0, or -1 based the result from the Stanford
# Core NLP server. The sentence object is a json object that comes from each
# item in the sentences field in the server result.
def _get_scalar_sentiment(sentence):
    sentiment = int(sentence['sentimentValue'])

    if sentiment > 2:
        return 1
    elif sentiment < 2:
        return -1
    else:
        return 0

# Runs an estimated confidence interval and SE from the given values. For any
# type of objects a confidence interval will be returned as the first two
# elements. ~2.5% of samples had a value less than the first element, and ~2.5%
# of the samples had an value greater than the second element. You are
# guaranteed at maximum these percentages. The actual percentages may be less
# depending on truncation of decimals. Since the objects can be any arbitrary
# objects, a callback, sample_value must be provided that accepts a sample and
# returns a scalar value. This is the value that is used to compare samples. The
# sample_size is used for the size of the bootstrapped samples, but if the value
# is omitted or less than 0, then the sample size is the size of the original
# list of objects.
#
# For example if the sample_value function returns the average of the sample,
# then this method returns the variance of objects average. If sample_value
# calculates the percentage of values greater than 0, then this method returns
# the variance of the percentage of values greater than 0 in the entire objects
# list.
#
# The return tuple is structured as follows:
#   (min_ci, max_ci, se)
# Note that these values are bootstraped estimates.
def bootstrap(objects, sample_value, num_samples, sample_size=-1):
    if sample_size < 0:
        sample_size = len(objects)
    samples = numpy.random.choice(objects, size=(num_samples, sample_size),
                                  replace=True).tolist()

    values = map(sample_value, samples)
    values.sort()

    sd = _sd(values)

    lower = int(num_samples * 0.025)
    upper = min(int(math.ceil(num_samples * 0.975)) - 1, num_samples - 1)

    return (values[lower], values[upper], sd)

def _sd(values):
    mean = reduce(lambda ag, v: ag + v, values, 0) / len(values)
    vr = 1 / len(values) * reduce(lambda ag, v: ag + (v - mean) ** 2, values, 0)
    return math.sqrt(vr)
