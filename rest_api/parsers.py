import re
import string
from sys import maxsize
import unicodedata
from urllib import request
from urllib.parse import urlparse

from ingredient_crf.ingredient_recognizer import EntityExtractor
from ingredient_crf import utils

from rest_api.constants import (
    CONVERSION_MAP,
    DEFAULT_MEASURABLE_UNIT,
    FRACTIONS,
    IngredientCategories,
    INGREDIENT_UNIT_MAPPINGS,
    INGREDIENT_UNITS,
    PINCH_AMOUNT,
    PINCH_AMOUNT_UNIT
)

from rest_api.utils import (
    AmountConverter,
    BaseIngredientFinder,
    find_index
)

from bs4 import BeautifulSoup

recognizer = EntityExtractor()


class SiteParser(object):

    def __init__(self, urls):
        self.urls = urls
        self.errors = []
        self.recipes = []
        self.ingredient_list = []
        self.shopping_list = []
        self.review_list = []

    def parse_urls(self):
        if not self.validate_urls():
            return

        for url in self.urls:
            domain = self.parse_domain(url)
            parser = IngredientParser(url)
            if domain == 'www.budgetbytes.com':
                parser = BBytesParser(url)
                parser.parse_url()
            elif domain == 'allrecipes.com':
                parser = AllRecipesParser(url)
                parser.parse_url()
            self.ingredient_list.extend(parser.ingredients)
            self.recipes.append(parser.recipe_info)
        self.merge_ingredients()

    def has_errors(self):
        if self.errors:
            return True
        return False

    def validate_urls(self):
        if all([bool(urlparse(url).scheme) for url in self.urls]):
            return True
        else:
            self.errors.append({
                'type': 'error',
                'message': 'Ensure all recipe urls entered are valid'
            })
            return False

    def attach_recipe(self, url, amount, unit):
        return {
            'url': url,
            'amount': amount,
            'unit': unit
        }

    def parse_domain(self, url):
        parsed_uri = urlparse(url)
        domain = '{uri.netloc}'.format(uri=parsed_uri)
        return domain

    def clean_text(self, text):
        translator = str.maketrans('', '', string.punctuation)
        return text.translate(translator).strip()

    def merge_ingredients(self):
        for ingredient in self.ingredient_list:
            name = self.clean_text(ingredient.get('name'))
            print(name)
            amount = ingredient.get('amount')
            category = ingredient.get('category')
            unit = ingredient.get('unit')
            url = ingredient.get('recipe_url')
            base_ingredient = BaseIngredientFinder.find(name)
            if base_ingredient:
                name = base_ingredient.name
                if category != IngredientCategories.MISC:
                    category = base_ingredient.category
                if not any(item['name'] == name for item in self.shopping_list):
                    self.shopping_list.append({
                        'name': name,
                        'category': category,
                        'amount': amount,
                        'unit': unit,
                        'recipes': [self.attach_recipe(url, amount, unit)]
                    })
                else:
                    index = find_index(self.shopping_list, 'name', name)
                    self.shopping_list[index]['amount'] += amount
                    self.shopping_list[index]['recipes'].append(
                        self.attach_recipe(url, amount, unit)
                    )
            else:
                self.review_list.append(ingredient)


