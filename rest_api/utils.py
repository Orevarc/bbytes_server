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


def find_amount(text):
    amount = [int(s) for s in text.split() if s.isdigit()]
    if not amount:
        rx = r'(\d*)(%s)' % '|'.join(map(chr, FRACTIONS))
        fraction_test = re.findall(rx, text)
        try:
            amount = fraction_test[0][1]
        except IndexError:
            amount = None
    else:
        amount = amount[0]
    return amount


def find_amount_before_index(text, index):
    sub_string = text[:index].strip()
    amount_string = ''
    digit_found = False
    for char in reversed(sub_string):
        try:
            unicodedata.digit(char)
            digit_found = True
            amount_string = char + amount_string
        except ValueError:
            try:
                temp = str(unicodedata.numeric(char))
                digit_found = True
                amount_string = temp.strip('0') + amount_string
            except ValueError:
                if not digit_found:
                    pass
                else:
                    break
    amount = 1
    try:
        amount = float(amount_string)
    except ValueError:
        pass
    return amount


def is_number(char):
    try:
        float(char)
        return True
    except ValueError:
        pass
    try:
        unicodedata.numeric(char)
        return True
    except (TypeError, ValueError):
        pass
    return False


def format_ingredient_string(text, unit='', unit_index=None):
    if unit_index:
        unit_char_count = len(unit)
        unit_end_index = unit_index + unit_char_count
        text = text[:unit_index] + text[unit_end_index:]
    else:
        text = text.replace(unit, '')
    text = ''.join([char for char in text if not is_number(char)])
    return string_punctuation(text.strip())


def find_amount_unit(amount_unit, full_ingredient):
    try:
        return full_ingredient.index(amount_unit), amount_unit
    except ValueError:
        return maxsize, None


def get_shopping_list_from_urls(urls):
    shopping_list = []
    recipes = []
    for url in urls:
        recipe_page = BeautifulSoup(urllib.request.urlopen(url))
        ingredient_list = recipe_page.find_all('li', {'class': 'ingredient'})
        shopping_list.extend(get_ingredients(ingredient_list, url))
        recipes.append({
            'title': get_recipe_title(recipe_page),
            'img': get_recipe_image(recipe_page),
            'url': url,
            'multiplier': 1
        })
    merged_shopping_list = merge_ingredients(shopping_list)
    return {
        'shopping_list': merged_shopping_list,
        'recipes': recipes
    }


def get_recipe_image(recipe_page):
    return recipe_page.select('.ERSTopRight img')[0]['src']


def get_recipe_title(recipe_page):
    return recipe_page.select('.post-title h1')[0].text


def get_ingredients(ingredient_list, url):
    shopping_list = []
    for ingredient in ingredient_list:
        item = dict(item_template)
        amount = 0
        amount_unit = ''
        name = ''
        full_text = ''.join(ingredient.findAll(text=True))
        full_ingredient = full_text.rsplit('$')[0].lower()
        ingredient_unit_found = False
        unit_index, amount_unit = min(find_amount_unit(
            unit[0], full_ingredient) for unit in INGREDIENT_UNITS)
        if amount_unit:
            amount = find_amount_before_index(full_ingredient, unit_index)
            # unit_char_count = len(amount_unit)
            # name_start_index = unit_index + unit_char_count
            name = format_ingredient_string(
                text=full_ingredient,
                unit=amount_unit,
                unit_index=unit_index)
            amount, amount_unit = AmountConverter.convert_measurable_amount(
                from_unit=amount_unit,
                to_unit=DEFAULT_MEASURABLE_UNIT,
                amount=amount
            )
            ingredient_unit_found = True
        if not ingredient_unit_found:
            amount = find_amount(full_ingredient)
            if not amount:
                # If no amount ingredient and no amount
                item['name'] = format_ingredient_string(full_ingredient, '')
                item['category'] = IngredientCategories.MISC
                item['full_ingredient'] = full_ingredient
            else:
                item['unit'] = ''
                item['amount'] = convert_to_number(amount)
                item['name'] = format_ingredient_string(full_ingredient, '')
                item['full_ingredient'] = full_ingredient
        else:
            item['amount'] = convert_to_number(amount)
            item['unit'] = amount_unit.translate(string.punctuation).strip()
            item['name'] = name.translate(string.punctuation).strip()
            item['full_ingredient'] = full_ingredient
        item['recipe_url'] = url
        shopping_list.append(item)
    return shopping_list


def find_index(item_list, key, value):
    for i, dic in enumerate(item_list):
        if dic[key] == value:
            return i
    return -1


def merge_ingredients(ingredient_list):
    merged_shopping_list = dict(list_template)
    item_list = []
    for_review = []
    for ingredient in ingredient_list:
        # Adding whole items (ie. 1 red pepper))
        parsed_name = ingredient.get('name')
        base_ingredient = get_base_ingredient(parsed_name)
        if base_ingredient:
            ingredient['name'] = base_ingredient.name
            ingredient['category'] = base_ingredient.category
            if not any(item['name'] == ingredient['name'] for item in item_list):
                item_list.append({
                        'name': ingredient.get('name'),
                        'amount': ingredient.get('amount'),
                        'unit': ingredient.get('unit'),
                        'category': ingredient.get('category'),
                        'recipes': [attach_recipe_url(
                            ingredient.get('recipe_url'),
                            ingredient.get('amount'),
                            ingredient.get('unit'))
                        ]
                })
            else:
                item_index = find_index(item_list, 'name', ingredient.get('name'))
                item_list[item_index]['amount'] += ingredient.get('amount')
                item_list[item_index]['recipes'].append(attach_recipe_url(
                    ingredient.get('recipe_url'),
                    ingredient.get('amount'),
                    ingredient.get('unit'))
                )
        else:
            for_review.append(ingredient)
    merged_shopping_list['item_list'] = item_list
    merged_shopping_list['for_review'] = for_review
    return merged_shopping_list


def attach_recipe_url(url, amount, unit):
    return {
        'url': url,
        'amount': amount,
        'unit': unit
    }


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
