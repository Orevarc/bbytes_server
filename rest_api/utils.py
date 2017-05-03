from django_rest_logger import log

import string
import unicodedata
import urllib.request
from bs4 import BeautifulSoup

from rest_api.constants import (
    CONVERSION_MAP,
    DEFAULT_MEASURABLE_UNIT,
    INGREDIENT_AMOUNTS
)


def get_shopping_list_from_urls(urls):
    shopping_list = []
    for url in urls:
        recipe_page = BeautifulSoup(urllib.request.urlopen(url))
        ingredient_list = recipe_page.find_all('li', {'class': 'ingredient'})
        for ingredient in ingredient_list:
            item = {}
            amount = 0
            amount_unit = ''
            name = ''
            full_text = ''.join(ingredient.findAll(text=True))
            amt_ingredient = full_text.rsplit('$')[0]
            found = False
            for amount_string in INGREDIENT_AMOUNTS:
                if amount_string[0] in amt_ingredient.lower():
                    split = amt_ingredient.lower().rsplit(amount_string[0])
                    amount = split[0]
                    name = split[1]
                    amount, amount_unit = AmountConverter.convert_measurable_amount(
                        from_unit=amount_string[0],
                        to_unit=DEFAULT_MEASURABLE_UNIT,
                        amount=amount
                    )
                    found = True
            if not found:
                amount = [int(s) for s in amt_ingredient.split() if s.isdigit()]
                if not amount:
                    amount = ''
                else:
                    amount = amount[0]
                item['amount'] = amount
                item['amount_unit'] = ''
                item['name'] = amt_ingredient.translate(string.punctuation).strip()
            else:
                item['amount'] = amount
                item['amount_unit'] = amount_unit.translate(string.punctuation).strip()
                item['name'] = name.translate(string.punctuation).strip()
            log.warning("{}: {} - {}".format(full_text, item['name'], item['amount_unit']))
            shopping_list.append(item)
    return merge_ingredients(shopping_list)


def merge_ingredients(ingredient_list):
    merged_ingredients = {}
    for ingredient in ingredient_list:
        # Adding whole items (ie. 1 red pepper)
        name = ingredient.get('name')
        if merged_ingredients.get(name, None):
            merged_ingredients[name]['amount'] += ingredient.get('amount')
        else:
            merged_ingredients[name] = {
                'amount': ingredient.get('amount'),
                'unit': ingredient.get('amount_unit')
            }
    return merged_ingredients


class AmountConverter(object):
    '''
        Class to help convert ingredient amounts between different
        weights/amounts. All conversions are going to be 1:1
    '''

    @classmethod
    def convert_measurable_amount(self, from_unit, to_unit, amount):
        # if isinstance(amount, str):
        #     print(amount)
        #     amount = unicodedata.numeric(amount)
        if from_unit == to_unit or from_unit not in CONVERSION_MAP or to_unit not in CONVERSION_MAP:
            return amount, from_unit
        multiplier = CONVERSION_MAP.get(from_unit).get(to_unit)
        converted_amount = 0
        try:
            converted_amount = float(amount) * multiplier
        except ValueError:
            print(amount)
            amount = unicodedata.numeric(amount.rstrip())
            converted_amount = float(amount) * multiplier
        return converted_amount, to_unit
