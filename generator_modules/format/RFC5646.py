from langcodes import Language
import random
from langcodes.data_dicts import (
    DEFAULT_SCRIPTS,
    ALL_SCRIPTS,
    TERRITORY_REPLACEMENTS,
    LANGUAGE_ALPHA3
)
language_codes = [lang for lang in LANGUAGE_ALPHA3.keys() if len(lang) == 2]
script_codes = list(ALL_SCRIPTS | set(DEFAULT_SCRIPTS.values()))
region_codes = list(TERRITORY_REPLACEMENTS.values())

class RFC5646:
    @staticmethod
    def generate_random_language_tag():
        lang = random.choice(language_codes)
        components = {'language': lang}

        if random.random() < 0.5:
            components['script'] = random.choice(script_codes)

        if random.random() < 0.7:
            components['territory'] = random.choice(region_codes)

        tag = Language.make(**components)
        return tag.to_tag()

    @staticmethod
    def generate_random_language_tag_value(min_length, max_length):
        while True:
            try:
                tag = RFC5646.generate_random_language_tag()
                lang = Language.get(tag)
                if lang.is_valid() and min_length < len(tag) < max_length:
                    return tag
            except Exception as e:
                print(f"{tag:<15} → ❌ Parse Error: {e}")