class IngredientParser(object):

    def __init__(self, url):
        self.url = url
        self.ingredients = []
        self.recipe_info = {}

    def get_recipe_page(self):
        '''
            Returns the entire html of the recipe page
        '''
        headers = {
            'User-Agent': 'bbytes'
        }
        req = request.Request(
            self.url, headers=headers)
        return BeautifulSoup(request.urlopen(req).read())

    def parse_url(self):
        return []

    def set_recipe_info(self, title='', img='images/meal.svg'):
        self.recipe_info = {
            'title': title,
            'img': img,
            'url': self.url,
            'multiplier': 1
        }

    def get_text_by_class(self, container, class_name):
        '''
            Returns the inner text of the element with class class_name inside
            the passed container
        '''
        element = container.select(class_name)
        if element:
            return element[0].text
        return ''

    def clean_full_ingredient(self, ingredient, unit):
        new_unit = self.clean_unit(unit)
        return ingredient.replace(unit, new_unit)

    def clean_unit(self, unit):
        '''
            Cleans the unit parsed and standardizes it in order to make all
            ingredient units the same for merging
        '''
        if unit.endswith('s'):
            # Strip 's' off of unit
            unit = unit[:-1]
        if unit in INGREDIENT_UNIT_MAPPINGS:
            unit = INGREDIENT_UNIT_MAPPINGS[unit]
        return unit

    def find_unit(self, unit, text):
        '''
            Returns the unit and the index of the unit in the text
            If the unit is not found, None and a maxsize integer is
            returned
        '''
        try:
            return text.index(unit), unit
        except ValueError:
            return maxsize, None

    def find_amount(self, text):
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

    def find_amount_before_index(self, text, unit_index):
        '''
            Returns the first amount in the text before the given index
        '''
        sub_string = text[:unit_index].strip()
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

    def convert_to_number(self, number):
        '''
            Returns a float for the number passed whether the number is
            a string, unicode fraction, or integer/float
        '''
        try:
            return float(number)
        except ValueError:
            pass
        if not number or isinstance(number, str):
            return 1.0
        rx = r'(\d*)(%s)' % '|'.join(map(chr, FRACTIONS))
        for d, f in re.findall(rx, number):
            d = int(d) if d else 0
            number = d + FRACTIONS[ord(f)]
        return float(number)

    def extract_name(self, text, unit='', unit_index=None):
        '''
            Returns the best attempt at a name stripping off the amount and
            unit values
        '''
        if unit_index:
            unit_char_count = len(unit)
            unit_end_index = unit_index + unit_char_count
            text = text[:unit_index] + text[unit_end_index:]
        else:
            text = text.replace(unit, '')
        text = ''.join([char for char in text if not self.is_number(char)])
        return self.strip_punctuation(text.strip())

    def is_number(self, char):
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

    def strip_punctuation(self, text):
        translator = str.maketrans('', '', string.punctuation)
        return text.translate(translator).strip()


class AllRecipesParser(IngredientParser):

    def __init__(self, url):
        super().__init__(url)

    def parse_url(self):
        recipe_page = self.get_recipe_page()
        self.get_ingredients(recipe_page)
        self.set_recipe_info(
            title=self.get_recipe_title(recipe_page),
            img=self.get_recipe_image(recipe_page)
        )

    def get_ingredients(self, recipe_page):
        ingredient_list = recipe_page.find_all(
            'span', {'class': 'recipe-ingred_txt added'})
        self.parse_ingredient_list(ingredient_list)

    # def has_null_entities(self, entities):
    #     return not bool(all([True if entity != '' else False for entity in entities.values()]))

    def parse_ingredient_list(self, ingredient_list):
        for ingredient in ingredient_list:
            print('ING')
            print(ingredient)
            name = unit = amount = category = ''
            full_ingredient = str(ingredient.string)
            print(full_ingredient)
            extracted_entities = recognizer.extract_entities(utils.clumpFractions(utils.cleanUnicodeFractions(full_ingredient.replace(',', '').strip())))
            amount = extracted_entities['amount']
            unit = extracted_entities['unit']
            name = extracted_entities['name']
            full_ingredient = self.clean_full_ingredient(full_ingredient, unit)
            unit = self.clean_unit(unit)
            unit_index, unit = min(self.find_unit(
                ing_unit[0], full_ingredient) for ing_unit in INGREDIENT_UNITS)
            if unit:
                # Known unit has been found, extract amount and convert
                name = self.extract_name(
                    text=full_ingredient, unit=unit, unit_index=unit_index)
                amount = self.find_amount_before_index(
                    text=full_ingredient, unit_index=unit_index)
                amount, unit = AmountConverter.convert_measurable_amount(
                    from_unit=unit, to_unit=DEFAULT_MEASURABLE_UNIT, amount=amount)
            else:
                # No unit was found, attempt to find an amount
                name = self.extract_name(
                        text=full_ingredient, unit='', unit_index=None)
                amount = self.find_amount(full_ingredient)
                if amount:
                    amount = self.convert_to_number(amount)
                else:
                    # No amount was found, add it to misc.
                    # (eg. freshly cracked pepper)
                    category = IngredientCategories.MISC
            self.ingredients.append({
                'name': name,
                'amount': amount,
                'unit': unit,
                'category': category,
                'full_ingredient': full_ingredient,
                'recipe_url': self.url
            })

    def get_recipe_image(self, recipe_page):
        # try:
        #     return recipe_page.select('.ERSTopRight img')[0]['src']
        # except IndexError:
        return recipe_page.select('.rec-photo')[0]['src']
        # return 'http://images.media-allrecipes.com/userphotos/250x140/4559472.jpg'

    def get_recipe_title(self, recipe_page):
        return recipe_page.select('.recipe-summary__h1')[0].text



