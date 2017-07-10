from pathlib import Path

from bbytes.base_settings import (
    NER_MODEL,
    RASA_CONFIG_FILE,
    TRAINED_MODEL_PATH
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
        return self.interpreter.parse(ingredient)

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
