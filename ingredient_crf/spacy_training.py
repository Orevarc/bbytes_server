import re
import decimal
import optparse
import pandas as pd
import random
from six import string_types
import spacy
from spacy.pipeline import EntityRecognizer
from spacy.gold import GoldParse
from spacy.tagger import Tagger


from ingredient_crf import utils


def train(csv_path, count, offset, output_directory):

    training_data = generate_training_data(csv_path, count, offset)

    model_name = 'en'
    food_label = 'FOOD'
    qty_label = 'QTY'
    comment_label = 'COMMENT'
    range_label = 'RANGE_END'
    unit_label = 'UNIT'

    nlp = spacy.load(model_name)
    nlp.entity.add_label(food_label)
    nlp.entity.add_label(qty_label)
    nlp.entity.add_label(comment_label)
    nlp.entity.add_label(range_label)
    nlp.entity.add_label(unit_label)

    ner = train_ingredient_ner(nlp, training_data, output_directory)


def generate_training_data(csv_path, count, offset):
    '''
        Format data contained in the csv to a format which can be
        interperetted by crf++ crf function
    '''
    df = pd.read_csv(csv_path)
    df.fillna('')
    start = int(offset)
    end = int(offset) + int(count)
    df_slice = df.iloc[start: end]

    training_data = []
    for index, row in df_slice.iterrows():
        print("Input: {}".format(row['input']))
        display_input = cleanUnicodeFractions(row["input"])
        tokens = tokenize(display_input)
        print("Display: {}".format(display_input))
        print("Tokens: {}".format(tokens))
        rowData = [(t, matchUp(t, row)) for t in tokens]
        best_tags = []
        for i, (token, tags) in enumerate(rowData):
            best_tag = getBestTag(tags, token, clumpFractions(display_input))
            if best_tag:
                best_tags.append(best_tag)
        training_data.append((clumpFractions(display_input).strip(), best_tags))
        print training_data


def train_ingredient_ner(nlp, training_data, output_directory):
    # Add new words to vocab
    for raw_text, _ in training_data:
        doc = nlp.make_doc(raw_text)
        for word in doc:
            _ = nlp.vocab[word.orth]
    for itn in range(20):
        random.shuffle(training_data)
        for raw_text, entity_offsets in training_data:
            print(raw_text)
            print(entity_offsets)
            doc = nlp(raw_text)
            nlp.tagger(doc)
            gold = GoldParse(doc, entities=entity_offsets)
            loss = nlp.entity.update(doc, gold)
    nlp.end_training()
    nlp.save_to_directory(output_directory)


def matchUp(token, ingredientRow):
    """
    Returns our best guess of the match between the tags and the
    words from the display text.
    This problem is difficult for the following reasons:
        * not all the words in the display name have associated tags
        * the quantity field is stored as a number, but it appears
          as a string in the display name
        * the comment is often a compilation of different comments in
          the display name
    """
    ret = []
    # strip parens from the token, since they often appear in the
    # display_name, but are removed from the comment.
    token = normalizeToken(token)
    decimalToken = parseNumbers(token)
    for key, val in ingredientRow.iteritems():
        if isinstance(val, string_types) and not key == 'input':
            for n, vt in enumerate(tokenize(val)):
                if normalizeToken(vt) == token and not key == 'input':
                    ret.append(key.upper())
        elif decimalToken is not None:
            try:
                if val == decimalToken:
                    ret.append(key.upper())
            except:
                pass
    return ret


def parseNumbers(s):
    """
    Parses a string that represents a number into a decimal data type so that
    we can match the quantity field in the db with the quantity that appears
    in the display name. Rounds the result to 2 places.
    """
    ss = unclump(s)
    m3 = re.match('^\d+$', ss)
    if m3 is not None:
        return decimal.Decimal(round(float(ss), 2))
    m1 = re.match(r'(\d+)\s+(\d)/(\d)', ss)
    if m1 is not None:
        num = int(m1.group(1)) + (float(m1.group(2)) / float(m1.group(3)))
        return decimal.Decimal(str(round(num, 2)))
    m2 = re.match(r'^(\d)/(\d)$', ss)
    if m2 is not None:
        num = float(m2.group(1)) / float(m2.group(2))
        return decimal.Decimal(str(round(num, 2)))
    return None


def getPrevTags(data, n):
    prevTags = []
    if not n == 0:
        prevTags = data[n-1][1]
    return prevTags


def getNextTags(data, n):
    nextTags = []
    if not n == len(data) - 1:
        nextTags = data[n+1][1]
    return nextTags


def addPrefixes(data):
    newData = []
    for n, (token, tags) in enumerate(data):
        prevTags = getPrevTags(data, n)
        nextTags = getNextTags(data, n)
        newTags = []
        for t in tags:
            if ((t not in prevTags) and (t not in nextTags)):
                p = 'U'
            elif ((t not in prevTags) and (t in nextTags)):
                p = 'B'
            elif ((t in prevTags) and (t in nextTags)):
                p = 'I'
            else:
                p = 'L'
            newTags.append("%s-%s" % (p, t))
        newData.append((token, newTags))
    return newData


def getBestTag(tags, token, input):
    if len(tags) == 1:
        start = input.index(token)
        end = start + len(token)
        entity = tags[0]
        return {
            "start": start,
            "end": end,
            "value": token,
            "entity": entity
        }
    # if there are multiple tags, pick the first which isn't COMMENT
    else:
        for t in tags:
            if 'INPUT' not in t or 'COMMENT' not in t:
                start = input.index(token)
                end = start + len(token)
                entity = t
                return {
                    "start": start,
                    "end": end,
                    "value": token,
                    "entity": entity
                }
    # we have no idea what to guess
    return None