class BBytesParser(IngredientParser):

    def __init__(self, url):
        super().__init__(url)

    def parse_url(self):
        recipe_page = self.get_recipe_page()
        self.get_ingredients(recipe_page)
        self.set_recipe_info(
            title=self.get_recipe_title(recipe_page),
            img=self.get_recipe_image(recipe_page)
        )

    def get_ingredients(self, recipe_page):
        ingredient_list = recipe_page.find_all(
            'li', {'class': 'ingredient'})
        if not ingredient_list:
            ingredient_list = recipe_page.find_all(
                'li', {'class': 'wprm-recipe-ingredient'})
            self.parse_ingredient_list_new_format(ingredient_list)
        else:
            self.parse_ingredient_list(ingredient_list)

    # def has_null_entities(self, entities):
    #     return not bool(all([True if entity != '' else False for entity in entities.values()]))

    def parse_ingredient_list(self, ingredient_list):
        for ingredient in ingredient_list:
            name = unit = amount = category = ''
            full_ingredient = self.strip_cost(ingredient)
            extracted_entities = recognizer.extract_entities(utils.clumpFractions(utils.cleanUnicodeFractions(full_ingredient.replace(',', '').strip())))
            amount = extracted_entities['amount']
            unit = extracted_entities['unit']
            name = extracted_entities['name']
            unit_index, unit = min(self.find_unit(
                ing_unit[0], full_ingredient) for ing_unit in INGREDIENT_UNITS)
            if unit:
                # Known unit has been found, extract amount and convert
                name = self.extract_name(
                    text=full_ingredient, unit=unit, unit_index=unit_index)
                amount = self.find_amount_before_index(
                    text=full_ingredient, unit_index=unit_index)
                amount, unit = AmountConverter.convert_measurable_amount(
                    from_unit=unit, to_unit=DEFAULT_MEASURABLE_UNIT, amount=amount)
            else:
                # No unit was found, attempt to find an amount
                name = self.extract_name(
                        text=full_ingredient, unit='', unit_index=None)
                amount = self.find_amount(full_ingredient)
                if amount:
                    amount = self.convert_to_number(amount)
                else:
                    # No amount was found, add it to misc.
                    # (eg. freshly cracked pepper)
                    category = IngredientCategories.MISC
            self.ingredients.append({
                'name': name,
                'amount': amount,
                'unit': unit,
                'category': category,
                'full_ingredient': full_ingredient,
                'recipe_url': self.url
            })

    def parse_ingredient_list_new_format(self, ingredient_list):
        for ingredient in ingredient_list:
            name = self.get_text_by_class(
                ingredient, '.wprm-recipe-ingredient-name')
            amount = self.get_text_by_class(
                ingredient, '.wprm-recipe-ingredient-amount')
            unit = self.get_text_by_class(
                ingredient, '.wprm-recipe-ingredient-unit')
            category = ''
            full_ingredient = '{} {} {}'.format(amount, unit, name)
            extracted_entities = recognizer.extract_entities(utils.clumpFractions(utils.cleanUnicodeFractions(full_ingredient.replace(',', '').strip())))
            if not extracted_entities['amount'] == '':
                amount = extracted_entities['amount']
            if not extracted_entities['unit'] == '':
                unit = extracted_entities['unit']
            if not extracted_entities['name'] == '':
                name = extracted_entities['name']
            if unit:
                if unit == 'can':
                    unit_index, unit = min(self.find_unit(
                        ing_unit[0], amount) for ing_unit in INGREDIENT_UNITS)
                    if unit:
                        amount = self.find_amount_before_index(
                            text=amount, unit_index=unit_index)
                        amount, unit = AmountConverter.convert_measurable_amount(
                            from_unit=unit, to_unit=DEFAULT_MEASURABLE_UNIT, amount=amount)
                elif unit == 'large':
                    amount, unit = AmountConverter.convert_measurable_amount(
                        from_unit=unit, to_unit=DEFAULT_MEASURABLE_UNIT, amount=amount)
                    unit = ''
                else:
                    amount, unit = AmountConverter.convert_measurable_amount(
                        from_unit=unit, to_unit=DEFAULT_MEASURABLE_UNIT, amount=amount)
            elif amount and not unit:
                amount = self.convert_to_number(amount)
            else:
                category = IngredientCategories.MISC
            self.ingredients.append({
                'name': name,
                'amount': amount,
                'unit': unit,
                'category': category,
                'full_ingredient': full_ingredient,
                'recipe_url': self.url
            })

    def get_recipe_image(self, recipe_page):
        try:
            return recipe_page.select('.ERSTopRight img')[0]['src']
        except IndexError:
            return recipe_page.select('.wprm-recipe-image img')[0]['src']

    def get_recipe_title(self, recipe_page):
        return recipe_page.select('.post-title h1')[0].text

    def strip_cost(self, ingredient):
        text = ''.join(ingredient.findAll(text=True))
        return text.rsplit('$')[0].lower()
