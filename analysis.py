################################################################################
#
# A wrapper around the different analysis that will be done such as sentiment
# analysis, politeness analysis, and talkativeness analysis. Most of these
# require third parties libraries whose boilerplate code will be handled here.
#
################################################################################

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

def _get_scalar_sentiment(sentence):
    sentiment = int(sentence['sentimentValue'])

    if sentiment > 2:
        return 1
    elif sentiment < 2:
        return -1
    else:
        return 0
