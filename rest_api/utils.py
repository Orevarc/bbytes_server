from django_rest_logger import log

import numbers
import re
import string
from sys import maxsize
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

translator = str.maketrans('', '', string.punctuation)


def string_punctuation(text):
    return text.translate(translator).strip()


def find_amount(full_ingredient):
    print('><><><><><><><')
    print(full_ingredient)
    amount = [int(s) for s in full_ingredient.split() if s.isdigit()]
    print(amount)
    if not amount:
        rx = r'(\d*)(%s)' % '|'.join(map(chr, FRACTIONS))
        fraction_test = re.findall(rx, full_ingredient)
        try:
            amount = fraction_test[0][1]
        except IndexError:
            amount = None
    else:
        amount = amount[0]
    return amount


def find_amount_unit(amount_unit, full_ingredient):
    try:
        return full_ingredient.index(amount_unit), amount_unit
    except ValueError:
        return maxsize, None


def get_shopping_list_from_urls(urls):
    shopping_list = []
    for url in urls:
        recipe_page = BeautifulSoup(urllib.request.urlopen(url))
        ingredient_list = recipe_page.find_all('li', {'class': 'ingredient'})
        shopping_list.extend(get_ingredients(ingredient_list))
    return merge_ingredients(shopping_list)


def get_ingredients(ingredient_list):
    shopping_list = []
    for ingredient in ingredient_list:
        item = dict(item_template)
        amount = 0
        amount_unit = ''
        name = ''
        full_text = ''.join(ingredient.findAll(text=True))
        full_ingredient = string_punctuation(full_text.rsplit('$')[0].lower())
        ingredient_unit_found = False
        unit_index, amount_unit = min(find_amount_unit(
            unit[0], full_ingredient) for unit in INGREDIENT_UNITS)
        if amount_unit:
            amount = full_ingredient[:unit_index]
            unit_char_count = len(amount_unit)
            name_start_index = unit_index + unit_char_count
            name = full_ingredient[name_start_index:]
            print('111111')
            print(full_ingredient)
            print(amount)
            print(amount_unit)
            amount, amount_unit = AmountConverter.convert_measurable_amount(
                from_unit=amount_unit,
                to_unit=DEFAULT_MEASURABLE_UNIT,
                amount=amount
            )
            print('2222222')
            print(full_ingredient)
            print(amount)
            print(amount_unit)
            ingredient_unit_found = True
        if not ingredient_unit_found:
            amount = find_amount(full_ingredient)
            if not amount:
                # If no amount ingredient and no amount
                item['name'] = full_ingredient
                item['category'] = IngredientCategories.MISC
            else:
                item['unit'] = ''
                item['amount'] = convert_to_number(amount)
                item['name'] = full_ingredient.rsplit(str(amount))[1]
        else:
            item['amount'] = convert_to_number(amount)
            item['unit'] = amount_unit.translate(string.punctuation).strip()
            item['name'] = name.translate(string.punctuation).strip()
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
                print('=====')
                print(base_ingredient_filter)
                base_ingredient_filter = base_ingredient_filter.split(
                    ' ', 1)[1]
            else:
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
            ingredient_mapping = IngredientMapping.objects.get(
                name=ingredient_mapping_filter)
        except IngredientMapping.DoesNotExist:
            ingredient_mapping = None
        if ingredient_mapping:
            ingredient_mapping_found = True
            base_ingredient = BaseIngredient.objects.get(
                pk=ingredient_mapping.ingredient_id)
        else:
            if ' ' in ingredient_mapping_filter:
                ingredient_mapping_filter = ingredient_mapping_filter.split(
                    ' ', 1)[1]
            else:
                return None
    return base_ingredient


def convert_to_number(number):
    try:
        return float(number)
    except ValueError:
        pass
    if not number or isinstance(number, str):
        return 1.0
    # if isinstance(number, numbers.Real):
    #     return float(number)
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
            converted_amount = float(amount) * multiplier
        except ValueError:
            amount = unicodedata.numeric(amount.rstrip())
            converted_amount = float(amount) * multiplier
        return converted_amount, to_unit
