from django_rest_logger import log

import numbers
import re
import string
import unicodedata
import urllib.request
from bs4 import BeautifulSoup

from rest_api.constants import (
    CONVERSION_MAP,
    DEFAULT_MEASURABLE_UNIT,
    FRACTIONS,
    IngredientCategories,
    INGREDIENT_UNITS,
    PINCH_AMOUNT,
    PINCH_AMOUNT_UNIT
)
from rest_api.models import (
    BaseIngredient,
    IngredientMapping
)

list_template = {
    'item_list': [],
    'for_review': []    
}

item_template = {
    'name': '',
    'amount': 1,
    'unit': '',
    'category':  ''
}


def get_shopping_list_from_urls(urls):
    shopping_list = []
    for url in urls:
        recipe_page = BeautifulSoup(urllib.request.urlopen(url))
        ingredient_list = recipe_page.find_all('li', {'class': 'ingredient'})
        shopping_list = get_ingredients(ingredient_list)
    return merge_ingredients(shopping_list)


def get_ingredients(ingredient_list):
    shopping_list = []
    for ingredient in ingredient_list:
        item = dict(item_template)
        amount = 0
        amount_unit = ''
        name = ''
        full_text = ''.join(ingredient.findAll(text=True))
        amt_ingredient = full_text.rsplit('$')[0]
        ingredient_unit_found = False
        for ingredient_unit in INGREDIENT_UNITS:
            if ingredient_unit[0] in amt_ingredient.lower():
                split = amt_ingredient.lower().rsplit(ingredient_unit[0])
                amount = split[0]
                name = split[1]
                amount, amount_unit = AmountConverter.convert_measurable_amount(
                    from_unit=ingredient_unit[0],
                    to_unit=DEFAULT_MEASURABLE_UNIT,
                    amount=amount
                )
                ingredient_unit_found = True
        if not ingredient_unit_found:
            amount = [int(s) for s in amt_ingredient.split() if s.isdigit()]
            if not amount:
                # If no amount ingredient and no amount
                item['name'] = amt_ingredient
                item['category'] = IngredientCategories.MISC
            else:
                amount = amount[0]
                item['unit'] = ''
                item['amount'] = convert_to_number(amount)
                item['name'] = amt_ingredient.translate(string.punctuation).strip()
        else:
            item['amount'] = convert_to_number(amount)
            item['unit'] = amount_unit.translate(string.punctuation).strip()
            item['name'] = name.translate(string.punctuation).strip()
        log.warning("{}: {} - {}".format(full_text, item['name'], item['unit']))
        shopping_list.append(item)
    return shopping_list


def merge_ingredients(ingredient_list):
    merged_shopping_list = dict(list_template)
    item_list = {}
    for_review = []
    for ingredient in ingredient_list:
        # Adding whole items (ie. 1 red pepper))
        parsed_name = ingredient.get('name')
        base_ingredient = get_base_ingredient(parsed_name)
        if base_ingredient:
            ingredient['name'] = base_ingredient.name
            ingredient['category'] = base_ingredient.category
            if item_list.get(ingredient['name'], None):
                item_list[ingredient['name']]['amount'] += ingredient.get('amount')
            else:
                item_list[ingredient['name']] = {
                    'amount': ingredient.get('amount'),
                    'unit': ingredient.get('unit'),
                    'category': ingredient.get('category')
                }
        else:
            for_review.append(ingredient)
    merged_shopping_list['item_list'] = item_list
    merged_shopping_list['for_review'] = for_review
    return merged_shopping_list


def get_base_ingredient(parsed_name):
    '''
    Returns the BaseIngredient if one is found directly or through the
    IngredientMapping. Returns None if neither are matched.

    Checks to see if the item's name string or a substring of the name string
    is a BaseIngredient. If no BaseIngredient is matched, the parsed_name is
    checked to see if an IngredientMapping is found.
    '''
    base_ingredient = None
    base_ingredient_found = False
    base_ingredient_filter = parsed_name
    while not base_ingredient_found:
        try:
            base_ingredient = BaseIngredient.objects.get(
                name=base_ingredient_filter)
        except BaseIngredient.DoesNotExist:
            base_ingredient = None
        if base_ingredient:
            base_ingredient_found = True
        else:
            if ' ' in base_ingredient_filter:
                base_ingredient_filter = base_ingredient_filter.split(
                    ' ', 1)[1]
            else:
                print("Here")
                base_ingredient_found = True
                base_ingredient = get_ingredient_mapping(parsed_name)
    return base_ingredient


def get_ingredient_mapping(parsed_name):
    '''
    Returns the BaseIngredient object if one is found. Returns None if not.

    If the item is not found in BaseIngredient, try to see if there is already
    a mapping for the the item. Mappings are common alternatives to standard
    base ingredients (ie cayenne is also cayenne powder)
    '''
    base_ingredient = None
    ingredient_mapping_found = False
    ingredient_mapping_filter = parsed_name
    while not ingredient_mapping_found:
        try:
            print("123")
            print(ingredient_mapping_filter)
            ingredient_mapping = IngredientMapping.objects.get(
                name=ingredient_mapping_filter)
        except IngredientMapping.DoesNotExist:
            ingredient_mapping = None
        if ingredient_mapping:
            ingredient_mapping_found = True
            base_ingredient = BaseIngredient.objects.get(
                pk=ingredient_mapping.ingredient_id)
            print(base_ingredient.name)
        else:
            if ' ' in ingredient_mapping_filter:
                ingredient_mapping_filter = ingredient_mapping_filter.split(
                    ' ', 1)[1]
            else:
                return None
    return base_ingredient


def convert_to_number(number):
    if not number or isinstance(number, str):
        return 1.0
    if isinstance(number, numbers.Real):
        return float(number)
    rx = r'(\d*)(%s)' % '|'.join(map(chr, FRACTIONS))
    for d, f in re.findall(rx, number):
        d = int(d) if d else 0
        number = d + FRACTIONS[ord(f)]
    return float(number)


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
            print("============================")
            print(amount)
            converted_amount = float(amount) * multiplier
        except ValueError:
            print(amount)
            amount = unicodedata.numeric(amount.rstrip())
            converted_amount = float(amount) * multiplier
        return converted_amount, to_unit
