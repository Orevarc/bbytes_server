import json
import os
import random
import re
import decimal
import pandas as pd

from bbytes.settings import MODEL_NAME

from rasa_nlu.converters import load_data
from rasa_nlu.config import RasaNLUConfig
from rasa_nlu.model import Trainer
from rasa_nlu.persistor import get_persistor
from six import string_types


from ingredient_crf import utils


def train(training_data_path, config_path, output_directory, aws=False):
    config = RasaNLUConfig(config_path)
    training_data = load_data(training_data_path)
    trainer = Trainer(config)
    trainer.train(training_data)
    if aws:
        persistor = get_persistor(config)
        model_directory = trainer.persist(
            path=output_directory,
            persistor=persistor,
            model_name=MODEL_NAME
        )
    else:
        model_directory = trainer.persist(
            path=output_directory,
            model_name=MODEL_NAME
        )
    model_fullpath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), model_directory[2:])
    print('Training Complete. Path to trained model: {}'.format(model_fullpath))


def test(test_data_path):
    correct = 0
    wrong = 0
    issues = []
    from ingredient_crf.ingredient_recognizer import EntityExtractor
    recognizer = EntityExtractor()
    df = pd.read_csv(test_data_path)
    for index, row in df.iterrows():
        print("Test")
        test_input = utils.clumpFractions(utils.cleanUnicodeFractions(row["input"].replace(',', '').strip()))
        parsed_ing = recognizer.extract_entities(test_input)
        entities = parsed_ing['entities']
        for entity in entities:
            if entity['value'] in row[entity['entity']]:
                correct += 1
            else:
                # Should have a funciton that grabs the correct tag
                wrong += 1
                issues.append({
                    'input': test_input,
                    'item': entity['value'],
                    'labeled_as': entity['entity']
                })





def generate_training_data(csv_path, count, offset):
    '''
        Format data contained in the csv to a format which can be
        interperetted by rasa nlu
    '''
    df = pd.read_csv(csv_path)
    df.fillna('')
    start = int(offset)
    end = int(offset) + int(count)
    df_slice = df.iloc[start: end]
    training_data = {
        "rasa_nlu_data": {
            "common_examples": []
        }
    }
    for index, row in df_slice.iterrows():
        print("Input: {}".format(row['input']))
        display_input = utils.cleanUnicodeFractions(row["input"]).replace(',', '')
        tokens = utils.tokenize(display_input)
        rowData = [(t, matchUp(t, row)) for t in tokens]
        best_tags = []
        for i, (token, tags) in enumerate(rowData):
            best_tag = getBestTag(tags, token, utils.clumpFractions(display_input))
            if best_tag:
                best_tags.append(best_tag)
        training_data['rasa_nlu_data']['common_examples'].append({
            "text": utils.clumpFractions(display_input).strip(),
            "entities": best_tags
        })
    random.shuffle(training_data['rasa_nlu_data']['common_examples'])
    with open('result.json', 'w') as fp:
        json.dump(training_data, fp)


def matchUp(token, ingredientRow):
    '''
    Returns the best guess of the match between the tags and the
    words from the display text.
    '''
    ret = []
    # split token further by certain characters
    token = utils.normalizeToken(token)
    decimalToken = parseNumbers(token)
    for key, val in ingredientRow.iteritems():
        if isinstance(val, string_types) and not key == 'input':
            for n, vt in enumerate(utils.tokenize(val)):
                if utils.normalizeToken(vt) == token and not key == 'input':
                    ret.append(key.upper())
        elif decimalToken is not None:
            try:
                if val == decimalToken:
                    ret.append(key.upper())
            except:
                pass
    return ret


def parseNumbers(s):
    '''
    Returns a number represented in the passed string
    '''
    ss = utils.unclump(s)
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
    '''
    Returns the tokenized data with corresponding BILOU tags
    '''
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
    '''
    Returns an rasa nlu entity array for identidying entities
    in the input
    '''
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
