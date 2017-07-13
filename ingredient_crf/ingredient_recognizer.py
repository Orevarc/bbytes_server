from pathlib import Path

from bbytes.base_settings import (
    NER_MODEL,
    RASA_CONFIG_FILE,
    TRAINED_MODEL_PATH
)
from rest_api.constants import (
    AMOUNT_TAG,
    FOOD_TAG,
    UNIT_TAG
)

from rasa_nlu.config import RasaNLUConfig
from rasa_nlu.data_router import DataRouter
from rasa_nlu.model import Metadata, Interpreter


class EntityExtractor(object):

    def __init__(self):
        self.load_model()

    def extract_entities(self, ingredient):
        if not self.interpreter:
            if not self.load_model():
                raise ValueError(
                    'No NER_MODEL specified in base_settings.py. Please train the model and specify the path location in base_settings.py')
        entity_dict = self.interpreter.parse(ingredient)

        return self.find_named_entities(entity_dict['entities'])

    def has_null_entities(self, entities):
        return bool(all([True if entity != '' else False for entity in entities.values()]))


    def find_named_entities(self, entities):
        final_entities = {}
        final_entities['amount'] = self.find_entity(AMOUNT_TAG, entities)
        final_entities['unit'] = self.find_entity(UNIT_TAG, entities)
        final_entities['name'] = self.find_entity(FOOD_TAG, entities)
        return final_entities

    def find_entity(self, entity_name, entities):
        found_entities = [entity['value'] for entity in entities if entity['entity'] == entity_name]
        full_string = ' '.join(found_entities).lower()
        if entity_name == AMOUNT_TAG and full_string == '(':
            full_string = '1'
        return full_string

    def load_model(self):
        if NER_MODEL:
            config = RasaNLUConfig(RASA_CONFIG_FILE)
            metadata = Path(NER_MODEL)
            if metadata:
                self.metadata = Metadata.load(NER_MODEL)
            else:
                # Need to fetch the model from s3
                data_router = DataRouter(config, None)
                data_router.load_model_from_cloud(TRAINED_MODEL_PATH, config)
                self.metadata = Metadata.load(NER_MODEL)
            self.interpreter = Interpreter.load(
                self.metadata, config)
            return True
        return False
